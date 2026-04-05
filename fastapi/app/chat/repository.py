import logging
from datetime import datetime
from typing import List, Optional, Dict
import uuid

from boto3.dynamodb.conditions import Key
from app.database import get_chat_sessions_table

logger = logging.getLogger(__name__)

class ChatRepository:
    table = get_chat_sessions_table()

    @classmethod
    def get_session(cls, session_id: str) -> Optional[Dict]:
        """Fetch a specific chat session."""
        resp = cls.table.get_item(Key={"session_id": session_id})
        return resp.get("Item")

    @classmethod
    def list_sessions_for_workspace(cls, workspace_id: str) -> List[Dict]:
        """List all chat sessions for a given workspace ordered by updated_at."""
        resp = cls.table.query(
            IndexName='GSI_Workspace',
            KeyConditionExpression=Key('workspace_id').eq(workspace_id)
        )
        items = resp.get('Items', [])
        # Sort in memory by updated_at desc (newest first)
        items.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        return items

    @classmethod
    def create_session(cls, workspace_id: str, title: str = "New Chat") -> Dict:
        """Create a new chat session."""
        session_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        item = {
            "session_id": session_id,
            "workspace_id": workspace_id,
            "title": title,
            "messages": [],
            "created_at": now,
            "updated_at": now,
        }
        cls.table.put_item(Item=item)
        return item

    @classmethod
    def save_messages(cls, session_id: str, new_messages: List[Dict]):
        """Append messages to an existing session."""
        try:
            now = datetime.utcnow().isoformat()
            
            # Use append to list
            expression = "SET messages = list_append(if_not_exists(messages, :empty_list), :new_msgs), updated_at = :now"
            
            cls.table.update_item(
                Key={"session_id": session_id},
                UpdateExpression=expression,
                ExpressionAttributeValues={
                    ":new_msgs": new_messages,
                    ":empty_list": [],
                    ":now": now
                }
            )
        except Exception as e:
            logger.error(f"Error saving messages to {session_id}: {e}")
            raise

    @classmethod
    def delete_session(cls, session_id: str):
        """Permanently delete a chat session."""
        try:
            cls.table.delete_item(Key={"session_id": session_id})
            logger.info(f"Deleted session: {session_id}")
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            raise
