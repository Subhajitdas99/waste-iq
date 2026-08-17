"""Deterministic scoring for benchmark cases.

Every case yields five sub-scores (0-10) and a weighted final score (0-100):

- repository_accuracy  — did the answer find/reference the right files?
- grounding            — are all citations real files in the indexed corpus?
- helpfulness          — does the answer actually answer the question?
- completeness         — share of expected files/ADRs/services present?
- hallucination_resistance — are there any non-existent citations at all?

Weights follow the quality gates: search accuracy 0.30, grounding 0.25,
helpfulness 0.15, completeness 0.15, hallucination resistance 0.15.
"""

from __future__ import annotations

from app.evaluation.schema import BenchmarkCase, CaseResult, ScoredCase

_RANK_SCORES = {0: 10.0, 1: 8.0, 2: 6.0, 3: 4.0, 4: 2.0}


def best_rank(cited_files: list[str], expected_files: list[str], limit: int) -> int | None:
    """Best rank of any expected file among cited files (rank = index in list)."""
    for rank, path in enumerate(cited_files[:limit]):
        for fragment in expected_files:
            if fragment in path:
                return rank
    return None


def score_repository_accuracy(case: BenchmarkCase, result: CaseResult) -> tuple[float, str]:
    if not case.expected_files:
        if result.status == "executed":
            return 10.0, "no file expectations (behaviour case)"
        return 0.0, "case did not execute"
    rank = best_rank(result.cited_files, case.expected_files, case.scoring_rules.rank_limit)
    if rank is None:
        return 0.0, "expected file not in top results"
    score = _RANK_SCORES.get(rank, 0.0)
    return score, f"expected file at rank {rank + 1}"


def score_grounding(case: BenchmarkCase, result: CaseResult) -> tuple[float, str]:
    if result.status != "executed":
        return 0.0, "case did not execute"
    if not result.evidence_grounded:
        return 0.0, "evidence contains ungrounded references"
    if result.evidence_count == 0 and not case.expected_files:
        return 10.0, "no citations produced (nothing to ground)"
    return 10.0, f"{result.evidence_count} citation(s) all resolved"


def score_helpfulness(case: BenchmarkCase, result: CaseResult) -> tuple[float, str]:
    if result.status != "executed":
        return 0.0, "case did not execute"
    answer = result.actual_answer.strip()
    if not answer:
        return 0.0, "empty answer"
    if len(answer) < 20:
        return 4.0, "answer too short to be useful"
    if case.expected_behaviour and result.behaviour_met is False:
        return 0.0, "expected behaviour not met"
    return 10.0, "answer present and substantive"


def score_completeness(case: BenchmarkCase, result: CaseResult) -> tuple[float, str]:
    expectations = [
        (case.expected_files, result.cited_files),
        (case.expected_adrs, result.cited_adrs),
        (case.expected_services, result.cited_services),
    ]
    total = sum(len(items) for items, _actual in expectations)
    if total == 0:
        if result.status == "executed":
            return 10.0, "no expectations declared"
        return 0.0, "case did not execute"
    matched = 0
    for expected, actual in expectations:
        for fragment in expected:
            if any(fragment in item for item in actual):
                matched += 1
    return round(10.0 * matched / total, 2), f"{matched}/{total} expectations met"


def score_hallucination_resistance(case: BenchmarkCase, result: CaseResult) -> tuple[float, str]:
    hallucinations = len(result.hallucinated_citations)
    if hallucinations == 0:
        return 10.0, "zero hallucinated citations"
    score = max(0.0, 10.0 - 10.0 * hallucinations)
    return score, f"{hallucinations} hallucinated citation(s)"


def score_case(case: BenchmarkCase, result: CaseResult) -> ScoredCase:
    """Compute the five sub-scores and the weighted final score for one case."""
    if result.status != "executed":
        return ScoredCase(case=case, result=result)
    repo_accuracy, repo_note = score_repository_accuracy(case, result)
    grounding, grounding_note = score_grounding(case, result)
    helpfulness, helpfulness_note = score_helpfulness(case, result)
    completeness, completeness_note = score_completeness(case, result)
    hallucination, hallucination_note = score_hallucination_resistance(case, result)

    weights = case.scoring_rules.weights
    final = round(
        10.0
        * (
            repo_accuracy * weights["repository_accuracy"]
            + grounding * weights["grounding"]
            + helpfulness * weights["helpfulness"]
            + completeness * weights["completeness"]
            + hallucination * weights["hallucination_resistance"]
        ),
        2,
    )
    return ScoredCase(
        case=case,
        result=result,
        repository_accuracy=round(repo_accuracy, 2),
        grounding=round(grounding, 2),
        helpfulness=round(helpfulness, 2),
        completeness=round(completeness, 2),
        hallucination_resistance=round(hallucination, 2),
        final_score=final,
    )
