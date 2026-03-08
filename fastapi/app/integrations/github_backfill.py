"""
GitHub repository history backfill service.

When a user connects a GitHub repo, this service fetches existing
PRs, commits, and issues, processes them through the Bedrock Agent
decision inference pipeline, and syncs results into the Knowledge Base.

Runs as a background daemon thread — does not block the API response.
"""

import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

import requests as http_requests

from app.config import settings
from app.integrations.models import IntegrationRepository
from app.webhooks.models import (
    IngestionEvent,
    Platform,
    EventType,
    EventStatus,
    EventContext,
    EventAuthor,
)
from app.webhooks.event_store import EventRepository

logger = logging.getLogger(__name__)

GITHUB_API_URL = "https://api.github.com"


# ── Rate Limiter ──────────────────────────────────────────────────────────────


class GitHubRateLimiter:
    """Simple rate limiter using GitHub's X-RateLimit headers."""

    def __init__(
        self,
        min_remaining: int = settings.BACKFILL_RATE_LIMIT_THRESHOLD,
        base_delay: float = settings.BACKFILL_API_DELAY,
    ):
        self.min_remaining = min_remaining
        self.base_delay = base_delay

    def wait_if_needed(self, response: http_requests.Response):
        remaining = int(response.headers.get("X-RateLimit-Remaining", 5000))
        reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
        if remaining < self.min_remaining:
            wait = max(0, reset_time - time.time()) + 1
            logger.info(
                f"[Backfill] Rate limit approaching ({remaining} remaining), "
                f"sleeping {wait:.0f}s"
            )
            time.sleep(wait)
        else:
            time.sleep(self.base_delay)


# ── Backfill Service ──────────────────────────────────────────────────────────


class GitHubBackfillService:
    """Fetches historical GitHub data with pagination and rate limiting."""

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.rate_limiter = GitHubRateLimiter()
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
        }

    def _get(self, url: str, params: Optional[Dict] = None) -> http_requests.Response:
        response = http_requests.get(url, headers=self.headers, params=params)
        self.rate_limiter.wait_if_needed(response)
        return response

    def _paginate(
        self, url: str, params: Dict, max_pages: int
    ) -> List[Dict]:
        items = []
        for page in range(1, max_pages + 1):
            params["page"] = page
            params.setdefault("per_page", 100)
            resp = self._get(url, params)
            if resp.status_code != 200:
                logger.warning(
                    f"[Backfill] API {resp.status_code} for {url} page {page}"
                )
                break
            data = resp.json()
            if not data:
                break
            items.extend(data)
            if len(data) < params["per_page"]:
                break
        return items

    def fetch_closed_prs(self, repo: str) -> List[Dict]:
        max_pages = settings.BACKFILL_MAX_PRS // 100 or 1
        return self._paginate(
            f"{GITHUB_API_URL}/repos/{repo}/pulls",
            {"state": "closed", "sort": "updated", "direction": "desc"},
            max_pages=max_pages,
        )

    def fetch_pr_reviews(self, repo: str, pr_number: int) -> List[Dict]:
        resp = self._get(
            f"{GITHUB_API_URL}/repos/{repo}/pulls/{pr_number}/reviews"
        )
        if resp.status_code != 200:
            return []
        return resp.json()

    def fetch_recent_commits(self, repo: str) -> List[Dict]:
        max_pages = settings.BACKFILL_MAX_COMMITS // 100 or 1
        return self._paginate(
            f"{GITHUB_API_URL}/repos/{repo}/commits",
            {"per_page": 100},
            max_pages=max_pages,
        )

    def fetch_closed_issues(self, repo: str) -> List[Dict]:
        max_pages = settings.BACKFILL_MAX_ISSUES // 100 or 1
        items = self._paginate(
            f"{GITHUB_API_URL}/repos/{repo}/issues",
            {"state": "closed", "sort": "updated", "direction": "desc"},
            max_pages=max_pages,
        )
        # Filter out pull requests (GitHub returns PRs as issues)
        return [i for i in items if "pull_request" not in i]

    def fetch_issue_comments(self, repo: str, issue_number: int) -> List[Dict]:
        resp = self._get(
            f"{GITHUB_API_URL}/repos/{repo}/issues/{issue_number}/comments"
        )
        if resp.status_code != 200:
            return []
        return resp.json()


# ── Event Converters ──────────────────────────────────────────────────────────


def _extract_author(user: Optional[Dict]) -> EventAuthor:
    if not user:
        return EventAuthor(name="unknown")
    return EventAuthor(
        name=user.get("login", "unknown"),
        username=user.get("login"),
        platform_id=str(user.get("id", "")),
        avatar_url=user.get("avatar_url"),
    )


