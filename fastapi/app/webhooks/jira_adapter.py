"""
Jira webhook adapter.

Handles Jira webhook secret validation and normalises Jira
webhook payloads (issues, comments, sprints) into IngestionEvents.
"""

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

# Map Jira webhookEvent → our EventType
_JIRA_EVENT_MAP: Dict[str, EventType] = {
    "jira:issue_created": EventType.ISSUE_CREATED,
    "jira:issue_updated": EventType.ISSUE_UPDATED,
    "jira:issue_deleted": EventType.ISSUE_CLOSED,
    "comment_created": EventType.ISSUE_COMMENTED,
    "comment_updated": EventType.ISSUE_COMMENTED,
    "sprint_started": EventType.SPRINT_STARTED,
    "sprint_closed": EventType.SPRINT_COMPLETED,
}


class JiraAdapter(BaseWebhookAdapter):
    """Webhook adapter for Jira."""

    @property
    def platform_name(self) -> str:
        return "jira"

    async def validate_signature(self, request: Request, body: bytes) -> bool:
        """
        Validate Jira webhook secret.
        Jira Cloud uses a shared secret in the query param or header.
        """
        secret = settings.JIRA_WEBHOOK_SECRET
        if not secret:
            logger.warning("JIRA_WEBHOOK_SECRET not set — skipping validation")
            return True

        # Jira can send the secret as a query param or custom header
        provided = (
            request.query_params.get("secret")
            or request.headers.get("X-Jira-Webhook-Secret", "")
        )
        return provided == secret

    async def parse_event(
        self, headers: Dict[str, str], payload: Dict[str, Any]
    ) -> Optional[IngestionEvent]:
        """Parse Jira webhook payload into an IngestionEvent."""
        webhook_event = payload.get("webhookEvent", "")

        event_type = _JIRA_EVENT_MAP.get(webhook_event)
        if not event_type:
            logger.debug(f"Ignoring Jira event: {webhook_event}")
            return None

        # Extract author
        user = payload.get("user", {})
        author = EventAuthor(
            name=user.get("displayName", "unknown"),
            email=user.get("emailAddress"),
            username=user.get("name"),
            platform_id=user.get("accountId"),
            avatar_url=(user.get("avatarUrls") or {}).get("48x48"),
        )

        # Extract context
        issue = payload.get("issue", {})
        fields = issue.get("fields", {})
        project = fields.get("project", {})

        context = EventContext(
            project=project.get("key"),
            organisation=project.get("name"),
            url=f"{settings.JIRA_BASE_URL}/browse/{issue.get('key', '')}" if settings.JIRA_BASE_URL else None,
        )

        # Extract content
        title = fields.get("summary")
        description = fields.get("description")

        # For comment events, get the comment body
        content = None
        comment = payload.get("comment", {})
        if comment:
            content = comment.get("body")

        return IngestionEvent(
            platform=Platform.JIRA,
            event_type=event_type,
            title=title,
            description=description,
            content=content,
            context=context,
            author=author,
            raw_payload=payload,
            tags=["jira", webhook_event, project.get("key", "")],
        )
