import sys
import os
import json
sys.path.insert(0, os.path.dirname(__file__))

from app.agents.bedrock_agent import agent_service, process_event_for_decisions

# Simulate a Slack message event
slack_event = {
    "event_id": "slack-test-001",
    "platform": "slack",
    "event_type": "message_sent",
    "title": "Slack message in #architecture",
    "content": "Guys, after discussing the latency issues, we have decided to switch our backend from Python/Flask to Go for the ingestion service. This will help us handle the high throughput from the webhooks. We also considered Rust, but Go has better library support for our current AWS SDK needs. @tech-lead validated this.",
    "author_name": "aman",
    "repository": "C123456",  # Channel ID
    "timestamp": "2026-03-08T18:00:00Z",
    "url": "https://slack.com/archives/C123456/p1234567890",
}

print("=" * 60)
print("TEST: Slack Decision Sync")
print("=" * 60)

print("\nProcessing Slack message event...")
result = process_event_for_decisions(slack_event)

if result:
    print(f"\n✅ Decision detected!")
    print(f"   Title: {result.get('title')}")
    print(f"   Confidence: {result.get('confidence', {}).get('overall', 'N/A')}")
    print(f"   Platform: {result.get('platform')}")
else:
    print("\n⚠️  No decision detected.")
    print("This might happen because the agent didn't find enough 'substance' in a single message.")

print("\nDONE")
