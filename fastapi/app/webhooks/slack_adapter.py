"""
Slack webhook adapter.

Handles Slack's URL verification challenge, signing secret validation,
and normalises Slack event payloads (messages, threads, reactions)
into IngestionEvents.
"""

import hmac
import hashlib
import time
import logging
from typing import Dict, Any, Optional

from fastapi import Request

from app.config import settings
from app.webhooks.base_adapter import BaseWebhookAdapter
from app.webhooks.models import (
    IngestionEvent, Platform, EventType,
    EventAuthor, EventContext,
)

logger = logging.getLogger(__name__)

# Map Slack event type → our EventType
_SLACK_EVENT_MAP: Dict[str, EventType] = {
    "message": EventType.MESSAGE_SENT,
    "app_mention": EventType.MESSAGE_SENT,
    "reaction_added": EventType.REACTION_ADDED,
}


class SlackAdapter(BaseWebhookAdapter):
    """Webhook adapter for Slack."""

    @property
    def platform_name(self) -> str:
        return "slack"

    async def validate_signature(self, request: Request, body: bytes) -> bool:
        """
        Validate Slack request signing secret.
        See: https://api.slack.com/authentication/verifying-requests-from-slack
        """
        secret = settings.SLACK_SIGNING_SECRET
        if not secret:
            logger.warning("SLACK_SIGNING_SECRET not set — skipping validation")
            return True

        timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
        if not timestamp:
            return False

        # Reject requests older than 5 minutes (replay protection)
        if abs(time.time() - int(timestamp)) > 300:
            logger.warning("Slack request timestamp too old — possible replay attack")
            return False

        sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
        expected = "v0=" + hmac.new(
            secret.encode("utf-8"),
            sig_basestring.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        provided = request.headers.get("X-Slack-Signature", "")
        return hmac.compare_digest(expected, provided)

    async def parse_event(
        self, headers: Dict[str, str], payload: Dict[str, Any]
    ) -> Optional[IngestionEvent]:
        """Parse Slack Events API payload into an IngestionEvent."""
        # The outer payload may be a url_verification challenge (handled in routes)
        event = payload.get("event", {})
        event_type_str = event.get("type", "")

        # Handle threaded replies
        if event_type_str == "message" and event.get("thread_ts"):
            mapped_type = EventType.THREAD_REPLY
        else:
            mapped_type = _SLACK_EVENT_MAP.get(event_type_str)

        if not mapped_type:
            logger.debug(f"Ignoring Slack event: {event_type_str}")
            return None

        # Ignore bot messages to avoid loops
        if event.get("bot_id") or event.get("subtype") == "bot_message":
            return None
            
        channel_id = event.get("channel", "unknown")
        user_id = event.get("user", "unknown")
        
        # Try to resolve real names dynamically
        from app.integrations.models import IntegrationRepository
        import requests
        
        channel_name = channel_id
        author_name = user_id
        
        integration = IntegrationRepository.find_by_resource("slack", channel_id)
        if integration:
            # Resolve channel name from DB
            for res in integration.resources:
                if res.resource_id == channel_id and res.resource_name:
                    channel_name = res.resource_name
                    break
                    
            # Resolve user name from Slack API
            if user_id != "unknown" and integration.access_token:
                try:
                    resp = requests.get(
                        "https://slack.com/api/users.info", 
                        headers={"Authorization": f"Bearer {integration.access_token}"}, 
                        params={"user": user_id}
                    )
                    data = resp.json()
                    if data.get("ok"):
                        user_obj = data.get("user", {})
                        p = user_obj.get("profile", {})
                        author_name = p.get("real_name") or p.get("display_name") or user_obj.get("name") or user_id
                except Exception as e:
                    logger.warning(f"Failed to lookup slack user {user_id}: {e}")

        # Extract author
        author = EventAuthor(
            name=author_name,
            username=user_id,
            platform_id=user_id,
        )

        # Extract context
        team = payload.get("team_id", "")
        context = EventContext(
            channel=channel_id,
            channel_name=channel_name,
            organisation=team,
        )

        # Extract content
        text = event.get("text", "")
        title = f"Slack message in #{channel_name}"

        return IngestionEvent(
            platform=Platform.SLACK,
            event_type=mapped_type,
            title=title,
            content=text,
            context=context,
            author=author,
            raw_payload=payload,
            tags=["slack", event_type_str],
        )
