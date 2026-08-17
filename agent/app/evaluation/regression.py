"""Regression detection — baseline vs. current benchmark runs.

A regression is any case whose score drops more than a tolerance or that
flips from pass to fail; an overall drop beyond tolerance also blocks.
"""

from __future__ import annotations

from app.evaluation.schema import (
    EvaluationReport,
    RegressionCase,
    RegressionReport,
)

_DELTA_TOLERANCE = 1.0


def compare_reports(baseline: EvaluationReport, current: EvaluationReport) -> RegressionReport:
    """Diff current results against a baseline; detect regressions."""
    baseline_cases = {scored.case.id: scored for scored in baseline.cases}
    comparisons: list[RegressionCase] = []
    for scored in current.cases:
        prior = baseline_cases.get(scored.case.id)
        if prior is None or scored.result.status != "executed":
            continue
        delta = round(scored.final_score - prior.final_score, 2)
        regression = delta < -_DELTA_TOLERANCE or (prior.passed and not scored.passed)
        comparisons.append(
            RegressionCase(
                case_id=scored.case.id,
                baseline_score=prior.final_score,
                current_score=scored.final_score,
                delta=delta,
                passed_before=prior.passed,
                passed_now=scored.passed,
                regression=regression,
            )
        )
    regressions = [c for c in comparisons if c.regression]
    return RegressionReport(
        baseline_version=baseline.benchmark_version,
        current_version=current.benchmark_version,
        baseline_overall=baseline.overall_score,
        current_overall=current.overall_score,
        overall_delta=round(current.overall_score - baseline.overall_score, 2),
        cases=comparisons,
        regressions=regressions,
    )
