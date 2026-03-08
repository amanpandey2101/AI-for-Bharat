"""
Workspace API routes — create, list, manage workspaces and their resources.
"""

import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel

from app.utils.dependencies import get_current_user_id
from app.workspaces import (
    Workspace,
    WorkspaceRepository,
    ConnectedResource,
    WorkspaceMember,
)

logger = logging.getLogger(__name__)

workspace_router = APIRouter()


# ── Request models ─────────────────────────────────────────────────────────────

class CreateWorkspaceRequest(BaseModel):
    name: str
    description: str = ""


class UpdateWorkspaceRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class AddResourceRequest(BaseModel):
    platform: str
    resource_id: str
    resource_name: str
    resource_type: str = "repository"


class RemoveResourceRequest(BaseModel):
    platform: str
    resource_id: str


# ── CRUD ───────────────────────────────────────────────────────────────────────

@workspace_router.post("/")
def create_workspace(
    body: CreateWorkspaceRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Create a new workspace."""
    ws = Workspace(
        name=body.name,
        description=body.description,
        owner_id=user_id,
        members=[WorkspaceMember(user_id=user_id, role="owner")],
    )
    WorkspaceRepository.save(ws)
    logger.info(f"Workspace created: {ws.workspace_id} by {user_id}")
    return {"workspace": ws.model_dump()}


@workspace_router.get("/")
def list_workspaces(
    user_id: str = Depends(get_current_user_id),
):
    """List all workspaces for the current user."""
    workspaces = WorkspaceRepository.list_by_owner(user_id)
    return {
        "workspaces": [ws.model_dump() for ws in workspaces],
        "total": len(workspaces),
    }


@workspace_router.get("/{workspace_id}")
def get_workspace(
    workspace_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Get a single workspace with all its resources."""
    ws = WorkspaceRepository.get(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {"workspace": ws.model_dump()}


@workspace_router.patch("/{workspace_id}")
def update_workspace(
    workspace_id: str,
    body: UpdateWorkspaceRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Update workspace name or description."""
    ws = WorkspaceRepository.get(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if body.name is not None:
        ws.name = body.name
    if body.description is not None:
        ws.description = body.description

    WorkspaceRepository.save(ws)
    return {"workspace": ws.model_dump()}


@workspace_router.delete("/{workspace_id}")
def delete_workspace(
    workspace_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Delete a workspace."""
    WorkspaceRepository.delete(workspace_id)
    return {"status": "deleted", "workspace_id": workspace_id}


# ── Resource Management ────────────────────────────────────────────────────────

@workspace_router.post("/{workspace_id}/resources")
def add_resource(
    workspace_id: str,
    body: AddResourceRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Add a resource (repo, channel, project) to a workspace."""
    resource = ConnectedResource(
        platform=body.platform,
        resource_id=body.resource_id,
        resource_name=body.resource_name,
        resource_type=body.resource_type,
    )
    ws = WorkspaceRepository.add_resource(workspace_id, resource)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {"workspace": ws.model_dump()}


@workspace_router.delete("/{workspace_id}/resources")
def remove_resource(
    workspace_id: str,
    body: RemoveResourceRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Remove a resource from a workspace."""
    ws = WorkspaceRepository.remove_resource(
        workspace_id, body.platform, body.resource_id
    )
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {"workspace": ws.model_dump()}


@workspace_router.get("/{workspace_id}/resources")
def list_resources(
    workspace_id: str,
    platform: Optional[str] = Query(None),
    user_id: str = Depends(get_current_user_id),
):
    """List resources in a workspace, optionally filtered by platform."""
    ws = WorkspaceRepository.get(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    resources = ws.resources
    if platform:
        resources = [r for r in resources if r.platform == platform]

    return {
        "resources": [r.model_dump() for r in resources],
        "total": len(resources),
    }


# ── Workspace-scoped data ─────────────────────────────────────────────────────

@workspace_router.get("/{workspace_id}/decisions")
def list_workspace_decisions(
    workspace_id: str,
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(get_current_user_id),
):
    """List decisions scoped to this workspace's resources."""
    from app.decisions import DecisionRepository

    ws = WorkspaceRepository.get(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Access control: ensure user is owner or member
    is_owner = ws.owner_id == user_id
    is_member = any(m.user_id == user_id for m in ws.members)
    if not (is_owner or is_member):
        raise HTTPException(status_code=403, detail="Not authorized to access this workspace")

    # Get resource IDs for this workspace
    resource_ids = {r.resource_id for r in ws.resources}

    # Get all decisions and filter by workspace resources
    if status:
        all_decisions = DecisionRepository.list_by_status(status, limit=200)
    else:
        all_decisions = DecisionRepository.list_recent(limit=200)

    # Filter to only decisions from workspace resources
    workspace_decisions = [
        d for d in all_decisions
        if d.repository in resource_ids
    ]
    
    total = len(workspace_decisions)
    paginated = workspace_decisions[offset : offset + limit]

    return {
        "decisions": [
            {
                "decision_id": d.decision_id,
                "title": d.title,
                "description": d.description,
                "rationale": d.rationale,
                "alternatives_considered": d.alternatives_considered,
                "repository": d.repository,
                "platform": d.platform,
                "status": getattr(d.status, "value", d.status),
                "confidence": d.confidence.overall,
                "tags": d.tags,
                "created_at": d.created_at,
                "evidence_count": (
                    len(d.intent) + len(d.execution) + len(d.authority) + len(d.outcomes)
                ),
            }
            for d in paginated
        ],
        "total": total,
        "has_more": offset + limit < total,
        "workspace_id": workspace_id,
    }


@workspace_router.get("/{workspace_id}/decisions/stats")
def workspace_decision_stats(
    workspace_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Get high-level decision stats scoped to a workspace."""
    from app.decisions import DecisionRepository

    ws = WorkspaceRepository.get(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    is_owner = ws.owner_id == user_id
    is_member = any(m.user_id == user_id for m in ws.members)
    if not (is_owner or is_member):
        raise HTTPException(status_code=403, detail="Not authorized to access this workspace")

    resource_ids = {r.resource_id for r in ws.resources}
    all_decisions = DecisionRepository.list_recent(limit=200)

    workspace_decisions = [
        d for d in all_decisions
        if d.repository in resource_ids
    ]

    total = len(workspace_decisions)
    by_status = {}
    by_platform = {}
    avg_confidence = 0.0

    for d in workspace_decisions:
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


@workspace_router.get("/{workspace_id}/events")
def list_workspace_events(
    workspace_id: str,
    platform: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(get_current_user_id),
):
    """List recent ingestion events scoped to this workspace's resources."""
    from app.webhooks.event_store import EventRepository
    
    ws = WorkspaceRepository.get(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    is_owner = ws.owner_id == user_id
    is_member = any(m.user_id == user_id for m in ws.members)
    if not (is_owner or is_member):
        raise HTTPException(status_code=403, detail="Not authorized to access this workspace")

    # Which resources belong to this workspace
    # GitHub/GitLab uses 'repository', Slack uses 'channel', Jira uses 'project'
    resource_ids = {r.resource_id for r in ws.resources}
    
    events = []
    # Collect events across platforms. We need enough to cover the offset chunk.
    # In a truly scalable system this would be paginated with a LastEvaluatedKey.
    fetch_limit = offset + limit
    platforms_to_fetch = [platform] if platform else ["github", "gitlab", "slack", "jira"]
    for p in platforms_to_fetch:
        events.extend(EventRepository.list_by_platform(p, limit=fetch_limit))
    
    # Filter strictly to the workspace resources
    workspace_events = []
    for e in events:
        ctx = e.context
        if ctx.repository in resource_ids:
            workspace_events.append(e)
        elif ctx.channel in resource_ids:
            workspace_events.append(e)
        elif ctx.project in resource_ids:
            workspace_events.append(e)
            
    # Sort and paginate
    workspace_events.sort(key=lambda ev: ev.timestamp, reverse=True)
    total = len(workspace_events)
    paginated = workspace_events[offset : offset + limit]

    return {
        "count": len(paginated),
        "total": total,
        "has_more": offset + limit < total,
        "events": [
            {
                "event_id": e.event_id,
                "platform": e.platform.value,
                "event_type": e.event_type.value,
                "title": e.title,
                "status": e.status.value if hasattr(e.status, "value") else str(e.status),
                "timestamp": e.timestamp,
                "author": e.author.name if e.author else None,
                "repository": e.context.repository or e.context.project or e.context.channel or "",
            }
            for e in paginated
        ],
        "workspace_id": workspace_id,
    }
