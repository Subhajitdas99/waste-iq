"""Tests for the ReviewAgent orchestration layer."""

import pytest

from app.review.pr_provider import FixturePullRequestProvider
from app.review.review_agent import ReviewAgent
from app.review.review_engine import ReviewEngine
from app.review.review_models import (
    PullRequestData,
    ReviewRequest,
    ReviewUnavailable,
)


class _NoFilesProvider(FixturePullRequestProvider):
    def get_pull_request(self, repo_full_name, number):
        pr = super().get_pull_request(repo_full_name, number)
        pr.files = []
        return pr


class _DiffOnlyProvider(FixturePullRequestProvider):
    """Provider that returns metadata + raw diff but no parsed files."""

    def __init__(self):
        self.called = 0

    def get_pull_request(self, repo_full_name, number):
        self.called += 1
        from app.review.fixtures import demo_patch

        return PullRequestData(
            number=number,
            repo_full_name=repo_full_name,
            title="demo",
            branch="feature/demo-payments",
            base_branch="main",
            commit_sha="abc123",
            author="demo",
            state="open",
            diff=demo_patch(),
            files=[],
        )


@pytest.fixture
def agent(noop_probe):
    return ReviewAgent(FixturePullRequestProvider(), noop_probe, ReviewEngine(noop_probe))


def test_review_returns_complete_review_object(agent):
    review = agent.review(ReviewRequest(repository="waste-iq/demo", pr_number=1))
    assert review.repo_full_name == "waste-iq/demo"
    assert review.pr_number == 1
    assert review.engine_version == "2.0.0"
    assert review.summary.total == len(review.findings) > 0
    assert review.summary.counts_by_category
    assert review.metrics.files_analyzed >= 3
    assert review.generated_at
    assert review.disclaimers
    assert review.session_id is None


def test_review_attaches_pr_metadata(agent):
    review = agent.review(ReviewRequest(repository="waste-iq/demo", pr_number=1))
    assert review.branch == "feature/demo-payments"
    assert review.base_branch
    assert review.commit_sha
    assert review.author
    assert review.title


def test_fetch_parses_diff_when_files_missing(noop_probe):
    provider = _DiffOnlyProvider()
    agent = ReviewAgent(provider, noop_probe, ReviewEngine(noop_probe))
    pr = agent.fetch(ReviewRequest(repository="waste-iq/demo", pr_number=1))
    assert pr.files
    assert any("payments.py" in f.path for f in pr.files)


def test_fetch_raises_when_no_files(noop_probe):
    agent = ReviewAgent(_NoFilesProvider(), noop_probe, ReviewEngine(noop_probe))
    with pytest.raises(ReviewUnavailable):
        agent.fetch(ReviewRequest(repository="waste-iq/demo", pr_number=1))


def test_review_raises_when_pr_missing(agent):
    with pytest.raises(ReviewUnavailable):
        agent.review(ReviewRequest(repository="waste-iq/demo", pr_number=99))


def test_find_for_head_matches_fixture_branch(agent):
    pr = agent.find_for_head("waste-iq/demo", "feature/demo-payments")
    assert pr is not None
    assert pr.number == 1


def test_find_for_head_returns_none_for_unknown_branch(agent):
    assert agent.find_for_head("waste-iq/demo", "not-a-branch") is None


class _ErrorProvider:
    def find_pull_request_for_head(self, repo_full_name, head_branch):
        raise ReviewUnavailable("nope")


def test_find_for_head_surfaces_unavailable_as_none(noop_probe):
    agent = ReviewAgent(_ErrorProvider(), noop_probe)
    assert agent.find_for_head("waste-iq/demo", "x") is None
