"""
Architecture Decision Records API routes.
"""

import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from app.utils.dependencies import get_current_user_id
from app.workspaces import WorkspaceRepository
from app.adrs import ADR, ADRRepository

logger = logging.getLogger(__name__)

adr_router = APIRouter()

# ── Request models ─────────────────────────────────────────────────────────────

class CreateADRRequest(BaseModel):
    title: str
    context: str = ""
    decision: str = ""
    consequences: str = ""
    status: str = "proposed"


class UpdateADRRequest(BaseModel):
    title: Optional[str] = None
    context: Optional[str] = None
    decision: Optional[str] = None
    consequences: Optional[str] = None
    status: Optional[str] = None


class DraftADRRequest(BaseModel):
    topic: str



# ── Helpers ────────────────────────────────────────────────────────────────────

def verify_workspace_access(workspace_id: str, user_id: str):
    """Ensure the user has access. Simple check: if they own it or it exists."""
    # In a full RBAC system, we'd check WorkspaceMembers. For now, just owner check.
    ws = WorkspaceRepository.get(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    # For now, allow any authenticated user to view workspace data if they have the ID,
    # or restrict to owner depending on previous patterns. 
    # Current codebase relies heavily on owner_id for listing, but direct ID access might be open.
    return ws


# ── CRUD ───────────────────────────────────────────────────────────────────────

@adr_router.post("/workspaces/{workspace_id}/adrs")
def create_adr(
    workspace_id: str,
    body: CreateADRRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Create a new Architecture Decision Record in a workspace."""
    verify_workspace_access(workspace_id, user_id)
    
    adr = ADR(
        workspace_id=workspace_id,
        title=body.title,
        context=body.context,
        decision=body.decision,
        consequences=body.consequences,
        status=body.status,
        created_by=user_id,
    )
    ADRRepository.save(adr)
    logger.info(f"ADR created: {adr.adr_id} in workspace {workspace_id}")
    return {"adr": adr.model_dump()}


@adr_router.post("/workspaces/{workspace_id}/adrs/draft")
def draft_adr(
    workspace_id: str,
    body: DraftADRRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Auto-draft an Architecture Decision Record using Bedrock Agent KB."""
    verify_workspace_access(workspace_id, user_id)
    
    from app.agents.bedrock_agent import agent_service
    import json
    
    try:
        # Retrieve context from KB
        kb_results = agent_service.retrieve_from_kb(body.topic, max_results=5)
        context_str = "\n".join([f"- {r['content']}" for r in kb_results])
        
        prompt = f"""We need to document an Architecture Decision Record (ADR) about: '{body.topic}'.

Here is the retrieved context from our team's past discussions, PRs, and recorded decisions:
<context>
{context_str}
</context>

Based on this context (and your general engineering knowledge if the context is sparse), please draft the ADR.
You MUST output ONLY valid JSON in the exact following structure with no markdown formatting around it:
{{
  "title": "<A clear, concise title>",
  "context": "<Detailed context and problem statement based on the retrieved information>",
  "decision": "<The chosen solution and why>",
  "consequences": "<Expected positive and negative consequences>"
}}
"""
        response_text = agent_service._invoke_model_direct(prompt)
        
        if not response_text:
            raise ValueError("No response from Bedrock")
            
        try:
            return json.loads(response_text)
        except Exception:
            clean_text = response_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:-3]
            elif clean_text.startswith("```"):
                clean_text = clean_text[3:-3]
            return json.loads(clean_text)
            
    except Exception as e:
        logger.error(f"Failed to draft ADR: {str(e)}", exc_info=True)
        return {
            "title": body.topic.title(),
            "context": "Could not auto-generate context from Knowledge Base.",
            "decision": "",
            "consequences": ""
        }



@adr_router.get("/workspaces/{workspace_id}/adrs")
def list_adrs(
    workspace_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """List all ADRs for a specific workspace."""
    verify_workspace_access(workspace_id, user_id)
    adrs = ADRRepository.list_by_workspace(workspace_id)
    return {
        "adrs": [adr.model_dump() for adr in adrs],
        "total": len(adrs),
    }


@adr_router.get("/workspaces/{workspace_id}/adrs/{adr_id}")
def get_adr(
    workspace_id: str,
    adr_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Get a single ADR by ID."""
    verify_workspace_access(workspace_id, user_id)
    adr = ADRRepository.get(workspace_id, adr_id)
    if not adr:
        raise HTTPException(status_code=404, detail="ADR not found")
    return {"adr": adr.model_dump()}


@adr_router.patch("/workspaces/{workspace_id}/adrs/{adr_id}")
def update_adr(
    workspace_id: str,
    adr_id: str,
    body: UpdateADRRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Update an existing ADR."""
    verify_workspace_access(workspace_id, user_id)
    adr = ADRRepository.get(workspace_id, adr_id)
    if not adr:
        raise HTTPException(status_code=404, detail="ADR not found")

    if body.title is not None:
        adr.title = body.title
    if body.context is not None:
        adr.context = body.context
    if body.decision is not None:
        adr.decision = body.decision
    if body.consequences is not None:
        adr.consequences = body.consequences
    if body.status is not None:
        adr.status = body.status

    ADRRepository.save(adr)
    return {"adr": adr.model_dump()}


@adr_router.delete("/workspaces/{workspace_id}/adrs/{adr_id}")
def delete_adr(
    workspace_id: str,
    adr_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Delete an ADR."""
    verify_workspace_access(workspace_id, user_id)
    ADRRepository.delete(workspace_id, adr_id)
    return {"status": "deleted", "adr_id": adr_id}


# ── Export ─────────────────────────────────────────────────────────────────────

@adr_router.get("/workspaces/{workspace_id}/adrs/{adr_id}/export")
def export_adr(
    workspace_id: str,
    adr_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Export an ADR in standard Markdown format."""
    verify_workspace_access(workspace_id, user_id)
    adr = ADRRepository.get(workspace_id, adr_id)
    if not adr:
        raise HTTPException(status_code=404, detail="ADR not found")

    # Format as standard ADR Markdown
    date_str = adr.created_at[:10]  # YYYY-MM-DD
    md_content = f"""# {adr.title}

* Status: {adr.status}
* Date: {date_str}

## Context and Problem Statement
{adr.context or "No context provided."}

## Decision
{adr.decision or "No decision documented."}

## Consequences
{adr.consequences or "No consequences documented."}
"""
    
    # Return as plain text but with a markdown attachment filename
    return PlainTextResponse(
        content=md_content,
        headers={
            "Content-Disposition": f'attachment; filename="ADR_{adr.adr_id[:8]}.md"'
        },
    )
