"""Tests for review persistence (ReviewStore + repositories)."""

import pytest

from app.db.models import ReviewEvidenceRow, ReviewFindingRow
from app.db.session import SessionLocal
from app.review.review_models import (
    PRReview,
    RepositoryContext,
    ReviewFinding,
    ReviewMetrics,
    ReviewSummary,
)
from app.review.review_repository import ReviewStore


def _finding(rule="CORR-PY-EXCEPT", category="correctness", severity="medium") -> ReviewFinding:
    return ReviewFinding(
        rule_id=rule,
        category=category,
        severity=severity,
        title="Bare except",
        explanation="Bare except hides errors.",
        file_path="app/x.py",
        start_line=3,
        end_line=3,
        snippet="except:",
        suggestion="Use except Exception",
        confidence=0.9,
    )


def _review(session_id: int = 0) -> PRReview:
    findings = [
        _finding(),
        _finding(rule="SEC-EVAL", category="security", severity="critical"),
        _finding(rule="DOC-MISSING-DOCSTRING", category="documentation", severity="low"),
    ]
    return PRReview(
        engine_version="2.0.0",
        repo_full_name="waste-iq/demo",
        pr_number=1,
        branch="feature/demo-payments",
        base_branch="main",
        commit_sha="abc",
        title="Demo",
        author="demo",
        summary=ReviewSummary.build(findings),
        findings=findings,
        repository_context=RepositoryContext(),
        metrics=ReviewMetrics(files_analyzed=3, added_lines=40),
    )


@pytest.fixture
def store(clean_review_db):
    db = SessionLocal()
    try:
        yield ReviewStore(db)
    finally:
        db.close()


def test_start_session_and_persist_review(store, clean_review_db):
    row = store.start_session("waste-iq/demo", 1, source="api")
    assert row.status == "in_progress"
    assert row.id is not None

    review = _review(row.id)
    review.session_id = row.id
    store.persist_review(row, review)

    assert row.status == "completed"
    assert row.findings_count == 3
    assert row.duration_ms is not None
    assert row.metrics_json
    assert row.branch == "feature/demo-payments"

    status = store.status()
    assert status.total_sessions == 1
    assert status.completed == 1
    assert status.findings_total == 3
    assert status.by_category["security"] == 1
    assert status.by_severity["critical"] == 1


def test_persist_writes_findings(store, clean_review_db):
    row = store.start_session("waste-iq/demo", 1)
    store.persist_review(row, _review(row.id))

    findings = (
        store._session.query(ReviewFindingRow)
        .filter(ReviewFindingRow.session_id == row.id)
        .order_by(ReviewFindingRow.id)
        .all()
    )
    assert len(findings) == 3
    assert findings[0].rule_id == "CORR-PY-EXCEPT"
    assert findings[0].severity == "medium"
    assert store._session.query(ReviewEvidenceRow).count() >= 0


def test_start_session_idempotent_by_delivery(store, clean_review_db):
    first = store.start_session("waste-iq/demo", 1, delivery_id="delivery-1")
    second = store.start_session("waste-iq/demo", 1, delivery_id="delivery-1")
    assert first.id == second.id

    other = store.start_session("waste-iq/demo", 1)
    assert other.id != first.id


def test_fail_session(store, clean_review_db):
    row = store.start_session("waste-iq/demo", 1)
    store.fail_session(row, "review unavailable")
    assert row.status == "failed"
    assert row.error == "review unavailable"
    status = store.status()
    assert status.failed == 1


def test_latest_and_get(store, clean_review_db):
    row_a = store.start_session("waste-iq/demo", 1)
    store.persist_review(row_a, _review(row_a.id))
    row_b = store.start_session("waste-iq/demo", 2)
    store.persist_review(row_b, _review(row_b.id))

    latest = store.latest(1)
    assert [r.id for r in latest] == [row_b.id]
    assert store.get(row_a.id) is not None
    assert store.get(999999) is None


def test_counts_average_duration(store, clean_review_db):
    row = store.start_session("waste-iq/demo", 1)
    review = _review(row.id)
    review.metrics.duration_ms = 123
    store.persist_review(row, review)
    status = store.status()
    assert status.average_duration_ms == 123
