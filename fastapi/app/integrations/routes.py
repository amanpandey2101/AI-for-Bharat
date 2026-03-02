"""
Integration routes — connect/disconnect platforms, list repos, select resources.

User Flow:
1. GET  /integrations/                      → list connected platforms
2. GET  /integrations/{platform}/connect    → start OAuth flow (redirects to platform)
3. GET  /integrations/{platform}/callback   → handle OAuth callback (auto-saves integration)
4. GET  /integrations/{platform}/repos      → list available repos/projects/channels
5. POST /integrations/{platform}/repos      → select repos to monitor (auto-registers webhooks)
6. DELETE /integrations/{platform}          → disconnect platform (removes webhooks)
"""

import secrets
import logging
from typing import List

from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel

from app.config import settings
from app.utils.dependencies import get_current_user_id
from app.integrations.models import (
    IntegrationModel, IntegrationRepository, ConnectedResource,
)
from app.integrations.github_service import GitHubService
from app.integrations.gitlab_service import GitLabService
from app.integrations.slack_service import SlackService
from app.integrations.jira_service import JiraService

logger = logging.getLogger(__name__)

integration_router = APIRouter()


_oauth_states: dict = {}



class SelectReposRequest(BaseModel):
    """Request body for selecting repositories/projects/channels to monitor."""
    resource_ids: List[str]  # list of repo full_names / channel IDs / project keys
    resource_names: List[str] = []  # optional human-readable names



@integration_router.get("/")
def list_integrations(user_id: str = Depends(get_current_user_id)):
    """List all connected platform integrations for the current user."""
    integrations = IntegrationRepository.list_by_user(user_id)
    return {
        "integrations": [
            {
                "platform": i.platform,
                "status": i.status,
                "platform_username": i.platform_username,
                "connected_resources": len(i.resources),
                "resources": [
                    {"id": r.resource_id, "name": r.resource_name, "webhook_active": r.webhook_registered}
                    for r in i.resources
                ],
                "created_at": i.created_at,
            }
            for i in integrations
        ]
    }



@integration_router.get("/github/connect")
def github_connect(user_id: str = Depends(get_current_user_id)):
    """Start GitHub OAuth flow — redirects to GitHub authorization page.
    Uses 'integration:' prefix in state so the shared /auth/github/callback
    knows to route here instead of the login flow.
    """
    state = f"integration:{secrets.token_urlsafe(32)}"
    _oauth_states[state] = {"user_id": user_id, "platform": "github"}
    return RedirectResponse(GitHubService.get_oauth_url(state))


def handle_github_integration_callback(code: str, state: str):
    """Called from auth/routes.py when state starts with 'integration:'.
    Exchange code, save integration, redirect to frontend.
    """
    session = _oauth_states.pop(state, None)
    if not session:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    user_id = session["user_id"]

    # Exchange code for token
    token_data = GitHubService.exchange_code(code)
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to get access token from GitHub")

    # Get GitHub user info
    gh_user = GitHubService.get_user_info(access_token)

    # Save integration
    integration = IntegrationModel(
        user_id=user_id,
        platform="github",
        access_token=access_token,
        scopes=token_data.get("scope", "").split(","),
        platform_user_id=str(gh_user.get("id", "")),
        platform_username=gh_user.get("login"),
    )
    IntegrationRepository.save(integration)

    # Redirect to frontend integrations page
    return RedirectResponse(f"{settings.FRONTEND_URL}/dashboard/integrations?connected=github")


@integration_router.get("/github/repos")
def github_list_repos(user_id: str = Depends(get_current_user_id)):
    """List GitHub repositories available to the user."""
    integration = IntegrationRepository.get(user_id, "github")
    if not integration:
        raise HTTPException(status_code=404, detail="GitHub not connected. Please connect first.")

    repos = GitHubService.list_repos(integration.access_token)
    return {"repos": repos}


@integration_router.post("/github/repos")
def github_select_repos(body: SelectReposRequest, user_id: str = Depends(get_current_user_id)):
    """Select GitHub repositories to monitor — auto-registers webhooks."""
    integration = IntegrationRepository.get(user_id, "github")
    if not integration:
        raise HTTPException(status_code=404, detail="GitHub not connected")

    webhook_base = f"{settings.API_BASE_URL}/webhooks/github"
    results = []

    for i, repo_name in enumerate(body.resource_ids):
        display_name = body.resource_names[i] if i < len(body.resource_names) else repo_name

        # Register webhook via GitHub API
        hook = GitHubService.register_webhook(
            access_token=integration.access_token,
            repo_full_name=repo_name,
            webhook_url=webhook_base,
            webhook_secret=integration.webhook_secret,
        )

        resource = ConnectedResource(
            resource_id=repo_name,
            resource_name=display_name,
            resource_type="repository",
            webhook_registered=hook is not None,
            platform_webhook_id=str(hook["id"]) if hook else None,
        )
        integration.resources.append(resource)
        results.append({
            "repo": repo_name,
            "webhook_registered": hook is not None,
        })

    IntegrationRepository.save(integration)
    return {"results": results}


