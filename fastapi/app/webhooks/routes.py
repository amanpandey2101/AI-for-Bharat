"""
Webhook routes — unified entry points for all platform webhooks.

Each platform gets its own POST endpoint. The flow is:
1. Read raw body → validate signature
2. Parse payload → normalise into IngestionEvent
3. Save to DynamoDB → publish to SQS
4. Return 202 Accepted (fast response, async processing)
"""

import logging
from typing import Dict

from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import JSONResponse

from app.webhooks.models import IngestionEvent, EventStatus
from app.webhooks.event_store import EventRepository, EventQueue
from app.webhooks.base_adapter import BaseWebhookAdapter
from app.webhooks.github_adapter import GitHubAdapter
from app.webhooks.gitlab_adapter import GitLabAdapter
from app.webhooks.slack_adapter import SlackAdapter
from app.webhooks.jira_adapter import JiraAdapter

logger = logging.getLogger(__name__)

webhook_router = APIRouter()

# ── Adapter Registry ───────────────────────────────────────────────────────────

_adapters: Dict[str, BaseWebhookAdapter] = {
    "github": GitHubAdapter(),
    "gitlab": GitLabAdapter(),
    "slack": SlackAdapter(),
    "jira": JiraAdapter(),
}


# ── Generic Handler ────────────────────────────────────────────────────────────

async def _handle_webhook(platform: str, request: Request) -> JSONResponse:
    """
    Generic webhook handler used by all platform routes.
    Validates → Parses → Stores → Queues → Runs AI Agent → Returns 202.
    """
    adapter = _adapters.get(platform)
    if not adapter:
        raise HTTPException(status_code=400, detail=f"Unknown platform: {platform}")

    # 1. Read raw body
    body = await request.body()

    # 2. Validate signature
    is_valid = await adapter.validate_signature(request, body)
    if not is_valid:
        logger.warning(f"Invalid {platform} webhook signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    # 3. Parse payload
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    headers = dict(request.headers)
    event = await adapter.parse_event(headers, payload)

    if event is None:
        # Event type not relevant — acknowledge but don't process
        return JSONResponse(
            status_code=200,
            content={"status": "ignored", "message": "Event type not tracked"},
        )

    # 4. Store in DynamoDB
    event.status = EventStatus.QUEUED
    EventRepository.save(event)

    # 5. Publish to SQS (best-effort — falls back gracefully)
    queued = EventQueue.publish(event)
    if not queued:
        event.status = EventStatus.RECEIVED
        EventRepository.update_status(event.event_id, EventStatus.RECEIVED)

    # 6. Fire-and-forget: run AI agent in background thread
    import threading
    event_dict = _event_to_agent_dict(event)
    thread = threading.Thread(
        target=_process_event_with_agent,
        args=(event_dict, event.event_id),
        daemon=True,
    )
    thread.start()

    # 7. Return 202 Accepted (fast response)
    return JSONResponse(
        status_code=202,
        content={
            "status": "accepted",
            "event_id": event.event_id,
            "platform": event.platform.value,
            "event_type": event.event_type.value,
        },
    )


def _event_to_agent_dict(event) -> Dict:
    """Convert IngestionEvent to a flat dict for the AI agent."""
    return {
        "event_id": event.event_id,
        "platform": event.platform.value,
        "event_type": event.event_type.value,
        "title": event.title or "",
        "content": event.content or event.description or "",
        "author_name": event.author.name if event.author else "unknown",
        "repository": event.context.repository or event.context.project or event.context.channel or "",
        "timestamp": event.timestamp,
        "url": event.context.url or "",
    }


def _process_event_with_agent(event_dict: Dict, event_id: str):
    """Background task: run the Bedrock Agent on an event to extract decisions."""
    try:
        from app.agents.bedrock_agent import process_event_for_decisions
        logger.info(f"[Agent] Processing event {event_id} for decisions...")

        result = process_event_for_decisions(event_dict)

        if result:
            logger.info(
                f"[Agent] ✅ Decision found: '{result.get('title')}' "
                f"(confidence: {result.get('confidence', {}).get('overall', 'N/A')})"
            )
            # Update event status to processed
            EventRepository.update_status(event_id, EventStatus.PROCESSED)
        else:
            logger.info(f"[Agent] No decision found in event {event_id}")
            EventRepository.update_status(event_id, EventStatus.PROCESSED)

    except Exception:
        logger.error(f"[Agent] Failed to process event {event_id}", exc_info=True)
        try:
            EventRepository.update_status(event_id, EventStatus.FAILED)
        except Exception:
            pass


# ── Platform Routes ────────────────────────────────────────────────────────────

@webhook_router.post("/github")
async def github_webhook(request: Request):
    """Receive GitHub webhook events (PRs, reviews, pushes, issues)."""
    return await _handle_webhook("github", request)


@webhook_router.post("/gitlab")
async def gitlab_webhook(request: Request):
    """Receive GitLab webhook events (merge requests, notes, pushes, issues)."""
    return await _handle_webhook("gitlab", request)


@webhook_router.post("/slack")
async def slack_webhook(request: Request):
    """
    Receive Slack Events API payloads.
    Handles the URL verification challenge automatically.
    """
    # Slack URL verification challenge (sent once during setup)
    try:
        body = await request.json()
        if body.get("type") == "url_verification":
            return JSONResponse(
                status_code=200,
                content={"challenge": body.get("challenge")},
            )
    except Exception:
        pass

    return await _handle_webhook("slack", request)


@webhook_router.post("/jira")
async def jira_webhook(request: Request):
    """Receive Jira webhook events (issues, comments, sprints)."""
    return await _handle_webhook("jira", request)


# ── Admin / Debug ──────────────────────────────────────────────────────────────

@webhook_router.get("/events")
async def list_events(platform: str = None, limit: int = 20):
    """List recent ingestion events (admin/debug endpoint)."""
    if platform:
        events = EventRepository.list_by_platform(platform, limit=limit)
    else:
        # List from all platforms
        events = []
        for p in ["github", "gitlab", "slack", "jira"]:
            events.extend(EventRepository.list_by_platform(p, limit=limit // 4 or 5))
        events.sort(key=lambda e: e.timestamp, reverse=True)
        events = events[:limit]

    return {
        "count": len(events),
        "events": [
            {
                "event_id": e.event_id,
                "platform": e.platform.value,
                "event_type": e.event_type.value,
                "title": e.title,
                "status": e.status.value,
                "timestamp": e.timestamp,
                "author": e.author.name if e.author else None,
            }
            for e in events
        ],
    }
