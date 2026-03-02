"""
Jira integration service.

Handles Atlassian OAuth 2.0 (3LO) flow, listing projects,
and auto-registering webhooks via the Jira REST API.
"""

import logging
from typing import Dict, List, Optional
import requests as http_requests

from app.config import settings

logger = logging.getLogger(__name__)

ATLASSIAN_AUTH_URL = "https://auth.atlassian.com/authorize"
ATLASSIAN_TOKEN_URL = "https://auth.atlassian.com/oauth/token"
ATLASSIAN_API_URL = "https://api.atlassian.com"

JIRA_SCOPES = "read:jira-work read:jira-user write:jira-work manage:jira-webhook offline_access"


class JiraService:
    """Manages Jira/Atlassian OAuth and webhook auto-registration."""

    @staticmethod
    def get_oauth_url(state: str) -> str:
        return (
            f"{ATLASSIAN_AUTH_URL}"
            f"?audience=api.atlassian.com"
            f"&client_id={settings.JIRA_CLIENT_ID}"
            f"&scope={JIRA_SCOPES}"
            f"&redirect_uri={settings.API_BASE_URL}/integrations/jira/callback"
            f"&state={state}"
            f"&response_type=code"
            f"&prompt=consent"
        )

    @staticmethod
    def exchange_code(code: str) -> Dict:
        response = http_requests.post(
            ATLASSIAN_TOKEN_URL,
            json={
                "grant_type": "authorization_code",
                "client_id": settings.JIRA_CLIENT_ID,
                "client_secret": settings.JIRA_CLIENT_SECRET,
                "code": code,
                "redirect_uri": f"{settings.API_BASE_URL}/integrations/jira/callback",
            },
        )
        return response.json()

    @staticmethod
    def get_accessible_sites(access_token: str) -> List[Dict]:
        """Get Atlassian sites (Jira instances) the user has access to."""
        response = http_requests.get(
            f"{ATLASSIAN_API_URL}/oauth/token/accessible-resources",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return response.json()

    @staticmethod
    def list_projects(access_token: str, cloud_id: str) -> List[Dict]:
        """List Jira projects for a given Atlassian cloud site."""
        response = http_requests.get(
            f"{ATLASSIAN_API_URL}/ex/jira/{cloud_id}/rest/api/3/project",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        data = response.json()
        return [
            {
                "id": p["id"],
                "key": p["key"],
                "name": p["name"],
                "url": f"https://{cloud_id}.atlassian.net/browse/{p['key']}",
            }
            for p in data
        ] if isinstance(data, list) else []

    @staticmethod
    def register_webhook(
        access_token: str,
        cloud_id: str,
        webhook_url: str,
        project_key: str,
    ) -> Optional[Dict]:
        """Register a webhook for a Jira project."""
        try:
            response = http_requests.post(
                f"{ATLASSIAN_API_URL}/ex/jira/{cloud_id}/rest/api/3/webhook",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "webhooks": [
                        {
                            "jqlFilter": f"project = {project_key}",
                            "events": [
                                "jira:issue_created",
                                "jira:issue_updated",
                                "comment_created",
                                "comment_updated",
                            ],
                        }
                    ],
                    "url": webhook_url,
                },
            )

            if response.status_code in (200, 201):
                result = response.json()
                logger.info(f"Registered Jira webhook for {project_key}")
                return result
            else:
                logger.error(f"Failed to register Jira webhook: {response.status_code} {response.text}")
                return None
        except Exception:
            logger.error("Exception registering Jira webhook", exc_info=True)
            return None

    @staticmethod
    def delete_webhook(access_token: str, cloud_id: str, webhook_id: str) -> bool:
        try:
            response = http_requests.delete(
                f"{ATLASSIAN_API_URL}/ex/jira/{cloud_id}/rest/api/3/webhook",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"webhookIds": [int(webhook_id)]},
            )
            return response.status_code in (200, 202)
        except Exception:
            return False
