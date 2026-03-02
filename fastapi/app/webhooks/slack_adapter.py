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

        # Extract author
        author = EventAuthor(
            name=event.get("user", "unknown"),
            username=event.get("user"),
            platform_id=event.get("user"),
        )

        # Extract context
        team = payload.get("team_id", "")
        context = EventContext(
            channel=event.get("channel"),
            organisation=team,
        )

        # Extract content
        text = event.get("text", "")
        title = f"Slack message in #{event.get('channel', 'unknown')}"

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
