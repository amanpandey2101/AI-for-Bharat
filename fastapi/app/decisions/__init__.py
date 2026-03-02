"""
Decision Entity — the core data model for AI-inferred decisions.

Represents a development decision extracted from PR discussions,
code reviews, commits, Jira issues, and Slack threads.
"""

import uuid
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field

from app.database import dynamodb as dynamodb_resource, dynamodb_client
from app.config import settings

logger = logging.getLogger(__name__)

DECISIONS_TABLE_NAME = f"{settings.DYNAMODB_TABLE_PREFIX}_decisions"


# ── Enums ──────────────────────────────────────────────────────────────────────

class DecisionStatus(str, Enum):
    INFERRED = "inferred"
    VALIDATED = "validated"
    DISPUTED = "disputed"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class EvidenceType(str, Enum):
    PR_DESCRIPTION = "pr_description"
    PR_COMMENT = "pr_comment"
    CODE_REVIEW = "code_review"
    COMMIT = "commit"
    CODE_DIFF = "code_diff"
    SLACK_MESSAGE = "slack_message"
    JIRA_ISSUE = "jira_issue"
    JIRA_COMMENT = "jira_comment"


# ── Sub-models ─────────────────────────────────────────────────────────────────

class Evidence(BaseModel):
    source_type: EvidenceType
    source_id: str
    content: str
    author: str
    timestamp: str
    confidence_contribution: float = 0.0
    url: Optional[str] = None


class ConfidenceScore(BaseModel):
    overall: float = Field(ge=0.0, le=1.0)
    evidence_quality: float = Field(ge=0.0, le=1.0, default=0.0)
    evidence_quantity: float = Field(ge=0.0, le=1.0, default=0.0)
    participant_authority: float = Field(ge=0.0, le=1.0, default=0.0)
    temporal_consistency: float = Field(ge=0.0, le=1.0, default=0.0)
    outcome_validation: float = Field(ge=0.0, le=1.0, default=0.0)


# ── Decision Entity ───────────────────────────────────────────────────────────