# ── GitLab ─────────────────────────────────────────────────────────────────────

@integration_router.get("/gitlab/connect")
def gitlab_connect(user_id: str = Depends(get_current_user_id)):
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = {"user_id": user_id, "platform": "gitlab"}
    return RedirectResponse(GitLabService.get_oauth_url(state))


@integration_router.get("/gitlab/callback")
def gitlab_callback(code: str = Query(...), state: str = Query(...)):
    session = _oauth_states.pop(state, None)
    if not session:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    user_id = session["user_id"]
    token_data = GitLabService.exchange_code(code)
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to get access token from GitLab")

    gl_user = GitLabService.get_user_info(access_token)

    integration = IntegrationModel(
        user_id=user_id,
        platform="gitlab",
        access_token=access_token,
        refresh_token=token_data.get("refresh_token"),
        scopes=token_data.get("scope", "").split(" "),
        platform_user_id=str(gl_user.get("id", "")),
        platform_username=gl_user.get("username"),
    )
    IntegrationRepository.save(integration)
    return RedirectResponse(f"{settings.FRONTEND_URL}/integrations?connected=gitlab")


@integration_router.get("/gitlab/repos")
def gitlab_list_repos(user_id: str = Depends(get_current_user_id)):
    integration = IntegrationRepository.get(user_id, "gitlab")
    if not integration:
        raise HTTPException(status_code=404, detail="GitLab not connected")
    projects = GitLabService.list_projects(integration.access_token)
    return {"repos": projects}


@integration_router.post("/gitlab/repos")
def gitlab_select_repos(body: SelectReposRequest, user_id: str = Depends(get_current_user_id)):
    integration = IntegrationRepository.get(user_id, "gitlab")
    if not integration:
        raise HTTPException(status_code=404, detail="GitLab not connected")

    webhook_base = f"{settings.API_BASE_URL}/webhooks/gitlab"
    results = []

    for i, project_id in enumerate(body.resource_ids):
        display_name = body.resource_names[i] if i < len(body.resource_names) else project_id
        hook = GitLabService.register_webhook(
            access_token=integration.access_token,
            project_id=project_id,
            webhook_url=webhook_base,
            webhook_secret=integration.webhook_secret,
        )
        resource = ConnectedResource(
            resource_id=project_id,
            resource_name=display_name,
            resource_type="repository",
            webhook_registered=hook is not None,
            platform_webhook_id=str(hook["id"]) if hook else None,
        )
        integration.resources.append(resource)
        results.append({"project": project_id, "webhook_registered": hook is not None})

    IntegrationRepository.save(integration)
    return {"results": results}


# ── Slack ──────────────────────────────────────────────────────────────────────

@integration_router.get("/slack/connect")
def slack_connect(user_id: str = Depends(get_current_user_id)):
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = {"user_id": user_id, "platform": "slack"}
    return RedirectResponse(SlackService.get_oauth_url(state))


@integration_router.get("/slack/callback")
def slack_callback(code: str = Query(...), state: str = Query(...)):
    session = _oauth_states.pop(state, None)
    if not session:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    user_id = session["user_id"]
    token_data = SlackService.exchange_code(code)

    if not token_data.get("ok"):
        raise HTTPException(status_code=400, detail=f"Slack OAuth error: {token_data.get('error')}")

    access_token = token_data.get("access_token")
    team = token_data.get("team", {})

    integration = IntegrationModel(
        user_id=user_id,
        platform="slack",
        access_token=access_token,
        platform_user_id=token_data.get("bot_user_id"),
        platform_org=team.get("id"),
        platform_username=team.get("name"),
    )
    IntegrationRepository.save(integration)
    return RedirectResponse(f"{settings.FRONTEND_URL}/integrations?connected=slack")


@integration_router.get("/slack/channels")
def slack_list_channels(user_id: str = Depends(get_current_user_id)):
    """List Slack channels the bot can access."""
    integration = IntegrationRepository.get(user_id, "slack")
    if not integration:
        raise HTTPException(status_code=404, detail="Slack not connected")
    channels = SlackService.list_channels(integration.access_token)
    return {"channels": channels}


