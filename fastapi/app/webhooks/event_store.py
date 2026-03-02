"""
Event storage and SQS queue integration.

- EventRepository: DynamoDB CRUD for ingested events
- EventQueue: SQS publishing for async processing
"""

import json
import logging
from typing import Optional, List, Dict, Any

import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

from app.config import settings
from app.database import dynamodb, dynamodb_client, get_table_name
from app.webhooks.models import IngestionEvent, EventStatus

logger = logging.getLogger(__name__)


# ── Table Name ─────────────────────────────────────────────────────────────────

EVENTS_TABLE_NAME = get_table_name("events")


# ── DynamoDB Table Creation ────────────────────────────────────────────────────

def create_events_table():
    """Create the Events table in DynamoDB if it doesn't exist."""
    try:
        table = dynamodb.create_table(
            TableName=EVENTS_TABLE_NAME,
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "platform", "AttributeType": "S"},
                {"AttributeName": "timestamp", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "GSI_Platform",
                    "KeySchema": [
                        {"AttributeName": "platform", "KeyType": "HASH"},
                        {"AttributeName": "timestamp", "KeyType": "RANGE"},
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
        logger.info(f"Created DynamoDB table: {EVENTS_TABLE_NAME}")
        return table
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            logger.info(f"DynamoDB table already exists: {EVENTS_TABLE_NAME}")
            return dynamodb.Table(EVENTS_TABLE_NAME)
        raise


def get_events_table():
    """Return a reference to the Events DynamoDB table."""
    return dynamodb.Table(EVENTS_TABLE_NAME)


# ── Event Repository ───────────────────────────────────────────────────────────

class EventRepository:
    """DynamoDB CRUD for ingestion events."""

    @staticmethod
    def save(event: IngestionEvent) -> IngestionEvent:
        """Store an event in DynamoDB."""
        table = get_events_table()
        table.put_item(Item=event.to_dynamo_item())
        logger.info(f"Saved event: {event.event_id} ({event.platform.value}/{event.event_type.value})")
        return event

    @staticmethod
    def get(event_id: str) -> Optional[IngestionEvent]:
        """Retrieve an event by ID."""
        table = get_events_table()
        response = table.get_item(Key={"PK": f"EVENT#{event_id}"})
        item = response.get("Item")
        return IngestionEvent.from_dynamo_item(item) if item else None

    @staticmethod
    def update_status(event_id: str, status: EventStatus) -> None:
        """Update the processing status of an event."""
        table = get_events_table()
        table.update_item(
            Key={"PK": f"EVENT#{event_id}"},
            UpdateExpression="SET #s = :status",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":status": status.value},
        )
        logger.info(f"Updated event {event_id} status to {status.value}")

    @staticmethod
    def list_by_platform(platform: str, limit: int = 50) -> List[IngestionEvent]:
        """List recent events for a given platform."""
        table = get_events_table()
        response = table.query(
            IndexName="GSI_Platform",
            KeyConditionExpression=Key("platform").eq(platform),
            ScanIndexForward=False,  # newest first
            Limit=limit,
        )
        return [IngestionEvent.from_dynamo_item(item) for item in response.get("Items", [])]


# ── SQS Event Queue ───────────────────────────────────────────────────────────

SQS_QUEUE_NAME = f"{settings.DYNAMODB_TABLE_PREFIX}-ingestion-queue"

_sqs_kwargs: Dict[str, Any] = {"region_name": settings.AWS_REGION}
if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
    _sqs_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
    _sqs_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY

sqs_client = boto3.client("sqs", **_sqs_kwargs)


class EventQueue:
    """Publishes normalised IngestionEvents to an SQS queue for async processing."""

    _queue_url: Optional[str] = None

    @classmethod
    def _get_queue_url(cls) -> Optional[str]:
        """Lazily resolve the SQS queue URL (creates if missing)."""
        if cls._queue_url:
            return cls._queue_url
        try:
            response = sqs_client.get_queue_url(QueueName=SQS_QUEUE_NAME)
            cls._queue_url = response["QueueUrl"]
        except ClientError as e:
            if e.response["Error"]["Code"] == "AWS.SimpleQueueService.NonExistentQueue":
                logger.info(f"SQS queue '{SQS_QUEUE_NAME}' not found — creating…")
                try:
                    response = sqs_client.create_queue(
                        QueueName=SQS_QUEUE_NAME,
                        Attributes={
                            "VisibilityTimeout": "60",
                            "MessageRetentionPeriod": "1209600",  # 14 days
                        },
                    )
                    cls._queue_url = response["QueueUrl"]
                    logger.info(f"Created SQS queue: {cls._queue_url}")
                except ClientError:
                    logger.warning("Failed to create SQS queue — events will be stored in DynamoDB only.", exc_info=True)
                    return None
            else:
                logger.warning("Failed to get SQS queue URL — events will be stored in DynamoDB only.", exc_info=True)
                return None
        return cls._queue_url

    @classmethod
    def publish(cls, event: IngestionEvent) -> bool:
        """
        Publish an event to SQS. Returns True on success.
        Falls back gracefully — if SQS is unavailable, the event is still
        persisted in DynamoDB and can be reprocessed later.
        """
        queue_url = cls._get_queue_url()
        if not queue_url:
            logger.warning(f"SQS unavailable — event {event.event_id} saved to DynamoDB only.")
            return False

        try:
            sqs_client.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps({
                    "event_id": event.event_id,
                    "platform": event.platform.value,
                    "event_type": event.event_type.value,
                    "timestamp": event.timestamp,
                }),
                MessageAttributes={
                    "Platform": {"DataType": "String", "StringValue": event.platform.value},
                    "EventType": {"DataType": "String", "StringValue": event.event_type.value},
                },
            )
            logger.info(f"Published event {event.event_id} to SQS")
            return True
        except ClientError:
            logger.warning(f"Failed to publish event {event.event_id} to SQS", exc_info=True)
            return False
