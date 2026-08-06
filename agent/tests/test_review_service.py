"""Tests for the ReviewService application service."""

from datetime import datetime, timezone

import pytest

from app.coordinator.event_handler import EventEnvelope
from app.review.pr_provider import FixturePullRequestProvider
from app.review.review_engine import ReviewEngine
from app.review.review_models import ReviewRequest, ReviewUnavailable
from app.review.review_service import ReviewService


@pytest.fixture
def service(noop_probe):
    provider = FixturePullRequestProvider()
    engine = ReviewEngine(noop_probe)
    return ReviewService(provider=provider, probe=noop_probe, engine=engine)


class _FailingProvider(FixturePullRequestProvider):
    def get_pull_request(self, repo_full_name, number):
        raise ReviewUnavailable("gone")


def _envelope(event_type="pull_request", action="opened", **payload) -> EventEnvelope:
    body = {
        "action": action,
        "repository": {"full_name": "waste-iq/demo"},
        "pull_request": {"number": 1},
        **payload,
    }
    return EventEnvelope(
        delivery_id="delivery-1",
        event_type=event_type,
        event_action=action,
        payload=body,
        received_at=datetime.now(timezone.utc),
    )


def test_submit_persists_and_returns_review(service, clean_review_db):
    review = service.submit(
        ReviewRequest(repository="waste-iq/demo", pr_number=1),
        delivery_id="delivery-1",
        correlation_id="corr-1",
    )
    assert review.session_id is not None
    assert review.summary.total > 0
    assert len(review.disclaimers) >= 1

    session = service.get(review.session_id)
    assert session is not None
    assert session["delivery_id"] == "delivery-1"
    assert session["correlation_id"] == "corr-1"
    assert session["status"] == "completed"
    assert session["findings_count"] == review.summary.total


def test_submit_duplicate_delivery_reuses_session(service, clean_review_db):
    first = service.submit(ReviewRequest(repository="waste-iq/demo", pr_number=1), delivery_id="d1")
    second = service.submit(
        ReviewRequest(repository="waste-iq/demo", pr_number=1), delivery_id="d1"
    )
    assert first.session_id == second.session_id


def test_submit_failure_marks_session_failed(noop_probe, clean_review_db):
    service = ReviewService(
        provider=_FailingProvider(), probe=noop_probe, engine=ReviewEngine(noop_probe)
    )
    with pytest.raises(ReviewUnavailable):
        service.submit(ReviewRequest(repository="waste-iq/demo", pr_number=1), delivery_id="f-1")
    sessions = service.recent(10)
    failed = [s for s in sessions if s["status"] == "failed"]
    assert len(failed) == 1
    assert failed[0]["repo_full_name"] == "waste-iq/demo"


def test_submit_disabled_raises(service, clean_review_db, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "agent_review_enabled", False)
    with pytest.raises(ReviewUnavailable):
        service.submit(ReviewRequest(repository="waste-iq/demo", pr_number=1))


def test_review_event_pull_request(service, clean_review_db):
    review = service.review_event(_envelope(action="opened"))
    assert review is not None
    assert review.pr_number == 1


def test_review_event_ignores_other_pull_request_actions(service, clean_review_db):
    assert service.review_event(_envelope(action="closed")) is None
    assert service.review_event(_envelope(action="edited")) is None


def test_review_event_requires_repo_and_number(service, clean_review_db):
    env = _envelope(action="opened")
    env.payload = {"action": "opened", "pull_request": {"number": 1}}
    assert service.review_event(env) is None


def test_review_event_workflow_run_completed(service, clean_review_db):
    env = _envelope(
        event_type="workflow_run",
        action="completed",
        workflow_run={"head_branch": "feature/demo-payments"},
    )
    review = service.review_event(env)
    assert review is not None
    assert review.branch == "feature/demo-payments"


