"""Integration tests for the chat orchestrator against real services (Phase 5)."""

import base64

import pytest
import respx
from httpx import Response

from app.chat.models import ChatNoEvidenceError, ChatReference
from app.chat.orchestrator import (
    ChatOrchestrator,
    _parse_issue_subject,
    _parse_pr_number,
    _parse_repository,
)
from app.context.di import Container
from app.core.config import settings
from app.llm.models import GroundingViolationError
from app.llm.service import LLMService
from app.review.review_models import ReviewRequest
from app.review.review_service import ReviewService

AUTH_ROUTE = """\
from fastapi import APIRouter

router = APIRouter(prefix="/api/auth")


@router.post("/login")
async def login(username: str, password: str):
    return {"ok": True}
"""

ROADMAP_DOC = """# Waste-IQ V1 Roadmap

## Milestone M0

Developer chat assistant: grounded answers from repository evidence.
"""

ADR_DOC = """# ADR-001 Dealer approval is propose-only

The dealer approval flow must never directly modify the ledger.
"""


@pytest.fixture
def container(tmp_path, clean_context_db):
    from app.db.session import SessionLocal

    (tmp_path / "backend" / "app" / "api" / "routes").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "architecture").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "backend" / "app" / "api" / "routes" / "auth.py").write_text(
        AUTH_ROUTE, encoding="utf-8"
    )
    (tmp_path / "docs" / "architecture" / "ADR-001.md").write_text(ADR_DOC, encoding="utf-8")
    (tmp_path / "docs" / "roadmap.md").write_text(ROADMAP_DOC, encoding="utf-8")
    container = Container(
        SessionLocal,
        repository_root=tmp_path,
        min_tokens=50,
        max_tokens=500,
    )
    container.pipeline().run()
    return container


@pytest.fixture
def empty_container(tmp_path, clean_context_db):
    from app.db.session import SessionLocal

    return Container(SessionLocal, repository_root=tmp_path, min_tokens=10, max_tokens=100)


def _orchestrator(container, **kwargs) -> ChatOrchestrator:
    return ChatOrchestrator(container, LLMService(), **kwargs)


class _RecordingReviewService(ReviewService):
    """ReviewService that records each submit request and provider selection."""

    def __init__(self, container):
        super().__init__(container=container)
        self.requests: list[ReviewRequest] = []
        self.providers: list[tuple[str, str]] = []

    def _provider_for(self, repo_full_name: str):
        provider = super()._provider_for(repo_full_name)
        self.providers.append((repo_full_name, provider.__class__.__name__))
        return provider

    def submit(self, request, *, delivery_id=None, correlation_id=None):
        self.requests.append(request)
        return super().submit(request, delivery_id=delivery_id, correlation_id=correlation_id)


def _recording_orchestrator(container):
    service = _RecordingReviewService(container)
    return _orchestrator(container, review_service=service), service


def test_explain_code_returns_grounded_answer(container):
    outcome = _orchestrator(container).handle("Explain the login route")
    assert outcome.intent == "explain_code"
    assert outcome.grounded
    assert outcome.references
    assert all(isinstance(ref, ChatReference) for ref in outcome.references)
    assert "auth.py" in " ".join(ref.file_path for ref in outcome.references)
    assert outcome.provider == "mock"
    assert outcome.latency_ms >= 0


def test_explain_architecture_grounds_on_adr_and_roadmap(container):
    outcome = _orchestrator(container).handle("Explain the dealer approval workflow")
    assert outcome.intent == "explain_architecture"
    assert outcome.grounded
    assert "ADR-001.md" in " ".join(ref.file_path for ref in outcome.references)


def test_find_implementation_returns_code_references(container):
    outcome = _orchestrator(container).handle("Where is the login route?")
    assert outcome.intent == "find_implementation"
    assert outcome.grounded
    assert any(ref.file_path.endswith("auth.py") for ref in outcome.references)


def test_summarize_returns_grounded_answer(container):
    outcome = _orchestrator(container).handle("Summarize the login route")
    assert outcome.intent == "summarize_changes"
    assert outcome.grounded
    assert outcome.answer
    assert "key point" in outcome.answer


