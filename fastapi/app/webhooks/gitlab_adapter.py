"""
GitLab webhook adapter.

Handles secret token validation and normalises GitLab
webhook payloads (merge requests, notes, pushes, issues) into IngestionEvents.
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

# Map GitLab object_kind + action → our EventType
_GITLAB_EVENT_MAP: Dict[str, Dict[str, EventType]] = {
    "merge_request": {
        "open": EventType.PR_CREATED,
        "update": EventType.PR_UPDATED,
        "merge": EventType.PR_MERGED,
        "close": EventType.PR_CLOSED,
    },
    "note": {
        "MergeRequest": EventType.REVIEW_COMMENT,
        "Issue": EventType.ISSUE_COMMENTED,
        "_default": EventType.REVIEW_COMMENT,
    },
    "push": {
        "_default": EventType.COMMIT_PUSHED,
    },
    "issue": {
        "open": EventType.ISSUE_CREATED,
        "update": EventType.ISSUE_UPDATED,
        "close": EventType.ISSUE_CLOSED,
    },
}


class GitLabAdapter(BaseWebhookAdapter):
    """Webhook adapter for GitLab."""

    @property
    def platform_name(self) -> str:
        return "gitlab"

    async def validate_signature(self, request: Request, body: bytes) -> bool:
        """Validate GitLab webhook secret token header."""
        secret = settings.GITLAB_WEBHOOK_SECRET
        if not secret:
            logger.warning("GITLAB_WEBHOOK_SECRET not set — skipping validation")
            return True

        token = request.headers.get("X-Gitlab-Token", "")
        return token == secret

    async def parse_event(
        self, headers: Dict[str, str], payload: Dict[str, Any]
    ) -> Optional[IngestionEvent]:
        """Parse GitLab webhook payload into an IngestionEvent."""
        object_kind = payload.get("object_kind", "")

        # Resolve event type
        if object_kind == "note":
            noteable_type = payload.get("object_attributes", {}).get("noteable_type", "_default")
            event_map = _GITLAB_EVENT_MAP.get("note", {})
            event_type = event_map.get(noteable_type) or event_map.get("_default")
        elif object_kind in ("merge_request", "issue"):
            action = payload.get("object_attributes", {}).get("action", "_default")
            event_type = _GITLAB_EVENT_MAP.get(object_kind, {}).get(action)
        elif object_kind == "push":
            event_type = EventType.COMMIT_PUSHED
        else:
            logger.debug(f"Ignoring GitLab event: {object_kind}")
            return None

        if not event_type:
            return None

        # Extract author
        user = payload.get("user", {})
        author = EventAuthor(
            name=user.get("name", user.get("username", "unknown")),
            username=user.get("username"),
            email=user.get("email"),
            avatar_url=user.get("avatar_url"),
        )

        # Extract context
        project = payload.get("project", {})
        context = EventContext(
            repository=project.get("path_with_namespace"),
            organisation=project.get("namespace"),
            url=project.get("web_url"),
        )

        # Extract content
        title, description, content = self._extract_content(object_kind, payload)

        return IngestionEvent(
            platform=Platform.GITLAB,
            event_type=event_type,
            title=title,
            description=description,
            content=content,
            context=context,
            author=author,
            raw_payload=payload,
            tags=["gitlab", object_kind],
        )

    @staticmethod
    def _extract_content(kind: str, payload: Dict) -> tuple:
        attrs = payload.get("object_attributes", {})
        if kind == "merge_request":
            return attrs.get("title"), attrs.get("description"), attrs.get("url")
        elif kind == "note":
            return None, attrs.get("note"), attrs.get("url")
        elif kind == "push":
            commits = payload.get("commits", [])
            messages = "\n".join(c.get("message", "") for c in commits)
            return f"Push to {payload.get('ref', '')}", messages, None
        elif kind == "issue":
            return attrs.get("title"), attrs.get("description"), attrs.get("url")
        return None, None, None
