"""
Base webhook adapter — defines the interface all platform adapters must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from fastapi import Request

from app.webhooks.models import IngestionEvent


class BaseWebhookAdapter(ABC):
    """
    Abstract base class for platform webhook adapters.

    Each platform (GitHub, GitLab, Slack, Jira) implements:
    1. validate_signature — verify the webhook is authentic
    2. parse_event — normalise the raw payload into an IngestionEvent
    """

    @abstractmethod
    async def validate_signature(self, request: Request, body: bytes) -> bool:
        """
        Validate the webhook signature / secret token.
        Returns True if the request is authentic.
        """
        ...

    @abstractmethod
    async def parse_event(self, headers: Dict[str, str], payload: Dict[str, Any]) -> Optional[IngestionEvent]:
        """
        Parse the platform-specific payload into a normalised IngestionEvent.
        Returns None if the event type should be ignored.
        """
        ...

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Return the platform identifier string (e.g. 'github')."""
        ...
