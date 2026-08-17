"""Application service for the PR Review Agent.

Wires providers, probe, engine and persistence; dispatches webhook-triggered
reviews; exposes status. Always read-only with respect to GitHub.
"""

from __future__ import annotations

import logging

from app.context.di import Container
from app.coordinator.event_handler import EventEnvelope
from app.core.config import settings
from app.db.session import SessionLocal
from app.review.pr_provider import (
    FixturePullRequestProvider,
    GitHubPullRequestProvider,
    PullRequestProvider,
)
from app.review.review_agent import ReviewAgent
from app.review.review_context import RepositoryProbe
from app.review.review_engine import ReviewEngine
from app.review.review_models import (
    PRReview,
    ReviewRequest,
    ReviewStatus,
    ReviewUnavailable,
)
from app.review.review_repository import ReviewStore

logger = logging.getLogger(__name__)

_PULL_REQUEST_ACTIONS = {"opened", "synchronize", "reopened", "ready_for_review"}
_WORKFLOW_ACTION = "completed"


class ReviewService:
    def __init__(
        self,
        container: Container | None = None,
        session_factory=None,
        provider: PullRequestProvider | None = None,
        probe: RepositoryProbe | None = None,
        engine: ReviewEngine | None = None,
    ) -> None:
        self._container = container
        self._session_factory = session_factory or SessionLocal
        self._injected_provider = provider
        self._probe = probe or RepositoryProbe(self.container)
        self._engine = engine or ReviewEngine(self._probe)
        self._token: str | None = None

    @property
    def container(self) -> Container:
        if self._container is None:
            from app.api.dependencies import get_container

            self._container = get_container()
        return self._container

    # ------------------------------------------------------------------
    # main entry points
    # ------------------------------------------------------------------
    def submit(
        self,
        request: ReviewRequest,
        *,
        delivery_id: str | None = None,
        correlation_id: str | None = None,
    ) -> PRReview:
        if not settings.agent_review_enabled:
            raise ReviewUnavailable("review agent is disabled")
        db = self._session_factory()
        store = ReviewStore(db)
        row = None
        try:
            row = store.start_session(
                request.repository,
                request.pr_number,
                source=request.source,
                delivery_id=delivery_id,
                correlation_id=correlation_id,
            )
            agent = ReviewAgent(self._provider_for(request.repository), self._probe, self._engine)
            review = agent.review(request)
            store.persist_review(row, review)
            review.session_id = row.id
            logger.info(
                "review completed repo=%s pr=%d findings=%d delivery=%s",
                request.repository,
                request.pr_number,
                len(review.findings),
                delivery_id or "-",
            )
            return review
        except ReviewUnavailable:
            logger.warning(
                "review unavailable repo=%s pr=%d",
                request.repository,
                request.pr_number,
                exc_info=True,
            )
            if row is not None:
                store.fail_session(row, "review unavailable")
            raise
        except Exception as exc:  # noqa: BLE001 - persist the failure and re-raise
            logger.exception("review failed repo=%s pr=%d", request.repository, request.pr_number)
            if row is not None:
                try:
                    store.fail_session(row, str(exc)[:2000])
                except Exception:  # noqa: BLE001 - the original error is what matters
                    pass
            raise
        finally:
            db.close()

    def review_event(self, envelope: EventEnvelope) -> PRReview | None:
        """Dispatch a webhook event to a review run, if it is one."""
        if not settings.agent_review_enabled or not settings.agent_review_auto_run:
            return None
        if envelope.event_type == "pull_request":
            if envelope.event_action not in _PULL_REQUEST_ACTIONS:
                return None
            payload = envelope.payload.get("pull_request", {})
            repo = envelope.payload.get("repository", {}).get("full_name")
            number = payload.get("number")
            if not repo or not number:
                return None
            return self.submit(
                ReviewRequest(repository=repo, pr_number=int(number), source="webhook"),
                delivery_id=envelope.delivery_id,
                correlation_id=envelope.delivery_id,
            )
        if envelope.event_type == "workflow_run":
            if envelope.event_action != _WORKFLOW_ACTION:
                return None
            run = envelope.payload.get("workflow_run", {})
            repo = envelope.payload.get("repository", {}).get("full_name")
            branch = run.get("head_branch")
            if not repo or not branch:
                return None
            pr = self._provider_for(repo).find_pull_request_for_head(repo, branch)
            if pr is None:
                logger.info("no open PR for branch repo=%s branch=%s", repo, branch)
                return None
            return self.submit(
                ReviewRequest(
                    repository=repo,
                    pr_number=pr.number,
                    branch=branch,
                    source="webhook",
                ),
                delivery_id=envelope.delivery_id,
                correlation_id=envelope.delivery_id,
            )
        return None

    def status(self) -> ReviewStatus:
        db = self._session_factory()
        try:
            store = ReviewStore(db)
            status = store.status()
            status.enabled = settings.agent_review_enabled
            status.engine_version = settings.agent_review_engine_version
            return status
        finally:
            db.close()

    def get(self, session_id: int) -> dict | None:
        db = self._session_factory()
        try:
            store = ReviewStore(db)
            row = store.get(session_id)
            if row is None:
                return None
            return {
                "id": row.id,
                "delivery_id": row.delivery_id,
                "correlation_id": row.correlation_id,
                "repo_full_name": row.repo_full_name,
                "pr_number": row.pr_number,
                "branch": row.branch,
                "base_branch": row.base_branch,
                "commit_sha": row.commit_sha,
                "author": row.author,
                "title": row.title,
                "source": row.source,
                "status": row.status,
                "error": row.error,
                "findings_count": row.findings_count,
                "duration_ms": row.duration_ms,
                "metrics": row.metrics_json,
                "created_at": row.created_at.isoformat(),
                "updated_at": row.updated_at.isoformat(),
            }
        finally:
            db.close()

    def recent(self, limit: int = 10) -> list[dict]:
        db = self._session_factory()
        try:
            rows = ReviewStore(db).latest(limit)
            return [
                {
                    "id": row.id,
                    "repo_full_name": row.repo_full_name,
                    "pr_number": row.pr_number,
                    "title": row.title,
                    "status": row.status,
                    "findings_count": row.findings_count,
                    "created_at": row.created_at.isoformat(),
                }
                for row in rows
            ]
        finally:
            db.close()

    # ------------------------------------------------------------------
    def _provider_for(self, repo_full_name: str) -> PullRequestProvider:
        if self._injected_provider is not None:
            return self._injected_provider
        if repo_full_name == settings.agent_review_fixture_repo:
            return FixturePullRequestProvider()
        if not settings.github_configured:
            raise ReviewUnavailable("github app not configured for PR review")
        return GitHubPullRequestProvider(self._installation_token())

    def _installation_token(self) -> str:
        if self._token:
            return self._token
        from app.clients.github_app import request_installation_token_sync

        try:
            self._token = request_installation_token_sync(
                settings.agent_github_app_id,
                settings.github_private_key or "",
                settings.agent_github_installation_id,
            )
        except Exception as exc:  # noqa: BLE001 - surface as unavailable
            raise ReviewUnavailable(f"could not issue github installation token: {exc}") from exc
        return self._token
