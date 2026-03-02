"""
GitLab integration service.

Handles OAuth2 flow, listing projects, and auto-registering webhooks.
"""

import logging
from typing import List, Dict, Optional
import requests as http_requests

from app.config import settings
from app.integrations.models import IntegrationModel, ConnectedResource

logger = logging.getLogger(__name__)

GITLAB_BASE = "https://gitlab.com"
GITLAB_OAUTH_URL = f"{GITLAB_BASE}/oauth/authorize"
GITLAB_TOKEN_URL = f"{GITLAB_BASE}/oauth/token"
GITLAB_API_URL = f"{GITLAB_BASE}/api/v4"

GITLAB_SCOPES = "api read_user read_repository"


class GitLabService:
    """Manages GitLab OAuth and webhook auto-registration."""

    @staticmethod
    def get_oauth_url(state: str) -> str:
        return (
            f"{GITLAB_OAUTH_URL}"
            f"?client_id={settings.GITLAB_CLIENT_ID}"
            f"&redirect_uri={settings.API_BASE_URL}/integrations/gitlab/callback"
            f"&response_type=code"
            f"&scope={GITLAB_SCOPES}"
            f"&state={state}"
        )

    @staticmethod
    def exchange_code(code: str) -> Dict:
        response = http_requests.post(
            GITLAB_TOKEN_URL,
            data={
                "client_id": settings.GITLAB_CLIENT_ID,
                "client_secret": settings.GITLAB_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": f"{settings.API_BASE_URL}/integrations/gitlab/callback",
            },
        )
        return response.json()

    @staticmethod
    def get_user_info(access_token: str) -> Dict:
        response = http_requests.get(
            f"{GITLAB_API_URL}/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return response.json()

    @staticmethod
    def list_projects(access_token: str) -> List[Dict]:
        projects = []
        page = 1
        while True:
            response = http_requests.get(
                f"{GITLAB_API_URL}/projects",
                headers={"Authorization": f"Bearer {access_token}"},
                params={
                    "membership": True,
                    "per_page": 100,
                    "page": page,
                    "order_by": "last_activity_at",
                },
            )
            data = response.json()
            if not data:
                break
            projects.extend([
                {
                    "id": str(p["id"]),
                    "full_name": p["path_with_namespace"],
                    "name": p["name"],
                    "url": p["web_url"],
                }
                for p in data
            ])
            page += 1
            if len(data) < 100:
                break
        return projects

    @staticmethod
    def register_webhook(
        access_token: str,
        project_id: str,
        webhook_url: str,
        webhook_secret: str,
    ) -> Optional[Dict]:
        try:
            response = http_requests.post(
                f"{GITLAB_API_URL}/projects/{project_id}/hooks",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "url": webhook_url,
                    "token": webhook_secret,
                    "push_events": True,
                    "merge_requests_events": True,
                    "issues_events": True,
                    "note_events": True,
                    "enable_ssl_verification": True,
                },
            )
            if response.status_code == 201:
                hook = response.json()
                logger.info(f"Registered GitLab webhook on project {project_id}: {hook['id']}")
                return hook
            else:
                logger.error(f"Failed to register GitLab webhook: {response.status_code} {response.text}")
                return None
        except Exception:
            logger.error("Exception registering GitLab webhook", exc_info=True)
            return None

    @staticmethod
    def delete_webhook(access_token: str, project_id: str, hook_id: str) -> bool:
        try:
            response = http_requests.delete(
                f"{GITLAB_API_URL}/projects/{project_id}/hooks/{hook_id}",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            return response.status_code == 200
        except Exception:
            return False
