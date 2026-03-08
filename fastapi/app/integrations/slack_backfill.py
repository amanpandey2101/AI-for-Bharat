"""
Slack channel history backfill service.

When a user connects a Slack channel, this service fetches existing
messages and threads, processes them through the Bedrock Agent
decision inference pipeline, and syncs results into the Knowledge Base.

Runs as a background daemon thread — does not block the API response.
"""

import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

import requests as http_requests

from app.config import settings
from app.integrations.models import IntegrationRepository
from app.webhooks.models import (
    IngestionEvent,
    Platform,
    EventType,
    EventStatus,
    EventContext,
    EventAuthor,
)
from app.webhooks.event_store import EventRepository

logger = logging.getLogger(__name__)

SLACK_API_URL = "https://slack.com/api"


# ── Backfill Service ──────────────────────────────────────────────────────────

class SlackBackfillService:
    """Fetches historical Slack data with pagination and rate limiting."""

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
        }

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> http_requests.Response:
        url = f"{SLACK_API_URL}/{endpoint}"
        response = http_requests.get(url, headers=self.headers, params=params)
        
        # Simple rate limit handling
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 5))
            logger.warning(f"[Slack Backfill] Rate limited. Sleeping for {retry_after}s")
            time.sleep(retry_after)
            return self._get(endpoint, params)
            
        return response

    def fetch_channel_history(self, channel_id: str, max_messages: int = 100) -> List[Dict]:
        """Fetch the most recent messages from a channel."""
        messages: List[Dict] = []
        cursor = None
        
        while len(messages) < max_messages:
            params = {
                "channel": channel_id,
                "limit": min(100, max_messages - len(messages)),
            }
            if cursor:
                params["cursor"] = cursor

            resp = self._get("conversations.history", params)
            if resp.status_code != 200:
                logger.error(f"[Slack Backfill] Failed to fetch channel history: {resp.text}")
                break
                
            data = resp.json()
            if not data.get("ok"):
                error_code = data.get("error")
                logger.error(f"[Slack Backfill] Slack API Error: {error_code}")
                if error_code == "not_in_channel":
                    raise Exception("The Memora bot is not in this channel. Please go to Slack, type '/invite @Memora' in this channel, and then reconnect it from the dashboard.")
                else:
                    raise Exception(f"Slack API error: {error_code}")

            batch = data.get("messages", [])
            if not batch:
                break
                
            # Filter out bot messages and system join messages
            for msg in batch:
                if msg.get("subtype") not in ("bot_message", "channel_join", "channel_leave"):
                    messages.append(msg)
                    
            cursor = data.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
                
            time.sleep(settings.BACKFILL_API_DELAY)
            
        return messages[:max_messages]
        
    def fetch_thread_replies(self, channel_id: str, thread_ts: str) -> List[Dict]:
        """Fetch replies for a specific thread."""
        params = {
            "channel": channel_id,
            "ts": thread_ts,
            "limit": 100
        }
        resp = self._get("conversations.replies", params)
        data = resp.json()
        if not data.get("ok"):
            logger.warning(f"[Slack Backfill] Failed to fetch thread: {data.get('error')}")
            return []
            
        # exclude the original message which is always returned first
        replies = data.get("messages", [])
        return replies[1:] if len(replies) > 1 else []


def _process_event_with_agent(event: IngestionEvent):
    """Run Bedrock Agent to extract decisions."""
    try:
        from app.agents.bedrock_agent import process_event_for_decisions

        logger.info(f"[Slack Backfill Agent] Processing event {event.event_id}...")
        event_dict = event.to_agent_dict()
        result = process_event_for_decisions(event_dict)

        if result:
            logger.info(f"[Slack Backfill Agent] ✅ Decision found: '{result.get('title')}'")
            EventRepository.update_status(event.event_id, EventStatus.PROCESSED)
        else:
            EventRepository.update_status(event.event_id, EventStatus.PROCESSED)

    except Exception:
        logger.error(f"[Slack Backfill Agent] Failed to process event {event.event_id}", exc_info=True)
        try:
            EventRepository.update_status(event.event_id, EventStatus.FAILED)
        except Exception:
            pass