def _pr_to_event(pr: Dict, repo: str) -> IngestionEvent:
    is_merged = pr.get("merged_at") is not None
    return IngestionEvent(
        platform=Platform.GITHUB,
        event_type=EventType.PR_MERGED if is_merged else EventType.PR_CLOSED,
        title=pr.get("title"),
        description=pr.get("body"),
        content=pr.get("body", ""),
        context=EventContext(
            repository=repo,
            organisation=repo.split("/")[0],
            url=pr.get("html_url"),
        ),
        author=_extract_author(pr.get("user")),
        timestamp=pr.get("merged_at") or pr.get("closed_at") or pr.get("updated_at", ""),
        tags=["backfill", "pull_request"],
    )


def _review_to_event(review: Dict, pr: Dict, repo: str) -> IngestionEvent:
    return IngestionEvent(
        platform=Platform.GITHUB,
        event_type=EventType.REVIEW_SUBMITTED,
        title=f"Review on: {pr.get('title', '')}",
        description=review.get("body"),
        content=review.get("body", ""),
        context=EventContext(
            repository=repo,
            organisation=repo.split("/")[0],
            url=review.get("html_url"),
        ),
        author=_extract_author(review.get("user")),
        timestamp=review.get("submitted_at", ""),
        tags=["backfill", "review"],
    )


def _commit_to_event(commit: Dict, repo: str) -> IngestionEvent:
    commit_data = commit.get("commit", {})
    author_info = commit.get("author")  # GitHub user object (may be null)
    commit_author = commit_data.get("author", {})
    return IngestionEvent(
        platform=Platform.GITHUB,
        event_type=EventType.COMMIT_PUSHED,
        title=commit_data.get("message", "").split("\n")[0][:120],
        description=commit_data.get("message"),
        content=commit_data.get("message", ""),
        context=EventContext(
            repository=repo,
            organisation=repo.split("/")[0],
            url=commit.get("html_url"),
        ),
        author=_extract_author(author_info) if author_info else EventAuthor(
            name=commit_author.get("name", "unknown"),
            email=commit_author.get("email"),
        ),
        timestamp=commit_author.get("date", ""),
        tags=["backfill", "commit"],
    )


def _issue_to_event(issue: Dict, repo: str) -> IngestionEvent:
    return IngestionEvent(
        platform=Platform.GITHUB,
        event_type=EventType.ISSUE_CLOSED,
        title=issue.get("title"),
        description=issue.get("body"),
        content=issue.get("body", ""),
        context=EventContext(
            repository=repo,
            organisation=repo.split("/")[0],
            url=issue.get("html_url"),
        ),
        author=_extract_author(issue.get("user")),
        timestamp=issue.get("closed_at") or issue.get("updated_at", ""),
        tags=["backfill", "issue"],
    )


def _comment_to_event(comment: Dict, issue: Dict, repo: str) -> IngestionEvent:
    return IngestionEvent(
        platform=Platform.GITHUB,
        event_type=EventType.ISSUE_COMMENTED,
        title=f"Comment on: {issue.get('title', '')}",
        description=comment.get("body"),
        content=comment.get("body", ""),
        context=EventContext(
            repository=repo,
            organisation=repo.split("/")[0],
            url=comment.get("html_url"),
        ),
        author=_extract_author(comment.get("user")),
        timestamp=comment.get("created_at", ""),
        tags=["backfill", "comment"],
    )


# ── Status Tracker ────────────────────────────────────────────────────────────


def _update_backfill_status(
    user_id: str,
    platform: str,
    repo_full_name: str,
    status: str,
    progress: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
):
    """Update backfill status on the ConnectedResource in DynamoDB."""
    try:
        integration = IntegrationRepository.get(user_id, platform)
        if not integration:
            return
        for resource in integration.resources:
            if resource.resource_id == repo_full_name:
                resource.backfill_status = status
                if progress:
                    resource.backfill_progress = progress
                if error:
                    resource.backfill_error = error
                if status == "in_progress" and not resource.backfill_started_at:
                    resource.backfill_started_at = datetime.utcnow().isoformat()
                if status in ("completed", "failed"):
                    resource.backfill_completed_at = datetime.utcnow().isoformat()
                break
        IntegrationRepository.save(integration)
    except Exception:
        logger.error(f"[Backfill] Failed to update status for {repo_full_name}", exc_info=True)


# ── Process Single Event ──────────────────────────────────────────────────────


def _process_single_event(event: IngestionEvent) -> bool:
    """Save event and process through Bedrock Agent. Returns True if a decision was found."""
    from app.agents.bedrock_agent import process_event_for_decisions

    event.status = EventStatus.QUEUED
    EventRepository.save(event)

    try:
        result = process_event_for_decisions(event.to_agent_dict())
        EventRepository.update_status(event.event_id, EventStatus.PROCESSED)
        return result is not None
    except Exception:
        logger.error(f"[Backfill] Failed to process event {event.event_id}", exc_info=True)
        try:
            EventRepository.update_status(event.event_id, EventStatus.FAILED)
        except Exception:
            pass
        return False


