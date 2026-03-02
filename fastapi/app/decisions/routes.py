"""
Decision API routes — list, get, validate, search decisions.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.utils.dependencies import get_current_user_id
from app.decisions import (
    DecisionRepository,
    DecisionEntity,
    DecisionStatus,
)

logger = logging.getLogger(__name__)

decision_router = APIRouter()


class ValidateRequest(BaseModel):
    status: str  # "validated" or "disputed"
    comment: Optional[str] = None


class SearchRequest(BaseModel):
    question: str


# ── Stats (must come before /{decision_id}) ────────────────────────────────────

@decision_router.get("/stats/overview")
def decision_stats(user_id: str = Depends(get_current_user_id)):
    """Get high-level decision stats."""
    all_decisions = DecisionRepository.list_recent(200)

    total = len(all_decisions)
    by_status = {}
    by_platform = {}
    avg_confidence = 0.0

    for d in all_decisions:
        by_status[d.status] = by_status.get(d.status, 0) + 1
        by_platform[d.platform] = by_platform.get(d.platform, 0) + 1
        avg_confidence += d.confidence.overall

    return {
        "total_decisions": total,
        "by_status": by_status,
        "by_platform": by_platform,
        "avg_confidence": round(avg_confidence / total, 2) if total > 0 else 0,
        "pending_validation": by_status.get("inferred", 0),
    }


# ── Semantic Search (Bedrock Agent + Knowledge Base) ───────────────────────────

@decision_router.post("/search")
def search_decisions_semantic(
    body: SearchRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    Semantic search: ask a natural language question about past decisions.
    Uses the Bedrock Agent + Knowledge Base for retrieval-augmented generation.
    """
    from app.agents.bedrock_agent import agent_service

    answer = agent_service.search_decisions(body.question)
    kb_results = agent_service.retrieve_from_kb(body.question, max_results=5)

    return {
        "answer": answer,
        "sources": kb_results,
        "question": body.question,
    }


@decision_router.get("/search/kb")
def search_kb_direct(
    q: str = Query(...),
    limit: int = Query(5, le=20),
    user_id: str = Depends(get_current_user_id),
):
    """Direct Knowledge Base vector search — returns matching decision documents."""
    from app.agents.bedrock_agent import agent_service

    results = agent_service.retrieve_from_kb(q, max_results=limit)
    return {"results": results, "query": q}


# ── List decisions ─────────────────────────────────────────────────────────────

@decision_router.get("/")
def list_decisions(
    status: Optional[str] = Query(None),
    repository: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    user_id: str = Depends(get_current_user_id),
):
    """List decisions — optionally filter by status or repository."""
    if repository:
        decisions = DecisionRepository.list_by_repository(repository, limit)
    elif status:
        decisions = DecisionRepository.list_by_status(status, limit)
    else:
        decisions = DecisionRepository.list_recent(limit)

    return {
        "decisions": [
            {
                "decision_id": d.decision_id,
                "title": d.title,
                "description": d.description,
                "rationale": d.rationale,
                "repository": d.repository,
                "platform": d.platform,
                "status": d.status,
                "confidence": d.confidence.overall,
                "confidence_factors": d.confidence.model_dump(),
                "participants": d.participants,
                "tags": d.tags,
                "created_at": d.created_at,
                "evidence_count": (
                    len(d.intent) + len(d.execution) + len(d.authority) + len(d.outcomes)
                ),
            }
            for d in decisions
        ],
        "total": len(decisions),
    }


# ── Get single decision ───────────────────────────────────────────────────────

@decision_router.get("/{decision_id}")
def get_decision(
    decision_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Get a single decision with full evidence chain."""
    decision = DecisionRepository.get(decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    return {
        "decision": decision.model_dump(),
    }


# ── Validate / Dispute ────────────────────────────────────────────────────────

@decision_router.post("/{decision_id}/validate")
def validate_decision(
    decision_id: str,
    body: ValidateRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Human-in-the-loop: validate or dispute an AI-inferred decision."""
    decision = DecisionRepository.get(decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    new_status = DecisionStatus(body.status)
    DecisionRepository.update_status(decision_id, new_status)

    logger.info(f"Decision {decision_id} status updated to {new_status} by {user_id}")

    return {
        "decision_id": decision_id,
        "new_status": new_status.value,
        "message": f"Decision {new_status.value}.",
    }


# ── Delete ─────────────────────────────────────────────────────────────────────

@decision_router.delete("/{decision_id}")
def delete_decision(
    decision_id: str,
    user_id: str = Depends(get_current_user_id),
):
    DecisionRepository.delete(decision_id)
    return {"status": "deleted", "decision_id": decision_id}

