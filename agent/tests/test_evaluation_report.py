"""Tests for evaluation report rendering, persistence, and status payload."""

import json

from app.evaluation.cases import BENCHMARK_CASES
from app.evaluation.report import (
    load_json,
    load_state,
    render_markdown,
    save_json,
    save_report,
    save_state,
    status_payload,
)
from app.evaluation.schema import BenchmarkCase, CaseResult
from app.evaluation.scoring import score_case


def _report():
    case = BenchmarkCase(
        id="t-1",
        category="repository_search",
        question="Find utils",
        expected_behaviour="find src/utils.py",
        expected_files=["src/utils.py"],
    )
    scored = score_case(
        case,
        CaseResult(
            case_id="t-1",
            actual_answer="top results: src/utils.py, README.md",
            cited_files=["src/utils.py"],
            cited_services=["Calculator"],
            evidence_grounded=True,
            evidence_count=2,
        ),
    )
    from app.evaluation.schema import CategorySummary, EvaluationReport, QualityGates

    return EvaluationReport(
        benchmark_version="1.0.0",
        run_id="abc123",
        ran_at="2026-08-06T12:00:00",
        repository_root="/repo",
        index_files=2,
        index_chunks=3,
        cases=[scored],
        categories=[
            CategorySummary(
                category="repository_search",
                cases=1,
                executed=1,
                average=100.0,
                grounding=10.0,
            )
        ],
        overall_score=100.0,
        hallucinations=0,
        gates=QualityGates(
            repository_search_ge_90=True,
            grounding_eq_100=True,
            hallucinations_zero=True,
            overall_ge_90=True,
        ),
    )


def test_render_markdown_contains_all_sections():
    markdown = render_markdown(_report())
    assert "# AI Engineering Agent — Evaluation Results" in markdown
    assert "## Quality Gates" in markdown
    assert "## Category Summary" in markdown
    assert "## Detailed Results" in markdown
    assert "| Feature | Question | Expected | Actual | Pass / Fail | Score | Notes |" in markdown
    assert "PASS" in markdown
    assert "src/utils.py" in markdown


def test_render_markdown_manual_case_row():
    report = _report()
    manual = score_case(
        BenchmarkCase(
            id="t-2",
            category="issue_assistant",
            mode="manual",
            question="AC?",
            expected_behaviour="x",
        ),
        CaseResult(case_id="t-2", status="manual", notes="manual mode"),
    )
    report.cases.append(manual)
    markdown = render_markdown(report)
    assert "manual" in markdown


def test_save_and_load_report_roundtrip(tmp_path):
    path = tmp_path / "results.json"
    save_json(_report(), path)
    loaded = load_json(path)
    assert loaded is not None
    assert loaded.benchmark_version == "1.0.0"
    assert loaded.overall_score == 100.0
    assert loaded.passed is True


def test_save_report_markdown(tmp_path):
    path = tmp_path / "EVALUATION_RESULTS.md"
    saved = save_report(_report(), path)
    assert saved.exists()
    assert "Evaluation Results" in saved.read_text(encoding="utf-8")


def test_load_json_missing_returns_none(tmp_path):
    assert load_json(tmp_path / "nope.json") is None


def test_load_json_corrupt_returns_none(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    assert load_json(path) is None


def test_status_payload_weakest_and_strongest_categories():
    payload = status_payload(_report())
    assert payload["benchmark_version"] == "1.0.0"
    assert payload["overall_score"] == 100.0
    assert payload["failures"] == 0
    assert payload["weakest_category"] == "repository_search"
    assert payload["strongest_category"] == "repository_search"
    assert payload["gates"]["passed"] is True


def test_status_payload_picks_weakest_among_multiple():
    report = _report()
    weak = score_case(
        BenchmarkCase(id="t-3", category="llm_layer", question="LLM?", expected_behaviour="x"),
        CaseResult(case_id="t-3", actual_answer="short", evidence_grounded=True, evidence_count=0),
    )
    report.cases.append(weak)
    from app.evaluation.schema import CategorySummary

    report.categories.append(
        CategorySummary(
            category="llm_layer", cases=1, executed=1, average=weak.final_score, grounding=10.0
        )
    )
    payload = status_payload(report)
    assert payload["weakest_category"] == "llm_layer"
    assert payload["strongest_category"] == "repository_search"


def test_save_state_roundtrip(tmp_path):
    path = tmp_path / "state.json"
    payload = save_state(_report(), path)
    assert json.loads(path.read_text(encoding="utf-8")) == payload


def test_full_registry_is_scoreable_without_execution():
    for case in BENCHMARK_CASES:
        if case.mode == "auto":
            scored = score_case(
                case,
                CaseResult(
                    case_id=case.id,
                    actual_answer="x" * 40,
                    cited_files=case.expected_files,
                    cited_adrs=case.expected_adrs,
                    cited_services=case.expected_services,
                    evidence_grounded=True,
                    evidence_count=1,
                ),
            )
            assert scored.final_score >= 0.0


def test_render_markdown_includes_declared_adrs():
    report = _report()
    report.cases[0].case.expected_adrs = ["ADR-004"]
    markdown = render_markdown(report)
    assert "ADR-004" in markdown


def test_render_markdown_failed_case_row():
    report = _report()
    failed = score_case(
        BenchmarkCase(id="t-4", category="pr_review", question="q", expected_behaviour="x"),
        CaseResult(case_id="t-4", status="failed", notes="execution error: Boom"),
    )
    report.cases.append(failed)
    markdown = render_markdown(report)
    assert "execution error" in markdown


def test_render_markdown_without_executed_cases_uses_dash():
    from app.evaluation.schema import EvaluationReport

    report = EvaluationReport(benchmark_version="1.0.0", run_id="x", ran_at="t", cases=[])
    markdown = render_markdown(report)
    assert "FAIL" in markdown


def test_load_state_corrupt_returns_none(tmp_path):
    path = tmp_path / "state.json"
    path.write_text("{not json", encoding="utf-8")
    assert load_state(path) is None


def test_category_average_unknown_category_is_zero():
    assert _report().category_average("unknown") == 0.0


def test_case_lookup_unknown_returns_none():
    assert _report().case("missing") is None
