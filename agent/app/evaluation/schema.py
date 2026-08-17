"""Benchmark schema — typed definitions for evaluation cases and results."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Category = Literal[
    "repository_search",
    "architecture",
    "issue_assistant",
    "pr_review",
    "documentation",
    "llm_layer",
]

CaseMode = Literal["auto", "manual"]

_WEIGHT_DEFAULT = {
    "repository_accuracy": 0.30,
    "grounding": 0.25,
    "helpfulness": 0.15,
    "completeness": 0.15,
    "hallucination_resistance": 0.15,
}


class ScoringRules(BaseModel):
    model_config = ConfigDict(extra="forbid")

    weights: dict[str, float] = Field(default_factory=lambda: dict(_WEIGHT_DEFAULT))
    rank_limit: int = 5


class BenchmarkCase(BaseModel):
    """One benchmark case, self-contained and deterministic.

    Every case declares what a correct answer must reference (files, ADRs,
    services) so scoring never depends on subjective judgment.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    category: Category
    mode: CaseMode = "auto"
    question: str
    expected_behaviour: str
    expected_files: list[str] = []
    expected_adrs: list[str] = []
    expected_services: list[str] = []
    expected_confidence: float | None = None
    scoring_rules: ScoringRules = Field(default_factory=ScoringRules)

    # Execution payload: exactly one key per category is consumed by the
    # runner (e.g. search_query for repository_search cases).
    payload: dict[str, Any] = Field(default_factory=dict)


class CaseResult(BaseModel):
    """Actual behaviour observed while executing a case."""

    model_config = ConfigDict(extra="forbid")

    case_id: str
    status: Literal["executed", "manual", "failed", "skipped"] = "executed"
    actual_answer: str = ""
    cited_files: list[str] = []
    cited_adrs: list[str] = []
    cited_services: list[str] = []
    evidence_grounded: bool = True
    evidence_count: int = 0
    hallucinated_citations: list[str] = []
    behaviour_met: bool | None = None
    notes: str = ""


class ScoredCase(BaseModel):
    """A case plus its five sub-scores (0-10) and weighted final score (0-100)."""

    model_config = ConfigDict(extra="forbid")

    case: BenchmarkCase
    result: CaseResult
    repository_accuracy: float = 0.0
    grounding: float = 0.0
    helpfulness: float = 0.0
    completeness: float = 0.0
    hallucination_resistance: float = 10.0
    final_score: float = 0.0

    @property
    def passed(self) -> bool:
        return self.result.status == "executed" and self.final_score >= 90.0


class CategorySummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str
    cases: int = 0
    executed: int = 0
    manual: int = 0
    failed: int = 0
    average: float = 0.0
    grounding: float = 0.0


class QualityGates(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repository_search_ge_90: bool = False
    grounding_eq_100: bool = False
    hallucinations_zero: bool = False
    overall_ge_90: bool = False

    @property
    def passed(self) -> bool:
        return (
            self.repository_search_ge_90
            and self.grounding_eq_100
            and self.hallucinations_zero
            and self.overall_ge_90
        )


class EvaluationReport(BaseModel):
    """Full benchmark run: cases, aggregates, gates, and a human verdict."""

    model_config = ConfigDict(extra="forbid")

    benchmark_version: str
    run_id: str
    ran_at: str
    repository_root: str = ""
    index_files: int = 0
    index_chunks: int = 0
    cases: list[ScoredCase] = []
    categories: list[CategorySummary] = []
    overall_score: float = 0.0
    hallucinations: int = 0
    gates: QualityGates = Field(default_factory=QualityGates)

    @property
    def passed(self) -> bool:
        return self.gates.passed

    def category_average(self, category: str) -> float:
        for summary in self.categories:
            if summary.category == category:
                return summary.average
        return 0.0

    def case(self, case_id: str) -> ScoredCase | None:
        for scored in self.cases:
            if scored.case.id == case_id:
                return scored
        return None


class RegressionCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    baseline_score: float
    current_score: float
    delta: float
    passed_before: bool
    passed_now: bool
    regression: bool


class RegressionReport(BaseModel):
    """Baseline vs. current comparison — a regression blocks a release."""

    model_config = ConfigDict(extra="forbid")

    baseline_version: str
    current_version: str
    baseline_overall: float
    current_overall: float
    overall_delta: float
    cases: list[RegressionCase] = []
    regressions: list[RegressionCase] = []

    @property
    def passed(self) -> bool:
        return not self.regressions and self.overall_delta >= -1.0
