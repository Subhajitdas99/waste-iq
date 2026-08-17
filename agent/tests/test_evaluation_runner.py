"""Tests for the benchmark runner and /api/evaluation/status endpoint."""

from types import SimpleNamespace

from app.evaluation.runner import (
    BenchmarkRunner,
    _handle_architecture,
    _handle_documentation,
    _handle_review,
    _issue_behaviour_met,
)
from app.evaluation.schema import BenchmarkCase


class _FakeStore:
    def __init__(self, paths=()):
        self._paths = list(paths)

    def indexed_files(self):
        return list(self._paths)


class _FakeSearchService:
    def __init__(self, *responses):
        self._responses = list(responses)
        self._call = 0

    def hybrid_search(self, request):
        results = self._responses[min(self._call, len(self._responses) - 1)]
        self._call += 1
        return _FakeResponse(results)


class _FakeResponse:
    def __init__(self, results):
        self.results = results


class _FakeContainer:
    repository_root = "."

    def __init__(self, search=None, indexed=()):
        self._search = search or _FakeSearchService([])
        self._store = _FakeStore(indexed)

    def search_service(self):
        return self._search

    def store(self):
        return self._store


class _FakeRunner:
    def __init__(self, container):
        self._container = container

    @property
    def container(self):
        return self._container


def _make_case(**overrides) -> BenchmarkCase:
    values = dict(id="t", category="repository_search", question="q", expected_behaviour="b")
    values.update(overrides)
    return BenchmarkCase(**values)


def _runner_cases() -> list[BenchmarkCase]:
    return [
        BenchmarkCase(
            id="rs-test-find-calculator",
            category="repository_search",
            question="Find Calculator",
            expected_behaviour="find src/utils.py",
            expected_files=["src/utils.py"],
            payload={"search_query": "Calculator multiply"},
        ),
        BenchmarkCase(
            id="ia-test-bug-triage",
            category="issue_assistant",
            question="Triage a bug",
            expected_behaviour="priority high, bug label",
            expected_files=[],
            payload={
                "issue": {"number": 1, "title": "App crashes on login", "body": "Exception thrown"},
                "repo_labels": ["bug", "backend"],
            },
        ),
        BenchmarkCase(
            id="ll-test-grounding",
            category="llm_layer",
            question="Grounding validation",
            expected_behaviour="grounded response accepted",
            expected_files=[],
            payload={"check": "grounding_validation"},
        ),
        BenchmarkCase(
            id="ia-test-manual",
            category="issue_assistant",
            mode="manual",
            question="Acceptance criteria",
            expected_behaviour="manual",
            expected_files=[],
        ),
    ]


def test_runner_executes_and_scores_all_cases(clean_context_db):
    from app.context.di import Container
    from app.db.session import SessionLocal

    container = Container(SessionLocal)
    container.pipeline().run()
    report = BenchmarkRunner(container, cases=_runner_cases()).run()

    assert len(report.cases) == 4
    executed = [c for c in report.cases if c.result.status == "executed"]
    assert len(executed) == 3
    manual = [c for c in report.cases if c.result.status == "manual"]
    assert len(manual) == 1

    search = report.case("rs-test-find-calculator")
    assert search is not None
    assert search.result.cited_files and "src/utils.py" in search.result.cited_files
    assert search.repository_accuracy == 10.0
    assert search.passed

    issue = report.case("ia-test-bug-triage")
    assert issue is not None
    assert issue.result.status == "executed"
    assert "priority" in issue.result.notes

    llm = report.case("ll-test-grounding")
    assert llm is not None
    assert llm.grounding == 10.0
    assert llm.result.evidence_grounded is True

    assert report.gates.hallucinations_zero is True
    assert report.cases[0].case.id == "rs-test-find-calculator"


def test_runner_failed_case_never_crashes_run(clean_context_db):
    broken = BenchmarkCase(
        id="x-broken",
        category="llm_layer",
        question="q",
        expected_behaviour="b",
        payload={"check": "does-not-exist"},
    )
    report = BenchmarkRunner(cases=[broken]).run()
    assert report.cases[0].result.status == "skipped"


def test_runner_search_never_hallucinates(clean_context_db):
    from app.context.di import Container
    from app.db.session import SessionLocal

    container = Container(SessionLocal)
    container.pipeline().run()
    report = BenchmarkRunner(container, cases=_runner_cases()).run()
    assert report.hallucinations == 0


def test_status_endpoint_never_run(client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        "app.api.routes.evaluation.settings.agent_evaluation_state_path",
        str(tmp_path / "state.json"),
    )
    response = client.get("/api/evaluation/status")
    assert response.status_code == 200
    data = response.json()
    assert data["last_run"] is None
    assert data["overall_score"] is None
    assert data["gates"] is None


def test_status_endpoint_after_run(client, monkeypatch, tmp_path):
    from app.evaluation.report import save_state
    from app.evaluation.schema import (
        CategorySummary,
        EvaluationReport,
        QualityGates,
    )

    path = tmp_path / "state.json"
    report = EvaluationReport(
        benchmark_version="1.0.0",
        run_id="run-1",
        ran_at="2026-08-06T12:00:00",
        cases=[],
        categories=[CategorySummary(category="llm_layer", cases=1, executed=1, average=99.0)],
        overall_score=99.0,
        hallucinations=0,
        gates=QualityGates(overall_ge_90=True),
    )
    save_state(report, path)
    monkeypatch.setattr("app.api.routes.evaluation.settings.agent_evaluation_state_path", str(path))

    response = client.get("/api/evaluation/status")
    assert response.status_code == 200
    data = response.json()
    assert data["last_run"] == "2026-08-06T12:00:00"
    assert data["overall_score"] == 99.0
    assert data["failures"] == 0
    assert data["weakest_category"] == "llm_layer"
    assert data["strongest_category"] == "llm_layer"


