"""Tests for regression detection (Phase 4.5)."""

from app.evaluation.regression import compare_reports
from app.evaluation.schema import BenchmarkCase, CaseResult, EvaluationReport
from app.evaluation.scoring import score_case


def _report(scores: dict[str, float]) -> EvaluationReport:
    scored = []
    for case_id, final in scores.items():
        case = BenchmarkCase(
            id=case_id,
            category="llm_layer",
            question="q",
            expected_behaviour="b",
        )
        result = CaseResult(
            case_id=case_id,
            actual_answer="x" * 40,
            evidence_grounded=True,
            evidence_count=1,
        )
        item = score_case(case, result)
        item.final_score = final
        scored.append(item)
    overall = round(sum(scores.values()) / len(scores), 2) if scores else 0.0
    return EvaluationReport(
        benchmark_version="1.0.0",
        run_id="r",
        ran_at="2026-08-06T00:00:00",
        cases=scored,
        overall_score=overall,
    )


def test_no_change_detects_no_regression():
    baseline = _report({"a": 95.0, "b": 92.0})
    current = _report({"a": 95.0, "b": 92.0})
    comparison = compare_reports(baseline, current)
    assert comparison.passed is True
    assert comparison.regressions == []
    assert comparison.overall_delta == 0.0


def test_score_drop_beyond_tolerance_is_regression():
    baseline = _report({"a": 95.0, "b": 92.0})
    current = _report({"a": 90.0, "b": 92.0})
    comparison = compare_reports(baseline, current)
    assert len(comparison.regressions) == 1
    assert comparison.regressions[0].case_id == "a"
    assert comparison.passed is False


def test_small_drop_within_tolerance_is_not_regression():
    baseline = _report({"a": 95.0, "b": 92.0})
    current = _report({"a": 94.5, "b": 92.0})
    comparison = compare_reports(baseline, current)
    assert comparison.regressions == []
    assert comparison.passed is True


def test_pass_to_fail_flip_is_regression_within_tolerance():
    baseline = _report({"a": 90.5, "b": 92.0})
    current = _report({"a": 89.5, "b": 92.0})
    comparison = compare_reports(baseline, current)
    assert any(r.case_id == "a" for r in comparison.regressions)


def test_new_case_in_current_is_ignored():
    baseline = _report({"a": 95.0})
    current = _report({"a": 95.0, "b": 95.0})
    comparison = compare_reports(baseline, current)
    assert comparison.regressions == []
    assert comparison.overall_delta == 0.0


def test_overall_drop_beyond_one_point_blocks():
    baseline = _report({"a": 95.0, "b": 92.0})
    current = _report({"a": 90.0, "b": 85.0})
    comparison = compare_reports(baseline, current)
    assert comparison.overall_delta < -1.0
    assert comparison.passed is False
