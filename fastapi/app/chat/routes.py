"""
Chat API using Amazon Bedrock Knowledge Base.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.utils.dependencies import get_current_user_id
from app.workspaces import WorkspaceRepository
from app.agents.bedrock_agent import get_agent_runtime_client
from app.config import settings

logger = logging.getLogger(__name__)

chat_router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

@chat_router.post("/{workspace_id}")
def chat_with_workspace(
    workspace_id: str,
    body: ChatRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    Chat with the workspace knowledge base using Bedrock's RetrieveAndGenerate API.
    """
    ws = WorkspaceRepository.get(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if not settings.BEDROCK_KB_ID:
        raise HTTPException(
            status_code=501, 
            detail="Knowledge Base ID (BEDROCK_KB_ID) is not configured"
        )

    try:
        from app.agents.bedrock_agent import agent_service
        
        # 1. Retrieve context from Knowledge Base directly
        kb_results = agent_service.retrieve_from_kb(body.message, max_results=5)
        
        # 2. Build our own RAG prompt so we control the fallback logic and error messages
        if kb_results:
            context_str = "\n".join([f"- {r['content']}" for r in kb_results])
            prompt = f"""You are Memora AI, an assistant for the {ws.name} workspace. 
            Answer the user's software engineering question using the following Knowledge Base context.
            If the context does not contain the answer, you can respond using your own programming knowledge but specify that it's not from the team's records.
            
            IMPORTANT: Keep your answer extremely concise, brief, and to the point. Do not output unnecessary tokens or long formatting.

            <context>
            {context_str}
            </context>

            User Question: {body.message}"""
        else:
            prompt = f"""You are Memora AI, an assistant for the {ws.name} workspace.
            The user asked a question, but there were no relevant documents found in the Knowledge Base (Make sure they have uploaded and synced data!).
            Please answer their question using your general programming knowledge, but politely mention that you couldn't find team-specific context.
            
            IMPORTANT: Keep your answer extremely concise, brief, and to the point. Do not output unnecessary tokens or long formatting.

            User Question: {body.message}"""

        # 3. Generate stream response using Converse API
        def iter_chat_stream():
            try:
                for chunk_text in agent_service._invoke_model_direct_stream(prompt):
                    yield chunk_text
            except Exception as e:
                logger.error("Error during streaming", exc_info=True)
                yield "\n\n[Error streaming response.]"

        from fastapi.responses import StreamingResponse
        return StreamingResponse(iter_chat_stream(), media_type="text/plain")
        
    except Exception as e:
        logger.error("Chat failure", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
