"""Tests for deterministic benchmark scoring (Phase 4.5)."""

from app.evaluation.schema import BenchmarkCase, CaseResult
from app.evaluation.scoring import (
    score_case,
    score_completeness,
    score_grounding,
    score_helpfulness,
    score_repository_accuracy,
)

_EXPECTED_FILES = ["backend/app/services/notifications.py"]


def _case(**overrides) -> BenchmarkCase:
    values = dict(
        id="t-1",
        category="repository_search",
        question="q",
        expected_behaviour="behaviour",
        expected_files=list(_EXPECTED_FILES),
    )
    values.update(overrides)
    return BenchmarkCase(**values)


def _result(**overrides) -> CaseResult:
    values = dict(
        case_id="t-1",
        actual_answer="answer with enough detail to be helpful for the question asked",
        cited_files=list(_EXPECTED_FILES),
        cited_services=["NotificationService"],
        evidence_grounded=True,
        evidence_count=3,
    )
    values.update(overrides)
    return CaseResult(**values)


def test_rank_one_scores_full_repository_accuracy():
    scored = score_case(_case(), _result(cited_files=list(_EXPECTED_FILES)))
    assert scored.repository_accuracy == 10.0


def test_rank_five_scores_half():
    files = [f"other/file-{i}.py" for i in range(4)] + list(_EXPECTED_FILES)
    scored = score_case(_case(), _result(cited_files=files))
    assert scored.repository_accuracy == 2.0


def test_missing_expected_file_scores_zero():
    scored = score_case(_case(), _result(cited_files=["backend/app/other.py"]))
    assert scored.repository_accuracy == 0.0
    assert scored.completeness == 0.0


def test_grounding_full_when_all_citations_resolve():
    scored = score_case(_case(), _result())
    assert scored.grounding == 10.0


def test_grounding_zero_when_evidence_not_grounded():
    scored = score_case(_case(), _result(evidence_grounded=False))
    assert scored.grounding == 0.0


def test_hallucination_resistance_penalized_per_citation():
    scored = score_case(
        _case(),
        _result(hallucinated_citations=["ghost.py"], evidence_grounded=False),
    )
    assert scored.hallucination_resistance == 0.0


def test_empty_answer_scores_zero_helpfulness():
    scored = score_case(_case(), _result(actual_answer=""))
    assert scored.helpfulness == 0.0


def test_completeness_is_ratio_of_expected_elements():
    case = _case(
        expected_files=["a.py"],
        expected_adrs=["ADR-001"],
        expected_services=["svc-a", "svc-b"],
    )
    scored = score_case(
        case,
        _result(cited_files=["a.py"], cited_adrs=[], cited_services=["svc-a"]),
    )
    assert scored.completeness == 5.0


def test_completeness_full_when_no_expectations():
    case = _case(expected_files=[], expected_adrs=[], expected_services=[])
    scored = score_case(case, _result())
    assert scored.completeness == 10.0


def test_final_score_is_weighted_sum_capped_at_100():
    case = _case(expected_files=[], expected_adrs=[], expected_services=[])
    scored = score_case(case, _result(actual_answer="x" * 40))
    assert scored.final_score == 100.0


def test_manual_case_scores_zero_everywhere():
    case = _case(mode="manual")
    result = CaseResult(case_id="t-1", status="manual", notes="manual mode")
    scored = score_case(case, result)
    assert scored.final_score == 0.0
    assert scored.passed is False


def test_passed_requires_final_90():
    case = _case(expected_files=[], expected_adrs=[], expected_services=[])
    perfect = score_case(case, _result(actual_answer="x" * 40))
    assert perfect.passed is True
    weak = score_case(case, _result(actual_answer="x" * 40, evidence_grounded=False))
    assert weak.passed is False


def test_failed_case_scores_zero():
    case = _case()
    result = CaseResult(case_id="t-1", status="failed", notes="boom")
    scored = score_case(case, result)
    assert scored.final_score == 0.0
    assert scored.grounding == 0.0


def test_sub_scorers_return_zero_for_non_executed_status():
    case = _case(expected_files=[], expected_adrs=[], expected_services=[])
    result = CaseResult(case_id="t-1", status="skipped")
    assert score_repository_accuracy(case, result) == (0.0, "case did not execute")
    assert score_grounding(case, result) == (0.0, "case did not execute")
    assert score_helpfulness(case, result) == (0.0, "case did not execute")
    assert score_completeness(case, result) == (0.0, "case did not execute")


def test_helpfulness_zero_when_expected_behaviour_not_met():
    scored = score_case(_case(), _result(actual_answer="x" * 40, behaviour_met=False))
    assert scored.helpfulness == 0.0
