"""
Slack integration service.

Handles Slack OAuth v2 flow. Once the app is installed to a workspace,
events flow automatically — no per-channel webhook registration needed.
"""

import logging
from typing import Dict, List, Optional
import requests as http_requests

from app.config import settings

logger = logging.getLogger(__name__)

SLACK_OAUTH_URL = "https://slack.com/oauth/v2/authorize"
SLACK_TOKEN_URL = "https://slack.com/api/oauth.v2.access"
SLACK_API_URL = "https://slack.com/api"

# Bot scopes needed for reading messages and channel info
SLACK_SCOPES = "channels:history,channels:read,groups:history,groups:read,chat:write,reactions:read,users:read"


class SlackService:
    """Manages Slack OAuth and workspace integration."""

    @staticmethod
    def get_oauth_url(state: str) -> str:
        return (
            f"{SLACK_OAUTH_URL}"
            f"?client_id={settings.SLACK_CLIENT_ID}"
            f"&scope={SLACK_SCOPES}"
            f"&redirect_uri={settings.API_BASE_URL}/integrations/slack/callback"
            f"&state={state}"
        )

    @staticmethod
    def exchange_code(code: str) -> Dict:
        response = http_requests.post(
            SLACK_TOKEN_URL,
            data={
                "client_id": settings.SLACK_CLIENT_ID,
                "client_secret": settings.SLACK_CLIENT_SECRET,
                "code": code,
                "redirect_uri": f"{settings.API_BASE_URL}/integrations/slack/callback",
            },
        )
        return response.json()

    @staticmethod
    def list_channels(access_token: str) -> List[Dict]:
        """List public channels the bot has been added to."""
        channels = []
        cursor = None
        while True:
            params = {"limit": 200, "types": "public_channel,private_channel"}
            if cursor:
                params["cursor"] = cursor

            response = http_requests.get(
                f"{SLACK_API_URL}/conversations.list",
                headers={"Authorization": f"Bearer {access_token}"},
                params=params,
            )
            data = response.json()
            if not data.get("ok"):
                logger.error(f"Slack channels list error: {data.get('error')}")
                break

            channels.extend([
                {
                    "id": c["id"],
                    "name": c["name"],
                    "is_private": c.get("is_private", False),
                    "num_members": c.get("num_members", 0),
                }
                for c in data.get("channels", [])
            ])

            cursor = data.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break

        return channels

    @staticmethod
    def get_team_info(access_token: str) -> Optional[Dict]:
        """Get workspace/team info."""
        response = http_requests.get(
            f"{SLACK_API_URL}/team.info",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        data = response.json()
        if data.get("ok"):
            team = data["team"]
            return {
                "id": team["id"],
                "name": team["name"],
                "domain": team.get("domain"),
            }
        return None
