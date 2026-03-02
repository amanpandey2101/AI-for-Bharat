"""
Quick test: invoke the Bedrock Agent directly to verify it works.
Run: python test_agent.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.agents.bedrock_agent import agent_service, process_event_for_decisions

# ── Test 1: Direct agent invocation ────────────────────────────────────────────
print("=" * 60)
print("TEST 1: Direct Agent Invocation")
print("=" * 60)

test_event = {
    "event_id": "test-001",
    "platform": "github",
    "event_type": "pr_created",
    "title": "Migrate database from PostgreSQL to DynamoDB",
    "content": """
    This PR migrates our entire data layer from PostgreSQL (SQLAlchemy) to AWS DynamoDB.

    ## Why?
    - We're targeting a serverless architecture for the AWS hackathon
    - DynamoDB offers pay-per-request pricing, no server management
    - Better integration with other AWS services (Lambda, Step Functions)

    ## What changed?
    - Replaced SQLAlchemy models with boto3 DynamoDB operations
    - Created new table schemas with GSIs for efficient queries
    - Updated all repository classes to use DynamoDB put_item/get_item
    - Added table creation on startup

    ## Alternatives considered:
    - Aurora Serverless (too expensive for our scale)
    - MongoDB Atlas (not native AWS)
    - Sticking with PostgreSQL on RDS (requires server management)

    Reviewers: @john-doe @jane-smith
    """,
    "author_name": "aman-kumar",
    "repository": "memora-dev/memora",
    "timestamp": "2026-03-01T19:00:00Z",
}

print("\nSending test event to agent...")
result = process_event_for_decisions(test_event)

if result:
    print(f"\n✅ Decision detected!")
    print(f"   Title: {result.get('title')}")
    print(f"   Confidence: {result.get('confidence', {}).get('overall', 'N/A')}")
    print(f"   Tags: {result.get('tags', [])}")
    print(f"   Participants: {result.get('participants', [])}")
    print(f"   Decision ID: {result.get('decision_id')}")
else:
    print("\n⚠️  No decision detected (agent may not have found a decision in this event)")

# ── Test 2: Semantic search ────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("TEST 2: Semantic Search (Knowledge Base)")
print("=" * 60)

answer = agent_service.search_decisions("Why did we choose DynamoDB?")
print(f"\nAnswer: {answer[:500]}...")

print("\n" + "=" * 60)
print("DONE")
print("=" * 60)