def test_review_event_workflow_run_no_open_pr(service, clean_review_db):
    env = _envelope(
        event_type="workflow_run",
        action="completed",
        workflow_run={"head_branch": "unknown-branch"},
    )
    assert service.review_event(env) is None


def test_review_event_ignored_when_auto_run_off(service, clean_review_db, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "agent_review_auto_run", False)
    assert service.review_event(_envelope(action="opened")) is None


def test_review_event_rejects_non_review_events(service, clean_review_db):
    env = _envelope(event_type="issues", action="opened")
    assert service.review_event(env) is None
    env = _envelope(event_type="workflow_run", action="requested")
    assert service.review_event(env) is None


def test_status_reflects_enabled_and_engine(service, clean_review_db):
    status = service.status()
    assert status.enabled is True
    assert status.engine_version == "2.0.0"
    assert status.healthy is True


def test_get_unknown_session_returns_none(service, clean_review_db):
    assert service.get(999999) is None


def test_recent_empty(service, clean_review_db):
    assert service.recent(5) == []


def test_submit_generic_error_marks_session_failed(noop_probe, clean_review_db):
    class _BoomProvider(FixturePullRequestProvider):
        def get_pull_request(self, repo_full_name, number):
            raise ValueError("internal explosion")

    service = ReviewService(
        provider=_BoomProvider(), probe=noop_probe, engine=ReviewEngine(noop_probe)
    )
    with pytest.raises(ValueError):
        service.submit(ReviewRequest(repository="waste-iq/demo", pr_number=1), delivery_id="boom")
    sessions = service.recent(10)
    failed = [s for s in sessions if s["status"] == "failed"]
    assert len(failed) == 1
    detail = service.get(failed[0]["id"])
    assert "explosion" in detail["error"]


def test_review_event_ignores_missing_pr_number(service, clean_review_db):
    env = _envelope(action="opened")
    env.payload = {
        "action": "opened",
        "repository": {"full_name": "waste-iq/demo"},
        "pull_request": {},
    }
    assert service.review_event(env) is None


def test_review_event_ignores_missing_workflow_branch(service, clean_review_db):
    env = _envelope(event_type="workflow_run", action="completed", workflow_run={})
    assert service.review_event(env) is None


def test_provider_for_requires_github_config(noop_probe, monkeypatch):
    from app.core.config import settings
    from app.review.review_models import ReviewUnavailable

    monkeypatch.setattr(settings.__class__, "github_configured", False)
    service = ReviewService(probe=noop_probe, engine=ReviewEngine(noop_probe))
    with pytest.raises(ReviewUnavailable, match="not configured"):
        service._provider_for("other/org")


def test_installation_token_issued_and_cached(noop_probe, monkeypatch):
    from app.clients import github_app
    from app.review.review_service import ReviewService

    issued = {"count": 0}

    def fake_token(app_id, private_key, installation_id):
        issued["count"] += 1
        return "inst-token-9"

    monkeypatch.setattr(github_app, "request_installation_token_sync", fake_token)
    service = ReviewService(probe=noop_probe, engine=ReviewEngine(noop_probe))
    provider = service._provider_for("other/org")
    from app.review.pr_provider import GitHubPullRequestProvider

    assert isinstance(provider, GitHubPullRequestProvider)
    assert issued["count"] == 1
    assert service._installation_token() == "inst-token-9"
    assert issued["count"] == 1


def test_installation_token_failure_raises_unavailable(noop_probe, monkeypatch):
    from app.clients import github_app
    from app.review.review_models import ReviewUnavailable
    from app.review.review_service import ReviewService

    def failing_token(app_id, private_key, installation_id):
        raise RuntimeError("no network")

    monkeypatch.setattr(github_app, "request_installation_token_sync", failing_token)
    service = ReviewService(probe=noop_probe, engine=ReviewEngine(noop_probe))
    with pytest.raises(ReviewUnavailable, match="installation token"):
        service._provider_for("other/org")
