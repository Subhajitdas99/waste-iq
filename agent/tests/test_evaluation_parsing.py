"""Tests for benchmark registry parsing + integrity (Phase 4.5)."""

import pytest

from app.evaluation.cases import (
    BENCHMARK_CASES,
    CATEGORY_ORDER,
    ARCHITECTURE_CASES,
    DOCUMENTATION_CASES,
    ISSUE_ASSISTANT_CASES,
    LLM_LAYER_CASES,
    PR_REVIEW_CASES,
    REPOSITORY_SEARCH_CASES,
)
from app.evaluation.schema import BenchmarkCase


def test_every_case_has_all_required_fields():
    for case in BENCHMARK_CASES:
        assert case.id
        assert case.category in CATEGORY_ORDER
        assert case.question
        assert case.expected_behaviour
        assert case.scoring_rules.rank_limit >= 1
        assert set(case.scoring_rules.weights) == {
            "repository_accuracy",
            "grounding",
            "helpfulness",
            "completeness",
            "hallucination_resistance",
        }


def test_case_ids_are_unique():
    ids = [case.id for case in BENCHMARK_CASES]
    assert len(ids) == len(set(ids))


def test_benchmark_covers_all_six_categories():
    categories = {case.category for case in BENCHMARK_CASES}
    assert categories == set(CATEGORY_ORDER)


def test_category_counts_match_spec():
    assert len(REPOSITORY_SEARCH_CASES) >= 6
    assert len(ARCHITECTURE_CASES) >= 4
    assert len(ISSUE_ASSISTANT_CASES) >= 6
    assert len(PR_REVIEW_CASES) >= 6
    assert len(DOCUMENTATION_CASES) >= 5
    assert len(LLM_LAYER_CASES) >= 7


def test_manual_cases_only_where_behaviour_not_deterministic():
    manual = [case for case in BENCHMARK_CASES if case.mode == "manual"]
    assert {case.id for case in manual} == {
        "ia-05-acceptance-criteria",
        "ia-06-complexity-estimation",
    }


def test_every_auto_case_has_execution_payload():
    for case in BENCHMARK_CASES:
        if case.mode == "auto":
            assert case.payload, f"{case.id} is missing its execution payload"


def test_search_cases_have_query_and_expected_files():
    for case in REPOSITORY_SEARCH_CASES:
        assert "search_query" in case.payload
        assert case.expected_files


def test_review_cases_use_fixture_repo():
    for case in PR_REVIEW_CASES:
        assert case.payload["repository"] == "waste-iq/demo"
        assert case.payload["pr_number"] == 1


def test_llm_cases_have_check_handler_name():
    from app.evaluation.checks import CHECK_HANDLERS

    for case in LLM_LAYER_CASES:
        assert case.payload["check"] in CHECK_HANDLERS


def test_expected_adrs_only_on_architecture_cases():
    for case in BENCHMARK_CASES:
        if case.expected_adrs:
            assert case.category == "architecture"


def test_case_roundtrip_serialization():
    case = BENCHMARK_CASES[0]
    restored = BenchmarkCase.model_validate(case.model_dump())
    assert restored == case


@pytest.mark.parametrize("case", BENCHMARK_CASES, ids=lambda c: c.id)
def test_each_case_question_is_substantive(case):
    assert len(case.question.strip()) >= 5
