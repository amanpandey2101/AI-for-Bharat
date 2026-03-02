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
    user_id: str = Depends(get_current_user_id),
):
    """List decisions scoped to this workspace's resources."""
    from app.decisions import DecisionRepository

    ws = WorkspaceRepository.get(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

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
        if d.repository in resource_ids or not resource_ids
    ][:limit]

    return {
        "decisions": [
            {
                "decision_id": d.decision_id,
                "title": d.title,
                "description": d.description,
                "repository": d.repository,
                "platform": d.platform,
                "status": d.status,
                "confidence": d.confidence.overall,
                "tags": d.tags,
                "created_at": d.created_at,
            }
            for d in workspace_decisions
        ],
        "total": len(workspace_decisions),
        "workspace_id": workspace_id,
    }
