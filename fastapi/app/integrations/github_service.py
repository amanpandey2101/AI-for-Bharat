"""
GitHub integration service.

Handles:
1. OAuth App flow (extended scopes for repo + webhook management)
2. Auto-registering webhooks on selected repositories
3. Listing user's accessible repos
"""

import logging
from typing import List, Dict, Optional
import requests as http_requests

from app.config import settings
from app.integrations.models import IntegrationModel, ConnectedResource

logger = logging.getLogger(__name__)

GITHUB_OAUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_URL = "https://api.github.com"

# Scopes needed: repo access + webhook management
GITHUB_SCOPES = "repo,admin:repo_hook,read:org,user:email"


class GitHubService:
    """Manages GitHub OAuth and webhook auto-registration."""

    @staticmethod
    def get_oauth_url(state: str) -> str:
        """Generate the GitHub OAuth authorization URL.
        Note: No redirect_uri — uses the one registered in the GitHub App settings.
        """
        return (
            f"{GITHUB_OAUTH_URL}"
            f"?client_id={settings.GITHUB_CLIENT_ID}"
            f"&scope={GITHUB_SCOPES}"
            f"&state={state}"
        )

    @staticmethod
    def exchange_code(code: str) -> Dict:
        """Exchange the OAuth code for an access token."""
        response = http_requests.post(
            GITHUB_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
            },
        )
        return response.json()

    @staticmethod
    def get_user_info(access_token: str) -> Dict:
        """Get authenticated GitHub user info."""
        response = http_requests.get(
            f"{GITHUB_API_URL}/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return response.json()

    @staticmethod
    def list_repos(access_token: str) -> List[Dict]:
        """List repositories the user has access to."""
        repos = []
        page = 1
        while True:
            response = http_requests.get(
                f"{GITHUB_API_URL}/user/repos",
                headers={"Authorization": f"Bearer {access_token}"},
                params={
                    "per_page": 100,
                    "page": page,
                    "sort": "updated",
                    "affiliation": "owner,collaborator,organization_member",
                },
            )
            data = response.json()
            if not data:
                break
            repos.extend([
                {
                    "id": str(r["id"]),
                    "full_name": r["full_name"],
                    "name": r["name"],
                    "private": r["private"],
                    "owner": r["owner"]["login"],
                    "url": r["html_url"],
                }
                for r in data
            ])
            page += 1
            if len(data) < 100:
                break
        return repos

    @staticmethod
    def register_webhook(
        access_token: str,
        repo_full_name: str,
        webhook_url: str,
        webhook_secret: str,
    ) -> Optional[Dict]:
        """
        Register a webhook on a GitHub repository.
        Returns the webhook response or None on failure.
        """
        try:
            response = http_requests.post(
                f"{GITHUB_API_URL}/repos/{repo_full_name}/hooks",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                },
                json={
                    "name": "web",
                    "active": True,
                    "events": [
                        "pull_request",
                        "pull_request_review",
                        "pull_request_review_comment",
                        "push",
                        "issues",
                        "issue_comment",
                    ],
                    "config": {
                        "url": webhook_url,
                        "content_type": "json",
                        "secret": webhook_secret,
                        "insecure_ssl": "0",
                    },
                },
            )

            if response.status_code == 201:
                hook = response.json()
                logger.info(f"Registered webhook on {repo_full_name}: {hook['id']}")
                return hook
            else:
                logger.error(f"Failed to register webhook on {repo_full_name}: {response.status_code} {response.text}")
                return None
        except Exception:
            logger.error(f"Exception registering webhook on {repo_full_name}", exc_info=True)
            return None

    @staticmethod
    def delete_webhook(
        access_token: str, repo_full_name: str, hook_id: str
    ) -> bool:
        """Remove a webhook from a GitHub repository."""
        try:
            response = http_requests.delete(
                f"{GITHUB_API_URL}/repos/{repo_full_name}/hooks/{hook_id}",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            return response.status_code == 204
        except Exception:
            logger.error(f"Failed to delete webhook {hook_id}", exc_info=True)
            return False
