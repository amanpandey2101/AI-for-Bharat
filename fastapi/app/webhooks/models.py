"""
Unified event models for the multi-platform ingestion layer.

All platform-specific webhook payloads are normalised into the
common IngestionEvent schema before being queued for processing.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────────────────

class Platform(str, Enum):
    GITHUB = "github"
    GITLAB = "gitlab"
    SLACK = "slack"
    JIRA = "jira"


class EventType(str, Enum):
    # Code-related
    PR_CREATED = "pr_created"
    PR_UPDATED = "pr_updated"
    PR_MERGED = "pr_merged"
    PR_CLOSED = "pr_closed"
    REVIEW_SUBMITTED = "review_submitted"
    REVIEW_COMMENT = "review_comment"
    COMMIT_PUSHED = "commit_pushed"
    BRANCH_CREATED = "branch_created"
    BRANCH_DELETED = "branch_deleted"

    # Issue / Ticket
    ISSUE_CREATED = "issue_created"
    ISSUE_UPDATED = "issue_updated"
    ISSUE_CLOSED = "issue_closed"
    ISSUE_COMMENTED = "issue_commented"

    # Discussion / Chat
    MESSAGE_SENT = "message_sent"
    THREAD_REPLY = "thread_reply"
    REACTION_ADDED = "reaction_added"

    # Sprint / Project
    SPRINT_STARTED = "sprint_started"
    SPRINT_COMPLETED = "sprint_completed"

    # Catch-all
    UNKNOWN = "unknown"


class EventStatus(str, Enum):
    RECEIVED = "received"
    QUEUED = "queued"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


# ── Core Models ────────────────────────────────────────────────────────────────

class EventAuthor(BaseModel):
    """Normalised author information across platforms."""
    name: str
    email: Optional[str] = None
    username: Optional[str] = None
    platform_id: Optional[str] = None
    avatar_url: Optional[str] = None


class EventContext(BaseModel):
    """Source context — what repo/project/channel the event came from."""
    repository: Optional[str] = None       # GitHub / GitLab repo
    project: Optional[str] = None          # Jira project key
    channel: Optional[str] = None          # Slack channel
    organisation: Optional[str] = None     # Org / workspace name
    url: Optional[str] = None              # Link to the source


class IngestionEvent(BaseModel):
    """
    The unified event schema.

    Every webhook payload from any platform gets normalised into this
    model before being queued (SQS) and stored (DynamoDB).
    """

    # Identity
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    platform: Platform
    event_type: EventType

    # Content
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None          # Body text, diff, message, etc.

    # Context
    context: EventContext = Field(default_factory=EventContext)
    author: Optional[EventAuthor] = None

    # Metadata
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    status: EventStatus = EventStatus.RECEIVED
    raw_payload: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)

    # DynamoDB key
    @property
    def pk(self) -> str:
        return f"EVENT#{self.event_id}"

    def to_dynamo_item(self) -> Dict[str, Any]:
        """Serialise for DynamoDB storage."""
        item: Dict[str, Any] = {
            "PK": self.pk,
            "event_id": self.event_id,
            "platform": self.platform.value,
            "event_type": self.event_type.value,
            "status": self.status.value,
            "timestamp": self.timestamp,
            "raw_payload": self.raw_payload,
            "tags": self.tags,
        }
        if self.title:
            item["title"] = self.title
        if self.description:
            item["description"] = self.description
        if self.content:
            item["content"] = self.content
        if self.context:
            item["context"] = self.context.model_dump(exclude_none=True)
        if self.author:
            item["author"] = self.author.model_dump(exclude_none=True)
        return item

    @classmethod
    def from_dynamo_item(cls, item: Dict[str, Any]) -> "IngestionEvent":
        """Reconstruct from a DynamoDB item."""
        return cls(
            event_id=item.get("event_id", ""),
            platform=Platform(item.get("platform", "github")),
            event_type=EventType(item.get("event_type", "unknown")),
            title=item.get("title"),
            description=item.get("description"),
            content=item.get("content"),
            context=EventContext(**item.get("context", {})),
            author=EventAuthor(**item["author"]) if item.get("author") else None,
            timestamp=item.get("timestamp", datetime.utcnow().isoformat()),
            status=EventStatus(item.get("status", "received")),
            raw_payload=item.get("raw_payload", {}),
            tags=item.get("tags", []),
        )


# ── SQS Message Format ────────────────────────────────────────────────────────

class SQSMessage(BaseModel):
    """Wrapper for SQS message body — contains the serialised IngestionEvent."""
    event_id: str
    platform: str
    event_type: str
    timestamp: str
