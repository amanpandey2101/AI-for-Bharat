"""
Architecture Decision Records (ADRs).

Stores architectural decisions made in a workspace.
"""

import uuid
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.database import dynamodb as dynamodb_resource, dynamodb_client
from app.config import settings

logger = logging.getLogger(__name__)

ADRS_TABLE_NAME = f"{settings.DYNAMODB_TABLE_PREFIX}_adrs"

class ADR(BaseModel):
    adr_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    title: str
    context: str = ""
    decision: str = ""
    consequences: str = ""
    status: str = "proposed"  # proposed, accepted, deprecated, superseded
    
    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    created_by: str  # User ID

    @property
    def pk(self) -> str:
        return f"WORKSPACE#{self.workspace_id}"

    @property
    def sk(self) -> str:
        return f"ADR#{self.adr_id}"

    def to_dynamo(self) -> Dict[str, Any]:
        data = self.model_dump()
        data["PK"] = self.pk
        data["SK"] = self.sk
        return data

    @classmethod
    def from_dynamo(cls, item: Dict[str, Any]) -> "ADR":
        item.pop("PK", None)
        item.pop("SK", None)
        return cls(**item)


def create_adrs_table():
    """Create the ADRs DynamoDB table."""
    try:
        dynamodb_client.create_table(
            TableName=ADRS_TABLE_NAME,
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        logger.info(f"Created DynamoDB table: {ADRS_TABLE_NAME}")
    except dynamodb_client.exceptions.ResourceInUseException:
        logger.debug(f"Table {ADRS_TABLE_NAME} already exists")
    except Exception:
        logger.error("Failed to create ADRs table", exc_info=True)


class ADRRepository:
    """DynamoDB operations for Architecture Decision Records."""

    @staticmethod
    def _table():
        return dynamodb_resource.Table(ADRS_TABLE_NAME)

    @staticmethod
    def save(adr: ADR) -> None:
        adr.updated_at = datetime.utcnow().isoformat()
        ADRRepository._table().put_item(Item=adr.to_dynamo())

    @staticmethod
    def get(workspace_id: str, adr_id: str) -> Optional[ADR]:
        result = ADRRepository._table().get_item(
            Key={"PK": f"WORKSPACE#{workspace_id}", "SK": f"ADR#{adr_id}"}
        )
        item = result.get("Item")
        return ADR.from_dynamo(item) if item else None

    @staticmethod
    def list_by_workspace(workspace_id: str, limit: int = 50) -> List[ADR]:
        from boto3.dynamodb.conditions import Key
        result = ADRRepository._table().query(
            KeyConditionExpression=Key("PK").eq(f"WORKSPACE#{workspace_id}") & Key("SK").begins_with("ADR#"),
            ScanIndexForward=False,  # Newest first
            Limit=limit,
        )
        return [ADR.from_dynamo(i) for i in result.get("Items", [])]

    @staticmethod
    def delete(workspace_id: str, adr_id: str) -> None:
        ADRRepository._table().delete_item(
            Key={"PK": f"WORKSPACE#{workspace_id}", "SK": f"ADR#{adr_id}"}
        )