class DecisionEntity(BaseModel):
    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    repository: str = ""
    platform: str = "github"

    # Decision content
    title: str
    description: str
    rationale: str = ""
    alternatives_considered: List[str] = []

    # Evidence chain
    intent: List[Evidence] = []       # PR descriptions, comments
    execution: List[Evidence] = []    # Code diffs, commits
    authority: List[Evidence] = []    # Approvals, reviewers
    outcomes: List[Evidence] = []     # Follow-up changes

    # Metadata
    confidence: ConfidenceScore = ConfidenceScore(overall=0.5)
    status: DecisionStatus = DecisionStatus.INFERRED
    participants: List[str] = []
    tags: List[str] = []
    source_event_ids: List[str] = []  # Links to ingestion events

    # Relationships
    related_decisions: List[str] = []
    superseded_by: Optional[str] = None
    supersedes: Optional[str] = None

    # Timestamps
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    # Agent attribution
    inferred_by: str = "decision_inference_agent"
    version: int = 1

    @property
    def pk(self) -> str:
        return f"DECISION#{self.decision_id}"

    def to_dynamo(self) -> Dict[str, Any]:
        from decimal import Decimal

        def _clean(obj):
            """Recursively clean data for DynamoDB compatibility."""
            if isinstance(obj, float):
                return Decimal(str(obj))
            if isinstance(obj, dict):
                return {k: _clean(v) for k, v in obj.items() if v is not None and v != "" and v != []}
            if isinstance(obj, list):
                return [_clean(i) for i in obj]
            return obj

        data = self.model_dump()
        data["PK"] = self.pk
        data["SK"] = "METADATA"
        return _clean(data)

    @classmethod
    def from_dynamo(cls, item: Dict[str, Any]) -> "DecisionEntity":
        from decimal import Decimal

        def _unconvert(obj):
            """Convert Decimal back to float for Pydantic."""
            if isinstance(obj, Decimal):
                return float(obj)
            if isinstance(obj, dict):
                return {k: _unconvert(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_unconvert(i) for i in obj]
            return obj

        item = _unconvert(item)
        item.pop("PK", None)
        item.pop("SK", None)
        # Deserialize nested
        item["intent"] = [Evidence(**e) for e in item.get("intent", [])]
        item["execution"] = [Evidence(**e) for e in item.get("execution", [])]
        item["authority"] = [Evidence(**e) for e in item.get("authority", [])]
        item["outcomes"] = [Evidence(**e) for e in item.get("outcomes", [])]
        if isinstance(item.get("confidence"), dict):
            item["confidence"] = ConfidenceScore(**item["confidence"])
        return cls(**item)


# ── DynamoDB Table Creation ────────────────────────────────────────────────────

def create_decisions_table():
    """Create the decisions DynamoDB table with GSIs."""
    try:
        dynamodb_client.create_table(
            TableName=DECISIONS_TABLE_NAME,
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
                {"AttributeName": "repository", "AttributeType": "S"},
                {"AttributeName": "status", "AttributeType": "S"},
                {"AttributeName": "created_at", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "GSI_Repository",
                    "KeySchema": [
                        {"AttributeName": "repository", "KeyType": "HASH"},
                        {"AttributeName": "created_at", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
                {
                    "IndexName": "GSI_Status",
                    "KeySchema": [
                        {"AttributeName": "status", "KeyType": "HASH"},
                        {"AttributeName": "created_at", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        logger.info(f"Created DynamoDB table: {DECISIONS_TABLE_NAME}")
    except dynamodb_client.exceptions.ResourceInUseException:
        logger.info(f"Table {DECISIONS_TABLE_NAME} already exists")
    except Exception:
        logger.error("Failed to create decisions table", exc_info=True)


# ── Repository ─────────────────────────────────────────────────────────────────

class DecisionRepository:
    """DynamoDB operations for Decision Entities."""

    @staticmethod
    def _table():
        return dynamodb_resource.Table(DECISIONS_TABLE_NAME)

    @staticmethod
    def save(decision: DecisionEntity) -> None:
        decision.updated_at = datetime.utcnow().isoformat()
        DecisionRepository._table().put_item(Item=decision.to_dynamo())

    @staticmethod
    def get(decision_id: str) -> Optional[DecisionEntity]:
        result = DecisionRepository._table().get_item(
            Key={"PK": f"DECISION#{decision_id}", "SK": "METADATA"}
        )
        item = result.get("Item")
        return DecisionEntity.from_dynamo(item) if item else None

    @staticmethod
    def list_by_repository(repository: str, limit: int = 50) -> List[DecisionEntity]:
        from boto3.dynamodb.conditions import Key
        result = DecisionRepository._table().query(
            IndexName="GSI_Repository",
            KeyConditionExpression=Key("repository").eq(repository),
            ScanIndexForward=False,
            Limit=limit,
        )
        return [DecisionEntity.from_dynamo(i) for i in result.get("Items", [])]

    @staticmethod
    def list_by_status(status: str, limit: int = 50) -> List[DecisionEntity]:
        from boto3.dynamodb.conditions import Key
        result = DecisionRepository._table().query(
            IndexName="GSI_Status",
            KeyConditionExpression=Key("status").eq(status),
            ScanIndexForward=False,
            Limit=limit,
        )
        return [DecisionEntity.from_dynamo(i) for i in result.get("Items", [])]

    @staticmethod
    def list_recent(limit: int = 50) -> List[DecisionEntity]:
        result = DecisionRepository._table().scan(Limit=limit)
        items = result.get("Items", [])
        # Filter to only METADATA records
        metadata_items = [i for i in items if i.get("SK") == "METADATA"]
        decisions = [DecisionEntity.from_dynamo(i) for i in metadata_items]
        decisions.sort(key=lambda d: d.created_at, reverse=True)
        return decisions[:limit]

    @staticmethod
    def update_status(decision_id: str, status: DecisionStatus) -> None:
        DecisionRepository._table().update_item(
            Key={"PK": f"DECISION#{decision_id}", "SK": "METADATA"},
            UpdateExpression="SET #s = :s, updated_at = :u",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={
                ":s": status.value,
                ":u": datetime.utcnow().isoformat(),
            },
        )

    @staticmethod
    def delete(decision_id: str) -> None:
        DecisionRepository._table().delete_item(
            Key={"PK": f"DECISION#{decision_id}", "SK": "METADATA"}
        )
