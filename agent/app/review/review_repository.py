"""Persistence for PR review sessions, findings and evidence.

Mirrors the repository pattern from app/db/repositories.py: sessions are
injected, repositories never create connections, and business logic goes
through the ReviewStore facade.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import ReviewEvidenceRow, ReviewFindingRow, ReviewSession
from app.review.review_models import (
    FindingEvidence,
    PRReview,
    ReviewStatus,
)

_SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ReviewSessionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        repo_full_name: str,
        pr_number: int,
        *,
        source: str = "api",
        delivery_id: str | None = None,
        correlation_id: str | None = None,
    ) -> ReviewSession:
        row = ReviewSession(
            delivery_id=delivery_id,
            correlation_id=correlation_id,
            repo_full_name=repo_full_name,
            pr_number=pr_number,
            source=source,
            status="in_progress",
        )
        self._session.add(row)
        self._session.flush()
        return row

    def by_delivery(self, delivery_id: str) -> ReviewSession | None:
        return (
            self._session.execute(
                select(ReviewSession).where(ReviewSession.delivery_id == delivery_id)
            )
            .scalars()
            .first()
        )

    def get(self, session_id: int) -> ReviewSession | None:
        return self._session.get(ReviewSession, session_id)

    def update(
        self,
        row: ReviewSession,
        *,
        status: str | None = None,
        error: str | None = None,
        findings_count: int | None = None,
        duration_ms: int | None = None,
        metrics_json: str | None = None,
        title: str | None = None,
        branch: str | None = None,
        base_branch: str | None = None,
        commit_sha: str | None = None,
        author: str | None = None,
    ) -> None:
        if status is not None:
            row.status = status
        if error is not None:
            row.error = error
        if findings_count is not None:
            row.findings_count = findings_count
        if duration_ms is not None:
            row.duration_ms = duration_ms
        if metrics_json is not None:
            row.metrics_json = metrics_json
        if title is not None:
            row.title = title
        if branch is not None:
            row.branch = branch
        if base_branch is not None:
            row.base_branch = base_branch
        if commit_sha is not None:
            row.commit_sha = commit_sha
        if author is not None:
            row.author = author
        row.updated_at = _utcnow()
        self._session.flush()

    def latest(self, limit: int = 10) -> list[ReviewSession]:
        return list(
            self._session.execute(
                select(ReviewSession).order_by(ReviewSession.id.desc()).limit(limit)
            )
            .scalars()
            .all()
        )

    def counts(self) -> dict:
        rows = self._session.execute(
            select(ReviewSession.status, func.count(ReviewSession.id)).group_by(
                ReviewSession.status
            )
        ).all()
        counts = {status: int(count) for status, count in rows}
        avg = self._session.execute(
            select(func.avg(ReviewSession.duration_ms)).where(ReviewSession.status == "completed")
        ).scalar()
        return {
            "total": int(sum(counts.values())),
            "by_status": counts,
            "average_duration_ms": int(avg or 0),
        }

    def commit(self) -> None:
        self._session.commit()


class ReviewFindingRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_many(self, session_id: int, review: PRReview) -> None:
        for finding in review.findings:
            self._session.add(
                ReviewFindingRow(
                    session_id=session_id,
                    rule_id=finding.rule_id,
                    category=finding.category,
                    severity=finding.severity,
                    title=finding.title,
                    explanation=finding.explanation,
                    file_path=finding.file_path,
                    start_line=finding.start_line,
                    end_line=finding.end_line,
                    snippet=finding.snippet,
                    suggestion=finding.suggestion,
                    confidence=finding.confidence,
                    related_adrs_json=json.dumps(finding.related_adrs),
                    related_files_json=json.dumps(finding.related_files),
                )
            )

    def by_session(self, session_id: int) -> list[ReviewFindingRow]:
        return list(
            self._session.execute(
                select(ReviewFindingRow)
                .where(ReviewFindingRow.session_id == session_id)
                .order_by(ReviewFindingRow.id)
            )
            .scalars()
            .all()
        )

    def totals(self) -> tuple[dict, dict]:
        rows = self._session.execute(
            select(
                ReviewFindingRow.category,
                ReviewFindingRow.severity,
                func.count(ReviewFindingRow.id),
            ).group_by(ReviewFindingRow.category, ReviewFindingRow.severity)
        ).all()
        by_category: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        for category, severity, count in rows:
            by_category[category] = by_category.get(category, 0) + int(count)
            by_severity[severity] = by_severity.get(severity, 0) + int(count)
        return by_category, by_severity

    def delete_for_session(self, session_id: int) -> None:
        rows = (
            self._session.execute(
                select(ReviewFindingRow).where(ReviewFindingRow.session_id == session_id)
            )
            .scalars()
            .all()
        )
        for row in rows:
            self._session.delete(row)
        self._session.flush()


class ReviewEvidenceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_many(self, session_id: int, findings: list[tuple[int, list[FindingEvidence]]]) -> None:
        for finding_id, evidence in findings:
            for item in evidence:
                self._session.add(
                    ReviewEvidenceRow(
                        session_id=session_id,
                        finding_id=finding_id,
                        kind=item.kind,
                        reference=item.reference,
                        content=item.content,
                        confidence=item.confidence,
                    )
                )

    def by_session(self, session_id: int) -> list[ReviewEvidenceRow]:
        return list(
            self._session.execute(
                select(ReviewEvidenceRow).where(ReviewEvidenceRow.session_id == session_id)
            )
            .scalars()
            .all()
        )


class ReviewStore:
    """Facade persisting a full review run atomically."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._sessions = ReviewSessionRepository(session)
        self._findings = ReviewFindingRepository(session)
        self._evidence = ReviewEvidenceRepository(session)

    def start_session(
        self,
        repo_full_name: str,
        pr_number: int,
        *,
        source: str = "api",
        delivery_id: str | None = None,
        correlation_id: str | None = None,
    ) -> ReviewSession:
        if delivery_id:
            existing = self._sessions.by_delivery(delivery_id)
            if existing is not None:
                return existing
        return self._sessions.create(
            repo_full_name,
            pr_number,
            source=source,
            delivery_id=delivery_id,
            correlation_id=correlation_id,
        )

    def persist_review(self, row: ReviewSession, review: PRReview) -> ReviewSession:
        self._findings.delete_for_session(row.id)
        self._findings.add_many(row.id, review)
        self._session.flush()
        finding_rows = self._findings.by_session(row.id)
        evidence = [
            (finding_row.id, finding.evidence)
            for finding_row, finding in zip(finding_rows, review.findings)
        ]
        self._evidence.add_many(row.id, evidence)
        self._sessions.update(
            row,
            status="completed",
            findings_count=len(review.findings),
            duration_ms=review.metrics.duration_ms,
            metrics_json=review.metrics.model_dump_json(),
            title=review.title,
            branch=review.branch,
            base_branch=review.base_branch,
            commit_sha=review.commit_sha,
            author=review.author,
        )
        self._sessions.commit()
        return row

    def fail_session(self, row: ReviewSession, error: str) -> ReviewSession:
        self._sessions.update(row, status="failed", error=error)
        self._sessions.commit()
        return row

    def get(self, session_id: int) -> ReviewSession | None:
        return self._sessions.get(session_id)

    def latest(self, limit: int = 10) -> list[ReviewSession]:
        return self._sessions.latest(limit)

    def status(self) -> ReviewStatus:
        counts = self._sessions.counts()
        by_category, by_severity = self._findings.totals()
        return ReviewStatus(
            healthy=True,
            enabled=True,
            engine_version="2.0.0",
            total_sessions=counts["total"],
            pending=counts["by_status"].get("in_progress", 0),
            completed=counts["by_status"].get("completed", 0),
            failed=counts["by_status"].get("failed", 0),
            findings_total=sum(by_severity.values()),
            by_category=by_category,
            by_severity=by_severity,
            average_duration_ms=counts["average_duration_ms"],
        )

    def commit(self) -> None:
        self._session.commit()


def _severity_rank(severity: str) -> int:
    return _SEVERITY_ORDER.get(severity, 0)
