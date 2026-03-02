"""
GitHub webhook adapter.

Handles HMAC-SHA256 signature validation and normalises GitHub
webhook payloads (PRs, reviews, pushes, issues) into IngestionEvents.
"""

import hmac
import hashlib
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

# Map GitHub event + action → our EventType
_GITHUB_EVENT_MAP: Dict[str, Dict[str, EventType]] = {
    "pull_request": {
        "opened": EventType.PR_CREATED,
        "synchronize": EventType.PR_UPDATED,
        "closed": EventType.PR_MERGED,  # refined below if not merged
        "reopened": EventType.PR_UPDATED,
    },
    "pull_request_review": {
        "submitted": EventType.REVIEW_SUBMITTED,
    },
    "pull_request_review_comment": {
        "created": EventType.REVIEW_COMMENT,
    },
    "push": {
        "_default": EventType.COMMIT_PUSHED,
    },
    "issues": {
        "opened": EventType.ISSUE_CREATED,
        "edited": EventType.ISSUE_UPDATED,
        "closed": EventType.ISSUE_CLOSED,
    },
    "issue_comment": {
        "created": EventType.ISSUE_COMMENTED,
    },
}


class GitHubAdapter(BaseWebhookAdapter):
    """Webhook adapter for GitHub."""

    @property
    def platform_name(self) -> str:
        return "github"

    async def validate_signature(self, request: Request, body: bytes) -> bool:
        """Validate GitHub HMAC-SHA256 webhook signature."""
        secret = settings.GITHUB_WEBHOOK_SECRET
        if not secret:
            logger.warning("GITHUB_WEBHOOK_SECRET not set — skipping signature validation")
            return True  # Allow in dev mode

        signature = request.headers.get("X-Hub-Signature-256", "")
        if not signature.startswith("sha256="):
            return False

        expected = hmac.new(
            secret.encode("utf-8"), body, hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(f"sha256={expected}", signature)

    async def parse_event(
        self, headers: Dict[str, str], payload: Dict[str, Any]
    ) -> Optional[IngestionEvent]:
        """Parse GitHub webhook payload into an IngestionEvent."""
        github_event = headers.get("x-github-event", "")
        action = payload.get("action", "_default")

        # Resolve event type
        event_types = _GITHUB_EVENT_MAP.get(github_event, {})
        event_type = event_types.get(action) or event_types.get("_default")
        if not event_type:
            logger.debug(f"Ignoring GitHub event: {github_event}/{action}")
            return None

        # Handle PR closed vs merged
        if github_event == "pull_request" and action == "closed":
            pr = payload.get("pull_request", {})
            event_type = EventType.PR_MERGED if pr.get("merged") else EventType.PR_CLOSED

        # Extract author
        sender = payload.get("sender", {})
        author = EventAuthor(
            name=sender.get("login", "unknown"),
            username=sender.get("login"),
            platform_id=str(sender.get("id", "")),
            avatar_url=sender.get("avatar_url"),
        )

        # Extract context
        repo = payload.get("repository", {})
        context = EventContext(
            repository=repo.get("full_name"),
            organisation=repo.get("owner", {}).get("login"),
            url=repo.get("html_url"),
        )

        # Extract content based on event type
        title, description, content = self._extract_content(github_event, payload)

        return IngestionEvent(
            platform=Platform.GITHUB,
            event_type=event_type,
            title=title,
            description=description,
            content=content,
            context=context,
            author=author,
            raw_payload=payload,
            tags=["github", github_event, action],
        )

    @staticmethod
    def _extract_content(event: str, payload: Dict) -> tuple:
        """Extract title, description, and content from the payload."""
        if event == "pull_request":
            pr = payload.get("pull_request", {})
            return pr.get("title"), pr.get("body"), pr.get("diff_url")
        elif event in ("pull_request_review", "pull_request_review_comment"):
            review = payload.get("review") or payload.get("comment", {})
            pr = payload.get("pull_request", {})
            return pr.get("title"), review.get("body"), review.get("html_url")
        elif event == "push":
            commits = payload.get("commits", [])
            messages = "\n".join(c.get("message", "") for c in commits)
            return f"Push to {payload.get('ref', '')}", messages, None
        elif event in ("issues", "issue_comment"):
            issue = payload.get("issue", {})
            comment = payload.get("comment", {})
            return issue.get("title"), issue.get("body"), comment.get("body")
        return None, None, None
