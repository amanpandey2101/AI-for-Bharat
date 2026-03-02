"""
DynamoDB client initialization and table management.

Replaces the previous SQLAlchemy engine/session setup with AWS DynamoDB
resources using boto3. Supports both AWS-hosted and local DynamoDB instances.
"""

import boto3
import logging
from botocore.exceptions import ClientError
from app.config import settings

logger = logging.getLogger(__name__)

# ── DynamoDB Resource ──────────────────────────────────────────────────────────

_dynamodb_kwargs = {
    "region_name": settings.AWS_REGION,
}

if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
    _dynamodb_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
    _dynamodb_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY

if settings.DYNAMODB_ENDPOINT_URL:
    _dynamodb_kwargs["endpoint_url"] = settings.DYNAMODB_ENDPOINT_URL

dynamodb = boto3.resource("dynamodb", **_dynamodb_kwargs)
dynamodb_client = boto3.client("dynamodb", **_dynamodb_kwargs)


# ── Table Name Helpers ─────────────────────────────────────────────────────────

def get_table_name(base_name: str) -> str:
    """Return the fully-qualified table name with the configured prefix."""
    return f"{settings.DYNAMODB_TABLE_PREFIX}_{base_name}"


USERS_TABLE_NAME = get_table_name("users")


# ── Table References ───────────────────────────────────────────────────────────

def get_users_table():
    """Return a reference to the Users DynamoDB table."""
    return dynamodb.Table(USERS_TABLE_NAME)


# ── Table Creation (for local dev / first-time setup) ──────────────────────────

def create_users_table():
    """
    Create the Users table in DynamoDB if it does not already exist.

    Schema follows the design document:
    - PK: USER#<email>  (Partition Key)
    - GSI_GithubID: github_id → allows lookup by GitHub ID
    - GSI_VerificationToken: verification_token → allows lookup by token
    """
    try:
        table = dynamodb.create_table(
            TableName=USERS_TABLE_NAME,
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "github_id", "AttributeType": "S"},
                {"AttributeName": "verification_token", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "GSI_GithubID",
                    "KeySchema": [
                        {"AttributeName": "github_id", "KeyType": "HASH"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5,
                    },
                },
                {
                    "IndexName": "GSI_VerificationToken",
                    "KeySchema": [
                        {"AttributeName": "verification_token", "KeyType": "HASH"},
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
        logger.info(f"Created DynamoDB table: {USERS_TABLE_NAME}")
        return table
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            logger.info(f"DynamoDB table already exists: {USERS_TABLE_NAME}")
            return dynamodb.Table(USERS_TABLE_NAME)
        raise


def ensure_tables_exist():
    """Create all required DynamoDB tables if they don't exist."""
    existing = dynamodb_client.list_tables()["TableNames"]

    if USERS_TABLE_NAME not in existing:
        create_users_table()

    # Events table (created via webhooks module)
    from app.webhooks.event_store import EVENTS_TABLE_NAME, create_events_table
    if EVENTS_TABLE_NAME not in existing:
        create_events_table()

    # Integrations table
    from app.integrations.models import INTEGRATIONS_TABLE_NAME, create_integrations_table
    if INTEGRATIONS_TABLE_NAME not in existing:
        create_integrations_table()

    # Decisions table
    from app.decisions import DECISIONS_TABLE_NAME, create_decisions_table
    if DECISIONS_TABLE_NAME not in existing:
        create_decisions_table()

    logger.info("All DynamoDB tables verified.")