def test_generate_issue_returns_triage_with_evidence(container):
    outcome = _orchestrator(container).handle("Generate an issue draft for the login failure")
    assert outcome.intent == "generate_issue"
    assert outcome.grounded
    assert "Triage" in outcome.answer
    assert outcome.references


def test_generate_documentation_returns_proposal_with_references(container):
    outcome = _orchestrator(container).handle("Generate documentation for the login route")
    assert outcome.intent == "generate_documentation"
    assert outcome.references
    assert outcome.answer


def test_generate_documentation_appends_changelog_entry(container):
    from app.agents.doc_agent import DocProposal

    class FakeDocAssistant:
        def analyze(self, pr_dict, changed_files=None, pr_body=None):
            return DocProposal(
                pr_number=7,
                pr_title="feat: login",
                changelog_section="Added",
                changelog_entry="Login route exposed",
                summary="Doc proposal summary",
            )

    outcome = _orchestrator(container, doc_assistant=FakeDocAssistant()).handle(
        "Generate documentation for the login route"
    )
    assert "Changelog (Added): Login route exposed" in outcome.answer


def test_review_pr_runs_review_agent(container):
    outcome = _orchestrator(container).handle("Review PR #1")
    assert outcome.intent == "review_pr"
    assert outcome.grounded
    assert "Findings:" in outcome.answer
    assert outcome.references


def test_unknown_question_returns_help_without_evidence(container):
    outcome = _orchestrator(container).handle("hello there, nice day?")
    assert outcome.intent == "unknown"
    assert not outcome.grounded
    assert not outcome.references
    assert "Try:" in outcome.answer


def test_no_evidence_raises_for_issue_intent(empty_container):
    with pytest.raises(ChatNoEvidenceError):
        _orchestrator(empty_container).handle("Generate an issue draft for the login failure")


def test_llm_grounding_violation_propagates(empty_container):
    with pytest.raises(GroundingViolationError):
        _orchestrator(empty_container).handle("Explain the login route")


def test_followup_reuses_previous_search_query(container):
    orch = _orchestrator(container)
    first = orch.handle("Where is the login route?")
    followup = orch.handle("what does it do?", previous_turns=[first])  # type: ignore[arg-type]
    assert followup.search_query == first.search_query
    assert followup.grounded


def test_custom_planner_dispatch_fallback(container):
    class BogusPlan:
        intent = "explain_code"
        search_query = "login"
        limit = 6
        source_types = ["code"]
        agent = "unsupported_agent"
        requires_evidence = False
        description = "bogus"
        notes = []

    def planner(detected, question, previous_turn):
        return BogusPlan()

    outcome = _orchestrator(container, planner=planner).handle("Explain the login route")
    assert "unsupported" in outcome.answer


def test_parse_pr_number_variants():
    assert _parse_pr_number("Review PR #12") == 12
    assert _parse_pr_number("review pr 7") == 7
    assert _parse_pr_number("no number here") == 1


def test_parse_issue_subject_strips_lead():
    number, subject = _parse_issue_subject("Generate an issue draft for the login failure")
    assert number == 0
    assert subject == "the login failure"


def test_parse_issue_subject_with_number():
    number, subject = _parse_issue_subject("Triage issue #42 the login failure")
    assert number == 42


def test_review_pr_fallback_number_when_missing(container):
    outcome = _orchestrator(container).handle("review this pull request")
    assert outcome.intent == "review_pr"
    assert "Findings:" in outcome.answer


def test_parse_pr_number_with_repository():
    assert _parse_pr_number("Review PR #69 for Subhajitdas99/waste-iq") == 69
    assert _parse_pr_number("Review Subhajitdas99/waste-iq#69") == 69
    assert _parse_pr_number("Review PR #1 for waste-iq/demo") == 1


def test_parse_repository_variants():
    assert _parse_repository("Review PR #69 for Subhajitdas99/waste-iq") == "Subhajitdas99/waste-iq"
    assert (
        _parse_repository("Review PR #69 for Subhajitdas99/waste-iq.") == "Subhajitdas99/waste-iq"
    )
    assert _parse_repository("Review PR #1 for waste-iq/demo") == "waste-iq/demo"
    assert _parse_repository("Review PR #12 in octo-org/octo_repo") == "octo-org/octo_repo"
    assert _parse_repository("Review Subhajitdas99/waste-iq#69") == "Subhajitdas99/waste-iq"
    assert _parse_repository("Review PR #1") is None
    assert _parse_repository("review this pull request") is None


