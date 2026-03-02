"""
User model (Pydantic) and DynamoDB repository.

Replaces the SQLAlchemy ORM model with:
- UserModel: Pydantic schema for validation & serialisation
- UserRepository: DynamoDB CRUD operations for the Users table

DynamoDB Key Design:
  PK  =  USER#<email>
  GSI_GithubID  →  github_id
  GSI_VerificationToken  →  verification_token
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, EmailStr, Field
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from app.database import get_users_table

import logging

logger = logging.getLogger(__name__)


# ── Pydantic Model ─────────────────────────────────────────────────────────────

class UserModel(BaseModel):
    """Pydantic model representing a User entity in DynamoDB."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str

    password_hash: Optional[str] = None
    github_id: Optional[str] = None
    provider: str = "email"
    avatar_url: Optional[str] = None

    is_deleted: bool = False
    is_inactive: bool = False
    is_verified: bool = False

    verification_token: Optional[str] = None
    verification_token_expires: Optional[str] = None  # ISO-8601 string

    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    # ── Helpers ────────────────────────────────────────────────────────────
    @property
    def pk(self) -> str:
        return f"USER#{self.email}"

    def to_dynamo_item(self) -> Dict[str, Any]:
        """Serialise the model to a DynamoDB item dict."""
        item: Dict[str, Any] = {
            "PK": self.pk,
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "provider": self.provider,
            "is_deleted": self.is_deleted,
            "is_inactive": self.is_inactive,
            "is_verified": self.is_verified,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        # Only write optional fields when they have a value
        if self.password_hash:
            item["password_hash"] = self.password_hash
        if self.github_id:
            item["github_id"] = self.github_id
        if self.avatar_url:
            item["avatar_url"] = self.avatar_url
        if self.verification_token:
            item["verification_token"] = self.verification_token
        if self.verification_token_expires:
            item["verification_token_expires"] = self.verification_token_expires
        return item

    @classmethod
    def from_dynamo_item(cls, item: Dict[str, Any]) -> "UserModel":
        """Construct a UserModel from a raw DynamoDB item."""
        return cls(
            id=item.get("id", ""),
            email=item.get("email", ""),
            name=item.get("name", ""),
            password_hash=item.get("password_hash"),
            github_id=item.get("github_id"),
            provider=item.get("provider", "email"),
            avatar_url=item.get("avatar_url"),
            is_deleted=item.get("is_deleted", False),
            is_inactive=item.get("is_inactive", False),
            is_verified=item.get("is_verified", False),
            verification_token=item.get("verification_token"),
            verification_token_expires=item.get("verification_token_expires"),
            created_at=item.get("created_at", datetime.utcnow().isoformat()),
            updated_at=item.get("updated_at", datetime.utcnow().isoformat()),
        )


# ── DynamoDB Repository ────────────────────────────────────────────────────────

class UserRepository:
    """Handles all DynamoDB operations for the Users table."""

    @staticmethod
    def _table():
        return get_users_table()

    # ── CREATE ─────────────────────────────────────────────────────────────

    @staticmethod
    def create(user: UserModel) -> UserModel:
        """Insert a new user item into DynamoDB."""
        table = UserRepository._table()
        table.put_item(Item=user.to_dynamo_item())
        logger.info(f"Created user: {user.email}")
        return user

    # ── READ ───────────────────────────────────────────────────────────────

    @staticmethod
    def get_by_email(email: str) -> Optional[UserModel]:
        """Look up a user by email (direct key lookup — fastest)."""
        table = UserRepository._table()
        response = table.get_item(Key={"PK": f"USER#{email}"})
        item = response.get("Item")
        if item:
            return UserModel.from_dynamo_item(item)
        return None

    @staticmethod
    def get_by_id(user_id: str) -> Optional[UserModel]:
        """
        Scan for a user by their UUID id.
        NOTE: In production, consider a GSI on `id` for O(1) lookups.
        For the current auth flow this is only called on /auth/me with
        the ID from the JWT, so low-frequency usage is acceptable.
        """
        table = UserRepository._table()
        response = table.scan(
            FilterExpression="id = :uid",
            ExpressionAttributeValues={":uid": user_id},
            Limit=1,
        )
        items = response.get("Items", [])
        if items:
            return UserModel.from_dynamo_item(items[0])
        return None

    @staticmethod
    def get_by_github_id(github_id: str) -> Optional[UserModel]:
        """Look up a user by GitHub ID using GSI_GithubID."""
        table = UserRepository._table()
        response = table.query(
            IndexName="GSI_GithubID",
            KeyConditionExpression=Key("github_id").eq(github_id),
            Limit=1,
        )
        items = response.get("Items", [])
        if items:
            return UserModel.from_dynamo_item(items[0])
        return None

    @staticmethod
    def get_by_verification_token(token: str) -> Optional[UserModel]:
        """Look up a user by verification token using GSI_VerificationToken."""
        table = UserRepository._table()
        response = table.query(
            IndexName="GSI_VerificationToken",
            KeyConditionExpression=Key("verification_token").eq(token),
            Limit=1,
        )
        items = response.get("Items", [])
        if items:
            return UserModel.from_dynamo_item(items[0])
        return None

    # ── UPDATE ─────────────────────────────────────────────────────────────

    @staticmethod
    def update(user: UserModel) -> UserModel:
        """
        Full replacement update — writes the complete item back.
        DynamoDB put_item with the same PK overwrites the existing item.
        """
        user.updated_at = datetime.utcnow().isoformat()
        table = UserRepository._table()
        table.put_item(Item=user.to_dynamo_item())
        logger.info(f"Updated user: {user.email}")
        return user

    # ── DELETE ─────────────────────────────────────────────────────────────

    @staticmethod
    def delete(email: str) -> None:
        """Delete a user item by email."""
        table = UserRepository._table()
        table.delete_item(Key={"PK": f"USER#{email}"})
        logger.info(f"Deleted user: {email}")
