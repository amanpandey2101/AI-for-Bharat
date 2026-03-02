"""
Workspace — the top-level organizational unit in Memora.

A workspace groups related resources (repos, channels, projects)
and scopes all decisions and events to a single project context.

Example:
  Workspace "Memora Platform"
    ├── GitHub: memora-dev/backend, memora-dev/frontend
    ├── Slack: #memora-engineering, #memora-design
    └── Jira: MEM project
"""

import uuid
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.database import dynamodb as dynamodb_resource, dynamodb_client
from app.config import settings

logger = logging.getLogger(__name__)

WORKSPACES_TABLE_NAME = f"{settings.DYNAMODB_TABLE_PREFIX}_workspaces"


# ── Models ─────────────────────────────────────────────────────────────────────

class ConnectedResource(BaseModel):
    """A single connected resource (repo, channel, or project)."""
    platform: str                        # github, gitlab, slack, jira
    resource_id: str                     # e.g. "owner/repo", "C0123CHANNEL", "MEM"
    resource_name: str                   # Display name
    resource_type: str = "repository"    # repository, channel, project
    connected_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class WorkspaceMember(BaseModel):
    """A member of a workspace."""
    user_id: str
    role: str = "member"                 # owner, admin, member
    joined_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class Workspace(BaseModel):
    """Top-level organizational unit."""
    workspace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    owner_id: str

    # Connected resources across platforms
    resources: List[ConnectedResource] = []

    # Members
    members: List[WorkspaceMember] = []

    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def pk(self) -> str:
        return f"WORKSPACE#{self.workspace_id}"

    def to_dynamo(self) -> Dict[str, Any]:
        from decimal import Decimal

        def _clean(obj):
            if isinstance(obj, float):
                return Decimal(str(obj))
            if isinstance(obj, dict):
                return {k: _clean(v) for k, v in obj.items() if v is not None and v != ""}
            if isinstance(obj, list):
                return [_clean(i) for i in obj]
            return obj

        data = self.model_dump()
        data["PK"] = self.pk
        data["SK"] = "METADATA"
        return _clean(data)

    @classmethod
    def from_dynamo(cls, item: Dict[str, Any]) -> "Workspace":
        from decimal import Decimal

        def _unconvert(obj):
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
        item["resources"] = [ConnectedResource(**r) for r in item.get("resources", [])]
        item["members"] = [WorkspaceMember(**m) for m in item.get("members", [])]
        return cls(**item)


# ── Table Creation ─────────────────────────────────────────────────────────────

def create_workspaces_table():
    """Create the workspaces DynamoDB table."""
    try:
        dynamodb_client.create_table(
            TableName=WORKSPACES_TABLE_NAME,
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
                {"AttributeName": "owner_id", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "GSI_Owner",
                    "KeySchema": [
                        {"AttributeName": "owner_id", "KeyType": "HASH"},
                        {"AttributeName": "SK", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        logger.info(f"Created DynamoDB table: {WORKSPACES_TABLE_NAME}")
    except dynamodb_client.exceptions.ResourceInUseException:
        logger.debug(f"Table {WORKSPACES_TABLE_NAME} already exists")
    except Exception:
        logger.error("Failed to create workspaces table", exc_info=True)


# ── Repository ─────────────────────────────────────────────────────────────────

class WorkspaceRepository:
    """DynamoDB operations for Workspaces."""

    @staticmethod
    def _table():
        return dynamodb_resource.Table(WORKSPACES_TABLE_NAME)

    @staticmethod
    def save(workspace: Workspace) -> None:
        workspace.updated_at = datetime.utcnow().isoformat()
        WorkspaceRepository._table().put_item(Item=workspace.to_dynamo())

    @staticmethod
    def get(workspace_id: str) -> Optional[Workspace]:
        result = WorkspaceRepository._table().get_item(
            Key={"PK": f"WORKSPACE#{workspace_id}", "SK": "METADATA"}
        )
        item = result.get("Item")
        return Workspace.from_dynamo(item) if item else None

    @staticmethod
    def list_by_owner(owner_id: str, limit: int = 50) -> List[Workspace]:
        from boto3.dynamodb.conditions import Key
        result = WorkspaceRepository._table().query(
            IndexName="GSI_Owner",
            KeyConditionExpression=Key("owner_id").eq(owner_id),
            ScanIndexForward=False,
            Limit=limit,
        )
        return [Workspace.from_dynamo(i) for i in result.get("Items", [])]

    @staticmethod
    def add_resource(workspace_id: str, resource: ConnectedResource) -> Optional[Workspace]:
        ws = WorkspaceRepository.get(workspace_id)
        if not ws:
            return None
        # Avoid duplicates
        existing = {(r.platform, r.resource_id) for r in ws.resources}
        if (resource.platform, resource.resource_id) not in existing:
            ws.resources.append(resource)
            WorkspaceRepository.save(ws)
        return ws

    @staticmethod
    def remove_resource(workspace_id: str, platform: str, resource_id: str) -> Optional[Workspace]:
        ws = WorkspaceRepository.get(workspace_id)
        if not ws:
            return None
        ws.resources = [
            r for r in ws.resources
            if not (r.platform == platform and r.resource_id == resource_id)
        ]
        WorkspaceRepository.save(ws)
        return ws

    @staticmethod
    def delete(workspace_id: str) -> None:
        WorkspaceRepository._table().delete_item(
            Key={"PK": f"WORKSPACE#{workspace_id}", "SK": "METADATA"}
        )

    @staticmethod
    def find_workspace_for_resource(owner_id: str, platform: str, resource_id: str) -> Optional[Workspace]:
        """Find which workspace a resource belongs to."""
        workspaces = WorkspaceRepository.list_by_owner(owner_id)
        for ws in workspaces:
            for r in ws.resources:
                if r.platform == platform and r.resource_id == resource_id:
                    return ws
        return None