def test_runner_skips_case_without_handler(monkeypatch):
    from app.evaluation import runner as runner_module

    monkeypatch.setattr(runner_module, "_HANDLERS", {})
    case = _make_case(category="repository_search")
    report = BenchmarkRunner(_FakeContainer(), cases=[case]).run()
    assert report.cases[0].result.status == "skipped"
    assert report.cases[0].result.notes == "no handler"


def test_runner_records_handler_exception(monkeypatch):
    from app.evaluation import runner as runner_module

    def _boom(runner, case, indexed):
        raise RuntimeError("boom")

    monkeypatch.setattr(runner_module, "_HANDLERS", {"llm_layer": _boom})
    case = _make_case(category="llm_layer")
    report = BenchmarkRunner(_FakeContainer(), cases=[case]).run()
    assert report.cases[0].result.status == "failed"
    assert "RuntimeError" in report.cases[0].result.notes


def _triage(**overrides):
    values = dict(
        priority="high",
        evidence=[SimpleNamespace(path="src/app.py")],
        suggested_labels=["bug"],
        duplicate_of=[],
        milestone=None,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def test_issue_behaviour_ia01_draft_with_repo_labels():
    payload = {
        "issue": {"number": 1, "title": "t", "body": "b"},
        "repo_labels": ["bug", "backend"],
    }
    case = _make_case(id="ia-01-generate-issue-draft", category="issue_assistant", payload=payload)
    assert _issue_behaviour_met(case, _triage(), payload) is True
    assert _issue_behaviour_met(case, _triage(suggested_labels=["unrelated"]), payload) is False


def test_issue_behaviour_ia01_draft_without_repo_labels():
    payload = {"issue": {"number": 1, "title": "t", "body": "b"}}
    case = _make_case(id="ia-01-generate-issue-draft", category="issue_assistant", payload=payload)
    assert _issue_behaviour_met(case, _triage(), payload) is True


def test_issue_behaviour_ia02_duplicate_detection():
    payload = {"issue": {"number": 2, "title": "t", "body": "b"}}
    case = _make_case(id="ia-02-duplicate-detection", category="issue_assistant", payload=payload)
    assert _issue_behaviour_met(case, _triage(duplicate_of=[9003]), payload) is True


def test_issue_behaviour_ia03_labels_within_repo():
    payload = {
        "issue": {"number": 3, "title": "t", "body": "b"},
        "repo_labels": ["bug", "security"],
    }
    case = _make_case(id="ia-03-label-suggestions", category="issue_assistant", payload=payload)
    assert _issue_behaviour_met(case, _triage(), payload) is True


def test_issue_behaviour_ia04_milestone_suggestion():
    payload = {"issue": {"number": 4, "title": "t", "body": "b"}}
    case = _make_case(id="ia-04-milestone-suggestions", category="issue_assistant", payload=payload)
    assert _issue_behaviour_met(case, _triage(milestone="M0"), payload) is True


def test_architecture_handler_annotates_adrs_from_decision_file():
    adr = SimpleNamespace(
        path="docs/architecture/ARCHITECTURE_DECISIONS.md",
        section_title="ADR-004: AI assistance is propose-only",
    )
    other = SimpleNamespace(path="README.md", section_title="Intro")
    search = _FakeSearchService(
        [SimpleNamespace(path="docs/architecture/ARCHITECTURE_DECISIONS.md")],
        [adr, other],
    )
    indexed = {"docs/architecture/ARCHITECTURE_DECISIONS.md"}
    case = _make_case(
        id="ar-test",
        category="architecture",
        expected_adrs=["ADR-004"],
        payload={"search_query": "ADR-004 propose-only"},
    )
    result = _handle_architecture(
        _FakeRunner(_FakeContainer(search=search, indexed=indexed)), case, indexed
    )
    assert result.cited_adrs == ["ADR-004"]
    assert "ADR-004" in result.actual_answer


def test_documentation_handler_generates_changelog():
    case = _make_case(
        id="dc-01-generate-changelog",
        category="documentation",
        payload={"pr_title": "feat(api): add notifications endpoint", "pr_number": 42},
    )
    result = _handle_documentation(_FakeRunner(_FakeContainer()), case, set())
    assert result.evidence_grounded is True
    assert "section=" in result.actual_answer


def test_documentation_handler_proposes_doc_updates():
    case = _make_case(
        id="dc-02-summarize-pull-request",
        category="documentation",
        payload={
            "pr_title": "feat(api): add notifications endpoint",
            "pr_number": 42,
            "changed_files": ["backend/app/api/routes/notifications.py"],
        },
    )
    result = _handle_documentation(_FakeRunner(_FakeContainer()), case, set())
    assert "proposal for PR #42" in result.actual_answer


def test_documentation_handler_explain_module_delegates_to_search():
    search = _FakeSearchService([SimpleNamespace(path="backend/app/services/notifications.py")])
    case = _make_case(
        id="dc-03-explain-module",
        category="documentation",
        payload={"search_query": "notification service"},
    )
    result = _handle_documentation(_FakeRunner(_FakeContainer(search=search)), case, set())
    assert "notifications.py" in result.actual_answer


def test_review_handler_runs_fixture_pr_against_engine():
    case = _make_case(
        id="pr-test",
        category="pr_review",
        payload={"repository": "waste-iq/demo", "pr_number": 1},
    )
    result = _handle_review(_FakeRunner(_FakeContainer()), case, set())
    assert result.case_id == "pr-test"
    assert "findings=" in result.notes