@respx.mock
def test_review_of_real_repo_uses_github_provider_and_token(
    container, clean_review_db, monkeypatch
):
    """Chat review of a real repository runs through GitHubPullRequestProvider.

    'Review PR #69 for Subhajitdas99/waste-iq' must keep the full repository
    name and PR number 69, select the GitHub provider, and authenticate with a
    fresh installation token — not the fixture provider.
    """
    from app.clients import github_app

    _API = "https://api.github.test"

    monkeypatch.setattr(
        github_app, "request_installation_token_sync", lambda *args: "inst-token-chat"
    )
    monkeypatch.setattr(settings, "agent_github_api_base_url", _API)

    diff = "diff --git a/a.py b/a.py\n@@ -0,0 +1,1 @@\n+x\n"
    respx.get(
        f"{_API}/repos/Subhajitdas99/waste-iq/pulls/69",
        headers={"Accept": "application/vnd.github.v3.diff"},
    ).mock(return_value=Response(200, text=diff))
    respx.get(
        f"{_API}/repos/Subhajitdas99/waste-iq/pulls/69",
        headers={"Accept": "application/vnd.github+json"},
    ).mock(
        return_value=Response(
            200,
            json={
                "number": 69,
                "title": "Add grounded engineering CLI",
                "state": "open",
                "user": {"login": "alice"},
                "head": {"ref": "feature/cli", "sha": "sha-69"},
                "base": {"ref": "develop"},
            },
        )
    )
    respx.get(f"{_API}/repos/Subhajitdas99/waste-iq/pulls/69/files", params={"per_page": 100}).mock(
        return_value=Response(200, json=[])
    )
    respx.get(f"{_API}/repos/Subhajitdas99/waste-iq/contents/a.py", params={"ref": "sha-69"}).mock(
        return_value=Response(
            200,
            json={
                "encoding": "base64",
                "content": base64.b64encode(b"x\n").decode("ascii"),
            },
        )
    )

    orch, service = _recording_orchestrator(container)
    outcome = orch.handle("Review PR #69 for Subhajitdas99/waste-iq")

    assert outcome.intent == "review_pr"
    assert outcome.grounded
    assert outcome.answer
    assert service.requests == [
        ReviewRequest(repository="Subhajitdas99/waste-iq", pr_number=69, source="chat")
    ]
    assert ("Subhajitdas99/waste-iq", "GitHubPullRequestProvider") in service.providers
    assert ("waste-iq/demo", "FixturePullRequestProvider") not in service.providers
    for call in respx.calls:
        if "/repos/Subhajitdas99/waste-iq/pulls/69" in str(call.request.url):
            assert call.request.headers["Authorization"] == "Bearer inst-token-chat"


def test_review_of_configured_fixture_repo_uses_fixture_provider(
    container, clean_review_db, monkeypatch
):
    monkeypatch.setattr(settings, "agent_review_fixture_repo", "demo-owner/demo-repo")
    orch, service = _recording_orchestrator(container)
    outcome = orch.handle("Review PR #1 for demo-owner/demo-repo")
    assert outcome.intent == "review_pr"
    assert outcome.grounded
    assert "Findings:" in outcome.answer
    assert service.requests == [
        ReviewRequest(repository="demo-owner/demo-repo", pr_number=1, source="chat")
    ]
    assert ("demo-owner/demo-repo", "FixturePullRequestProvider") in service.providers


def test_review_without_repository_still_uses_fixture_provider(container, clean_review_db):
    orch, service = _recording_orchestrator(container)
    outcome = orch.handle("Review PR #1")
    assert outcome.intent == "review_pr"
    assert outcome.grounded
    assert service.requests == [
        ReviewRequest(repository=settings.agent_review_fixture_repo, pr_number=1, source="chat")
    ]
    assert (settings.agent_review_fixture_repo, "FixturePullRequestProvider") in service.providers