def _create_event(platform_org: str, channel_id: str, message: Dict) -> IngestionEvent:
    author = EventAuthor(
        name=message.get("user", "unknown"),
        username=message.get("user"),
        platform_id=message.get("user"),
    )

    context = EventContext(
        channel=channel_id,
        organisation=platform_org,
    )

    text = message.get("text", "")
    ts = message.get("ts", "")
    event_type = EventType.MESSAGE_SENT
    
    # Check if it was part of a thread
    if message.get("thread_ts") and message.get("thread_ts") != ts:
        event_type = EventType.THREAD_REPLY

    ts_float = float(ts) if ts else time.time()
    dt = datetime.utcfromtimestamp(ts_float)

    return IngestionEvent(
        platform=Platform.SLACK,
        event_type=event_type,
        title=f"Slack message in #{channel_id}",
        content=text,
        context=context,
        author=author,
        raw_payload=message,
        timestamp=dt.isoformat() + "Z",
        tags=["slack", "backfill"],
    )


# ── Runner ────────────────────────────────────────────────────────────────────

def run_backfill_for_channel(
    access_token: str,
    channel_id: str,
    user_id: str,
):
    """
    Main entry point for the background backfill process.
    Updates the connected resource status as it progresses.
    """
    logger.info(f"[Slack Backfill] Starting for channel {channel_id} (user: {user_id})")

    integration = IntegrationRepository.get(user_id, "slack")
    if not integration:
        logger.error(f"[Slack Backfill] Slack integration not found for user {user_id}")
        return

    # Find the resource to update status
    resource = next((r for r in integration.resources if r.resource_id == channel_id), None)
    if not resource:
        logger.error(f"[Slack Backfill] Resource {channel_id} not found in integration")
        return

    # Helper to update status
    def update_status(status: str, progress: Dict = None, error: str = None):
        resource.backfill_status = status
        if progress:
            resource.backfill_progress = progress
        if error:
            resource.backfill_error = error
        if status == "in_progress":
            resource.backfill_started_at = datetime.utcnow().isoformat()
        if status in ("completed", "failed"):
            resource.backfill_completed_at = datetime.utcnow().isoformat()
        IntegrationRepository.save(integration)

    update_status("in_progress", {"messages": 0, "threads": 0})

    try:
        service = SlackBackfillService(access_token)
        platform_org = integration.platform_org or "unknown"

        logger.info(f"[Slack Backfill] Fetching history for {channel_id}...")
        
        # 1. Fetch channel history (last N messages)
        max_msgs = getattr(settings, "BACKFILL_MAX_SLACK_MESSAGES", 100)
        messages = service.fetch_channel_history(channel_id, max_messages=max_msgs)
        
        logger.info(f"[Slack Backfill] Found {len(messages)} recent messages")

        events_processed = 0
        threads_processed = 0

        for msg in messages:
            # Create ingestion event for the main message
            event = _create_event(platform_org, channel_id, msg)
            EventRepository.save(event)
            _process_event_with_agent(event)
            events_processed += 1
            
            # If this message has a thread, fetch the replies
            thread_ts = msg.get("thread_ts")
            if thread_ts and thread_ts == msg.get("ts") and msg.get("reply_count", 0) > 0:
                logger.info(f"[Slack Backfill] Fetching thread for {thread_ts}...")
                replies = service.fetch_thread_replies(channel_id, thread_ts)
                
                # We can group thread replies into one big event context, or process them individually.
                # Processing individually:
                for reply in replies:
                    if reply.get("subtype") not in ("bot_message",):
                        reply_event = _create_event(platform_org, channel_id, reply)
                        EventRepository.save(reply_event)
                        _process_event_with_agent(reply_event)
                        events_processed += 1
                
                threads_processed += 1
                time.sleep(settings.BACKFILL_API_DELAY)

            update_status("in_progress", {
                "messages": events_processed,
                "threads": threads_processed
            })

        logger.info(f"[Slack Backfill] Completed for {channel_id} (Processed {events_processed} msgs)")
        update_status("completed", {"messages": events_processed, "threads": threads_processed})

    except Exception as e:
        logger.error(f"[Slack Backfill] Failed for {channel_id}: {e}", exc_info=True)
        update_status("failed", error=str(e))
