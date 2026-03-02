"""
Integration model and DynamoDB repository.

Each integration represents a user's connection to a platform
(GitHub, GitLab, Slack, Jira). Stores OAuth tokens, connected
resources (repos/channels/projects), and auto-generated webhook secrets.

DynamoDB Key Design:
  PK = INTEGRATION#<user_id>#<platform>
  GSI_WebhookLookup: webhook_id → allows inbound webhook routing
"""

import uuid
import secrets
from datetime import datetime
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from app.database import dynamodb, dynamodb_client, get_table_name

import logging

logger = logging.getLogger(__name__)



INTEGRATIONS_TABLE_NAME = get_table_name("integrations")


def get_integrations_table():
    return dynamodb.Table(INTEGRATIONS_TABLE_NAME)


def create_integrations_table():
    """Create the Integrations table in DynamoDB."""
    try:
        table = dynamodb.create_table(
            TableName=INTEGRATIONS_TABLE_NAME,
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "webhook_id", "AttributeType": "S"},
                {"AttributeName": "user_id", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "GSI_WebhookLookup",
                    "KeySchema": [
                        {"AttributeName": "webhook_id", "KeyType": "HASH"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5,
                    },
                },
                {
                    "IndexName": "GSI_UserIntegrations",
                    "KeySchema": [
                        {"AttributeName": "user_id", "KeyType": "HASH"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5,
                    },
                },
            ],
            ProvisionedThroughput={
                "ReadCapacityUnits": 5,
                "WriteCapacityUnits": 5,
            },
        )
        table.wait_until_exists()
        logger.info(f"Created DynamoDB table: {INTEGRATIONS_TABLE_NAME}")
        return table
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            logger.info(f"Table already exists: {INTEGRATIONS_TABLE_NAME}")
            return dynamodb.Table(INTEGRATIONS_TABLE_NAME)
        raise


# ── Pydantic Model ─────────────────────────────────────────────────────────────

class ConnectedResource(BaseModel):
    """A repo, channel, or project the user has connected for monitoring."""
    resource_id: str           # e.g. repo full_name, channel ID, project key
    resource_name: str         
    resource_type: str = ""    # "repository", "channel", "project"
    webhook_registered: bool = False
    platform_webhook_id: Optional[str] = None  # ID returned by the platform API


class IntegrationModel(BaseModel):
    """Represents a user's connection to a platform."""

    user_id: str
    platform: str  # github, gitlab, slack, jira

    access_token: str = ""
    refresh_token: Optional[str] = None
    token_expires_at: Optional[str] = None
    scopes: List[str] = Field(default_factory=list)

    webhook_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    webhook_secret: str = Field(default_factory=lambda: secrets.token_hex(32))

    resources: List[ConnectedResource] = Field(default_factory=list)

    platform_user_id: Optional[str] = None
    platform_username: Optional[str] = None
    platform_org: Optional[str] = None

    status: str = "active" 
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def pk(self) -> str:
        return f"INTEGRATION#{self.user_id}#{self.platform}"

    def to_dynamo_item(self) -> Dict[str, Any]:
        item: Dict[str, Any] = {
            "PK": self.pk,
            "user_id": self.user_id,
            "platform": self.platform,
            "access_token": self.access_token,
            "webhook_id": self.webhook_id,
            "webhook_secret": self.webhook_secret,
            "scopes": self.scopes,
            "resources": [r.model_dump() for r in self.resources],
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if self.refresh_token:
            item["refresh_token"] = self.refresh_token
        if self.token_expires_at:
            item["token_expires_at"] = self.token_expires_at
        if self.platform_user_id:
            item["platform_user_id"] = self.platform_user_id
        if self.platform_username:
            item["platform_username"] = self.platform_username
        if self.platform_org:
            item["platform_org"] = self.platform_org
        return item

    @classmethod
    def from_dynamo_item(cls, item: Dict[str, Any]) -> "IntegrationModel":
        resources = [ConnectedResource(**r) for r in item.get("resources", [])]
        return cls(
            user_id=item.get("user_id", ""),
            platform=item.get("platform", ""),
            access_token=item.get("access_token", ""),
            refresh_token=item.get("refresh_token"),
            token_expires_at=item.get("token_expires_at"),
            scopes=item.get("scopes", []),
            webhook_id=item.get("webhook_id", ""),
            webhook_secret=item.get("webhook_secret", ""),
            resources=resources,
            platform_user_id=item.get("platform_user_id"),
            platform_username=item.get("platform_username"),
            platform_org=item.get("platform_org"),
            status=item.get("status", "active"),
            created_at=item.get("created_at", ""),
            updated_at=item.get("updated_at", ""),
        )



class IntegrationRepository:
    """DynamoDB CRUD for integrations."""

    @staticmethod
    def save(integration: IntegrationModel) -> IntegrationModel:
        integration.updated_at = datetime.utcnow().isoformat()
        table = get_integrations_table()
        table.put_item(Item=integration.to_dynamo_item())
        logger.info(f"Saved integration: {integration.user_id}/{integration.platform}")
        return integration

    @staticmethod
    def get(user_id: str, platform: str) -> Optional[IntegrationModel]:
        table = get_integrations_table()
        response = table.get_item(
            Key={"PK": f"INTEGRATION#{user_id}#{platform}"}
        )
        item = response.get("Item")
        return IntegrationModel.from_dynamo_item(item) if item else None

    @staticmethod
    def get_by_webhook_id(webhook_id: str) -> Optional[IntegrationModel]:
        """Look up integration by webhook_id (for inbound webhook routing)."""
        table = get_integrations_table()
        response = table.query(
            IndexName="GSI_WebhookLookup",
            KeyConditionExpression=Key("webhook_id").eq(webhook_id),
            Limit=1,
        )
        items = response.get("Items", [])
        return IntegrationModel.from_dynamo_item(items[0]) if items else None

    @staticmethod
    def list_by_user(user_id: str) -> List[IntegrationModel]:
        """List all integrations for a user."""
        table = get_integrations_table()
        response = table.query(
            IndexName="GSI_UserIntegrations",
            KeyConditionExpression=Key("user_id").eq(user_id),
        )
        return [IntegrationModel.from_dynamo_item(i) for i in response.get("Items", [])]

    @staticmethod
    def delete(user_id: str, platform: str) -> None:
        table = get_integrations_table()
        table.delete_item(Key={"PK": f"INTEGRATION#{user_id}#{platform}"})
        logger.info(f"Deleted integration: {user_id}/{platform}")

    @staticmethod
    def find_by_resource(platform: str, resource_id: str) -> Optional[IntegrationModel]:
        """
        Find which user's integration owns a given resource (repo/channel/project).
        Used when an inbound webhook arrives to route it to the right user.
        """
        table = get_integrations_table()
        response = table.scan(
            FilterExpression="platform = :p AND contains(#res, :rid)",
            ExpressionAttributeNames={"#res": "resources"},
            ExpressionAttributeValues={
                ":p": platform,
                ":rid": resource_id,
            },
        )
        items = response.get("Items", [])
        if items:
            return IntegrationModel.from_dynamo_item(items[0])
        return None