@integration_router.post("/slack/channels")
def slack_select_channels(body: SelectReposRequest, user_id: str = Depends(get_current_user_id)):
    """Select Slack channels to monitor (events auto-flow, this just tracks which channels matter)."""
    integration = IntegrationRepository.get(user_id, "slack")
    if not integration:
        raise HTTPException(status_code=404, detail="Slack not connected")

    for i, channel_id in enumerate(body.resource_ids):
        name = body.resource_names[i] if i < len(body.resource_names) else channel_id
        resource = ConnectedResource(
            resource_id=channel_id,
            resource_name=name,
            resource_type="channel",
            webhook_registered=True,  # Slack events flow automatically
        )
        integration.resources.append(resource)

    IntegrationRepository.save(integration)
    return {"results": [{"channel": c, "monitored": True} for c in body.resource_ids]}


# ── Jira ───────────────────────────────────────────────────────────────────────

@integration_router.get("/jira/connect")
def jira_connect(user_id: str = Depends(get_current_user_id)):
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = {"user_id": user_id, "platform": "jira"}
    return RedirectResponse(JiraService.get_oauth_url(state))


@integration_router.get("/jira/callback")
def jira_callback(code: str = Query(...), state: str = Query(...)):
    session = _oauth_states.pop(state, None)
    if not session:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    user_id = session["user_id"]
    token_data = JiraService.exchange_code(code)
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to get Jira access token")

    # Get accessible Jira sites
    sites = JiraService.get_accessible_sites(access_token)
    cloud_id = sites[0]["id"] if sites else None

    integration = IntegrationModel(
        user_id=user_id,
        platform="jira",
        access_token=access_token,
        refresh_token=token_data.get("refresh_token"),
        platform_org=cloud_id,
    )
    IntegrationRepository.save(integration)
    return RedirectResponse(f"{settings.FRONTEND_URL}/integrations?connected=jira")


@integration_router.get("/jira/projects")
def jira_list_projects(user_id: str = Depends(get_current_user_id)):
    integration = IntegrationRepository.get(user_id, "jira")
    if not integration or not integration.platform_org:
        raise HTTPException(status_code=404, detail="Jira not connected")
    projects = JiraService.list_projects(integration.access_token, integration.platform_org)
    return {"projects": projects}


@integration_router.post("/jira/projects")
def jira_select_projects(body: SelectReposRequest, user_id: str = Depends(get_current_user_id)):
    integration = IntegrationRepository.get(user_id, "jira")
    if not integration or not integration.platform_org:
        raise HTTPException(status_code=404, detail="Jira not connected")

    webhook_base = f"{settings.API_BASE_URL}/webhooks/jira"
    results = []

    for i, project_key in enumerate(body.resource_ids):
        name = body.resource_names[i] if i < len(body.resource_names) else project_key
        hook = JiraService.register_webhook(
            access_token=integration.access_token,
            cloud_id=integration.platform_org,
            webhook_url=webhook_base,
            project_key=project_key,
        )
        resource = ConnectedResource(
            resource_id=project_key,
            resource_name=name,
            resource_type="project",
            webhook_registered=hook is not None,
        )
        integration.resources.append(resource)
        results.append({"project": project_key, "webhook_registered": hook is not None})

    IntegrationRepository.save(integration)
    return {"results": results}


# ── Disconnect ─────────────────────────────────────────────────────────────────

@integration_router.delete("/{platform}")
def disconnect_platform(platform: str, user_id: str = Depends(get_current_user_id)):
    """Disconnect a platform — removes webhooks and deletes the integration."""
    integration = IntegrationRepository.get(user_id, platform)
    if not integration:
        raise HTTPException(status_code=404, detail=f"{platform} not connected")

    # Attempt to delete webhooks from the platform
    for resource in integration.resources:
        if resource.platform_webhook_id:
            try:
                if platform == "github":
                    GitHubService.delete_webhook(
                        integration.access_token, resource.resource_id, resource.platform_webhook_id
                    )
                elif platform == "gitlab":
                    GitLabService.delete_webhook(
                        integration.access_token, resource.resource_id, resource.platform_webhook_id
                    )
            except Exception:
                logger.warning(f"Failed to delete webhook for {resource.resource_id}", exc_info=True)

    IntegrationRepository.delete(user_id, platform)
    return {"status": "disconnected", "platform": platform}