# ── Main Orchestrator ─────────────────────────────────────────────────────────


def run_backfill_for_repo(
    access_token: str,
    repo_full_name: str,
    user_id: str,
    platform: str,
):
    """
    Main backfill entry point — runs in a background thread.

    Fetches historical PRs, commits, and issues from a GitHub repo,
    processes each through the Bedrock Agent pipeline, then triggers
    a single KB sync at the end.
    """
    logger.info(f"[Backfill] Starting backfill for {repo_full_name}")
    _update_backfill_status(user_id, platform, repo_full_name, "in_progress")

    service = GitHubBackfillService(access_token)
    progress = {
        "prs_processed": 0,
        "reviews_processed": 0,
        "commits_processed": 0,
        "issues_processed": 0,
        "comments_processed": 0,
        "decisions_found": 0,
    }

    try:
        # ── Phase 1: Closed / Merged PRs + Reviews ────────────────────────
        logger.info(f"[Backfill] Phase 1: Fetching closed PRs for {repo_full_name}")
        prs = service.fetch_closed_prs(repo_full_name)
        logger.info(f"[Backfill] Fetched {len(prs)} closed PRs")

        for pr in prs:
            try:
                event = _pr_to_event(pr, repo_full_name)
                if _process_single_event(event):
                    progress["decisions_found"] += 1
                progress["prs_processed"] += 1

                # Fetch reviews for this PR
                reviews = service.fetch_pr_reviews(repo_full_name, pr["number"])
                for review in reviews:
                    if not review.get("body"):
                        continue
                    try:
                        rev_event = _review_to_event(review, pr, repo_full_name)
                        if _process_single_event(rev_event):
                            progress["decisions_found"] += 1
                        progress["reviews_processed"] += 1
                    except Exception:
                        logger.error(f"[Backfill] Failed to process review", exc_info=True)
            except Exception:
                logger.error(f"[Backfill] Failed to process PR #{pr.get('number')}", exc_info=True)

        _update_backfill_status(user_id, platform, repo_full_name, "in_progress", progress)

        # ── Phase 2: Recent Commits ───────────────────────────────────────
        logger.info(f"[Backfill] Phase 2: Fetching commits for {repo_full_name}")
        commits = service.fetch_recent_commits(repo_full_name)
        logger.info(f"[Backfill] Fetched {len(commits)} commits")

        for commit in commits:
            try:
                event = _commit_to_event(commit, repo_full_name)
                if _process_single_event(event):
                    progress["decisions_found"] += 1
                progress["commits_processed"] += 1
            except Exception:
                logger.error(f"[Backfill] Failed to process commit", exc_info=True)

        _update_backfill_status(user_id, platform, repo_full_name, "in_progress", progress)

        # ── Phase 3: Closed Issues + Comments ─────────────────────────────
        logger.info(f"[Backfill] Phase 3: Fetching closed issues for {repo_full_name}")
        issues = service.fetch_closed_issues(repo_full_name)
        logger.info(f"[Backfill] Fetched {len(issues)} closed issues")

        for issue in issues:
            try:
                event = _issue_to_event(issue, repo_full_name)
                if _process_single_event(event):
                    progress["decisions_found"] += 1
                progress["issues_processed"] += 1

                # Fetch comments for issues that have them
                if issue.get("comments", 0) > 0:
                    comments = service.fetch_issue_comments(
                        repo_full_name, issue["number"]
                    )
                    for comment in comments:
                        if not comment.get("body"):
                            continue
                        try:
                            cmt_event = _comment_to_event(comment, issue, repo_full_name)
                            if _process_single_event(cmt_event):
                                progress["decisions_found"] += 1
                            progress["comments_processed"] += 1
                        except Exception:
                            logger.error(f"[Backfill] Failed to process comment", exc_info=True)
            except Exception:
                logger.error(f"[Backfill] Failed to process issue #{issue.get('number')}", exc_info=True)

        # ── Final: Sync Knowledge Base once ───────────────────────────────
        if progress["decisions_found"] > 0:
            logger.info(
                f"[Backfill] Triggering KB sync — {progress['decisions_found']} decisions found"
            )
            from app.agents.bedrock_agent import agent_service
            agent_service.sync_knowledge_base()

        _update_backfill_status(user_id, platform, repo_full_name, "completed", progress)
        logger.info(
            f"[Backfill] Completed for {repo_full_name}: "
            f"{progress['prs_processed']} PRs, {progress['commits_processed']} commits, "
            f"{progress['issues_processed']} issues, {progress['decisions_found']} decisions"
        )

    except Exception as e:
        logger.error(f"[Backfill] Fatal error for {repo_full_name}", exc_info=True)
        _update_backfill_status(
            user_id, platform, repo_full_name, "failed", progress, str(e)
        )
