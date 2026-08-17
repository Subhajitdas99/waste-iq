"""Review agent — orchestrates PR fetch, rule engine and context probe."""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.config import settings
from app.review.diff import parse_patch
from app.review.pr_provider import PullRequestProvider
from app.review.review_context import RepositoryProbe
from app.review.review_engine import ReviewEngine
from app.review.review_models import (
    PRReview,
    PullRequestData,
    ReviewRequest,
    ReviewSummary,
    ReviewUnavailable,
)


class ReviewAgent:
    """Turns a ReviewRequest into an evidence-backed PRReview object.

    Purely read-only: fetches PR data, analyzes it, and returns findings.
    It never writes to GitHub or to the review DB (the service persists).
    """

    def __init__(
        self,
        provider: PullRequestProvider,
        probe: RepositoryProbe,
        engine: ReviewEngine | None = None,
    ) -> None:
        self._provider = provider
        self._probe = probe
        self._engine = engine or ReviewEngine(probe)

    def fetch(self, request: ReviewRequest) -> PullRequestData:
        pr = self._provider.get_pull_request(request.repository, request.pr_number)
        if not pr.files and pr.diff:
            pr.files = parse_patch(pr.diff)
        if not pr.files:
            raise ReviewUnavailable(
                f"no changed files available for {request.repository}#{request.pr_number}"
            )
        return pr

    def review(self, request: ReviewRequest) -> PRReview:
        pr = self.fetch(request)
        findings, repository_context, metrics = self._engine.review(pr, request.repository)
        return PRReview(
            engine_version=settings.agent_review_engine_version,
            repo_full_name=request.repository,
            pr_number=request.pr_number,
            branch=pr.branch,
            base_branch=pr.base_branch,
            commit_sha=pr.commit_sha,
            title=pr.title,
            author=pr.author,
            source=request.source,
            summary=ReviewSummary.build(findings),
            findings=findings,
            repository_context=repository_context,
            metrics=metrics,
            generated_at=_now_iso(),
        )

    def find_for_head(self, repo_full_name: str, head_branch: str) -> PullRequestData | None:
        try:
            return self._provider.find_pull_request_for_head(repo_full_name, head_branch)
        except ReviewUnavailable:
            return None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
