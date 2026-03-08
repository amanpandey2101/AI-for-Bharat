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

GITHUB_SCOPES = "repo,admin:repo_hook,read:org,user:email"


class GitHubService:
    """Manages GitHub OAuth and webhook auto-registration."""

    @staticmethod
    def get_oauth_url(state: str) -> str:
        """Generate the GitHub OAuth authorization URL."""
        return (
            f"{GITHUB_OAUTH_URL}"
            f"?client_id={settings.GITHUB_CLIENT_ID}"
            f"&scope={GITHUB_SCOPES}"
            f"&state={state}"
            f"&redirect_uri={settings.API_BASE_URL}/auth/github/callback"
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

    @staticmethod
    def create_adr_pr(
        access_token: str,
        repo_full_name: str,
        decision: dict,
    ) -> Optional[str]:
        """Creates a PR with an ADR document for the validated decision."""
        import base64
        import re
        import time

        try:
            # 1. Get default branch
            repo_resp = http_requests.get(
                f"{GITHUB_API_URL}/repos/{repo_full_name}",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if repo_resp.status_code != 200:
                logger.error(f"Failed to fetch repo {repo_full_name}")
                return None
            default_branch = repo_resp.json().get("default_branch", "main")

            # 2. Get latest commit SHA
            ref_resp = http_requests.get(
                f"{GITHUB_API_URL}/repos/{repo_full_name}/git/refs/heads/{default_branch}",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if ref_resp.status_code != 200:
                return None
            sha = ref_resp.json().get("object", {}).get("sha")

            # 3. Create new branch
            branch_name = f"memora/adr-{int(time.time())}"
            create_ref_resp = http_requests.post(
                f"{GITHUB_API_URL}/repos/{repo_full_name}/git/refs",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"ref": f"refs/heads/{branch_name}", "sha": sha}
            )
            if create_ref_resp.status_code != 201:
                return None

            # 4. Generate Markdown content
            safe_title = re.sub(r'[^a-zA-Z0-9]', '-', decision.get("title", "decision").lower())
            file_path = f"docs/architecture/decisions/{int(time.time())}-{safe_title}.md"
            
            content = f"# {decision.get('title')}\n\n"
            content += f"**Status:** Validated\n"
            content += f"**Date:** {time.strftime('%Y-%m-%d')}\n\n"
            content += "## Description\n"
            content += f"{decision.get('description', '')}\n\n"
            
            if decision.get('rationale'):
                content += "## Rationale\n"
                content += f"{decision.get('rationale')}\n\n"
                
            if decision.get('alternatives_considered'):
                content += "## Alternatives Considered\n"
                for alt in decision.get('alternatives_considered'):
                    content += f"- {alt}\n"
                    
            content_encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')

            # 5. Commit file
            commit_resp = http_requests.put(
                f"{GITHUB_API_URL}/repos/{repo_full_name}/contents/{file_path}",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "message": f"docs(adr): auto-generated ADR for '{decision.get('title')}'",
                    "content": content_encoded,
                    "branch": branch_name
                }
            )
            if commit_resp.status_code not in (200, 201):
                logger.error(f"Failed to commit file {commit_resp.text}")
                return None
                
            # 6. Create PR
            pr_resp = http_requests.post(
                f"{GITHUB_API_URL}/repos/{repo_full_name}/pulls",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "title": f"docs(adr): {decision.get('title')}",
                    "body": f"This ADR was automatically inferred from discussions and validated via Memora.\n\nDescription: {decision.get('description')}",
                    "head": branch_name,
                    "base": default_branch
                }
            )
            
            if pr_resp.status_code == 201:
                pr_url = pr_resp.json().get("html_url")
                logger.info(f"Successfully created ADR PR: {pr_url}")
                return pr_url
            else:
                logger.error(f"Failed to create PR {pr_resp.text}")
                return None
                
        except Exception:
            logger.error("Error creating ADR PR via GitHub", exc_info=True)
            return None
