"""Benchmark runner — executes every case against the real subsystems.

Dispatch by category to the live implementation (Repository Context Service,
PR Review Agent, Issue Assistant, Documentation Agent, LLM layer) and records
the observed behaviour for deterministic scoring. Never writes to the
repository and never modifies any assistant.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

from app.evaluation.cases import BENCHMARK_CASES, CATEGORY_ORDER
from app.evaluation.checks import CHECK_HANDLERS
from app.evaluation.schema import (
    BenchmarkCase,
    CaseResult,
    CategorySummary,
    EvaluationReport,
    QualityGates,
    ScoredCase,
)
from app.evaluation.scoring import score_case


class BenchmarkRunner:
    """Executes the benchmark suite and produces an EvaluationReport."""

    def __init__(self, container=None, cases: list[BenchmarkCase] | None = None) -> None:
        self._container = container
        self._cases = cases if cases is not None else BENCHMARK_CASES

    @property
    def container(self):
        if self._container is None:
            from app.api.dependencies import get_container

            self._container = get_container()
        return self._container

    # ------------------------------------------------------------------
    def run(self) -> EvaluationReport:
        indexed_paths = set(self.container.store().indexed_files())
        scored: list[ScoredCase] = []
        for case in self._cases:
            result = self._execute(case, indexed_paths)
            scored.append(score_case(case, result))

        report = EvaluationReport(
            benchmark_version=self._benchmark_version(),
            run_id=uuid.uuid4().hex[:12],
            ran_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            repository_root=str(self.container.repository_root),
            cases=scored,
        )
        report.categories = self._category_summaries(scored)
        executed = [c for c in scored if c.result.status == "executed"]
        if executed:
            report.overall_score = round(sum(c.final_score for c in executed) / len(executed), 2)
        report.hallucinations = sum(len(c.result.hallucinated_citations) for c in executed)
        report.gates = self._quality_gates(report, executed)
        return report

    # ------------------------------------------------------------------
    def _execute(self, case: BenchmarkCase, indexed_paths: set[str]) -> CaseResult:
        if case.mode == "manual":
            return CaseResult(
                case_id=case.id,
                status="manual",
                actual_answer="Manual case — scored by a human per the scoring guide.",
                notes="manual mode",
            )
        handler = _HANDLERS.get(case.category)
        if handler is None:
            return CaseResult(case_id=case.id, status="skipped", notes="no handler")
        t0 = time.monotonic()
        try:
            result = handler(self, case, indexed_paths)
        except Exception as exc:  # noqa: BLE001 - benchmark must never crash
            result = CaseResult(
                case_id=case.id,
                status="failed",
                actual_answer="",
                notes=f"execution error: {type(exc).__name__}: {exc}",
            )
        result.notes = result.notes or f"ran in {(time.monotonic() - t0) * 1000:.0f}ms"
        return result

    # ------------------------------------------------------------------
    @staticmethod
    def _benchmark_version() -> str:
        from app.core.config import settings

        return settings.agent_benchmark_version

    @staticmethod
    def _category_summaries(scored: list[ScoredCase]) -> list[CategorySummary]:
        summaries: list[CategorySummary] = []
        for category in CATEGORY_ORDER:
            cases = [c for c in scored if c.case.category == category]
            executed = [c for c in cases if c.result.status == "executed"]
            summary = CategorySummary(category=category, cases=len(cases))
            summary.executed = len(executed)
            summary.manual = sum(1 for c in cases if c.result.status == "manual")
            summary.failed = sum(1 for c in cases if c.result.status == "failed")
            if executed:
                summary.average = round(sum(c.final_score for c in executed) / len(executed), 2)
                summary.grounding = round(sum(c.grounding for c in executed) / len(executed), 2)
            summaries.append(summary)
        return summaries

    @staticmethod
    def _quality_gates(report: EvaluationReport, executed: list[ScoredCase]) -> QualityGates:
        if not executed:
            return QualityGates()
        search_cases = [
            c for c in executed if c.case.category == "repository_search" and c.case.mode == "auto"
        ]
        search_average = (
            round(sum(c.final_score for c in search_cases) / len(search_cases), 2)
            if search_cases
            else 0.0
        )
        grounding_average = (
            round(sum(c.grounding for c in executed) / len(executed), 2) if executed else 0.0
        )
        return QualityGates(
            repository_search_ge_90=bool(search_cases) and search_average >= 90.0,
            grounding_eq_100=grounding_average >= 10.0,
            hallucinations_zero=report.hallucinations == 0,
            overall_ge_90=report.overall_score >= 90.0,
        )


# ---------------------------------------------------------------------------
# Handlers — one per category. Each returns the observed CaseResult.
# ---------------------------------------------------------------------------


def _search(container, query: str, limit: int) -> list[str]:
    from app.context.models import SearchRequest

    response = container.search_service().hybrid_search(SearchRequest(query=query, limit=limit))
    return [result.path for result in response.results]


def _handle_search(runner: BenchmarkRunner, case: BenchmarkCase, indexed: set[str]) -> CaseResult:
    payload = case.payload
    paths = _search(runner.container, payload["search_query"], case.scoring_rules.rank_limit)
    return CaseResult(
        case_id=case.id,
        actual_answer=f"top {len(paths)} results: " + ", ".join(paths or ["<none>"]),
        cited_files=paths,
        evidence_grounded=True,
        evidence_count=len(paths),
        hallucinated_citations=[p for p in paths if p not in indexed],
    )


def _handle_architecture(
    runner: BenchmarkRunner, case: BenchmarkCase, indexed: set[str]
) -> CaseResult:
    result = _handle_search(runner, case, indexed)
    adrs_found = []
    if any("ARCHITECTURE_DECISIONS.md" in path for path in result.cited_files):
        from app.context.models import SearchRequest

        response = runner.container.search_service().hybrid_search(
            SearchRequest(query=case.payload["search_query"], limit=case.scoring_rules.rank_limit)
        )
        for item in response.results:
            if "ARCHITECTURE_DECISIONS.md" not in item.path:
                continue
            section = item.section_title or ""
            for adr in case.expected_adrs:
                if adr.lower() in section.lower():
                    adrs_found.append(adr)
    result.cited_adrs = sorted(set(adrs_found))
    result.actual_answer += f" | ADRs found: {', '.join(result.cited_adrs) or '<none>'}"
    return result


def _issue_behaviour_met(case: BenchmarkCase, triage, payload: dict) -> bool | None:
    """Automated pass/fail assertion per issue case; None when no assertion."""
    if case.id == "ia-01-generate-issue-draft":
        priority_ok = triage.priority in ("high", "critical")
        evidence_ok = len(triage.evidence) > 0
        labels_ok = True
        if payload.get("repo_labels") is not None:
            allowed = {label.lower() for label in payload["repo_labels"]}
            labels_ok = bool(triage.suggested_labels) and all(
                label.lower() in allowed for label in triage.suggested_labels
            )
        return priority_ok and evidence_ok and labels_ok
    if case.id == "ia-02-duplicate-detection":
        return len(triage.duplicate_of) > 0
    if case.id == "ia-03-label-suggestions":
        allowed = {label.lower() for label in payload.get("repo_labels") or []}
        return bool(triage.suggested_labels) and all(
            label.lower() in allowed for label in triage.suggested_labels
        )
    if case.id == "ia-04-milestone-suggestions":
        return triage.milestone is not None
    return None


def _handle_issue(runner: BenchmarkRunner, case: BenchmarkCase, indexed: set[str]) -> CaseResult:
    from app.agents.issue_agent import IssueAssistant

    payload = case.payload
    triage = IssueAssistant(runner.container).analyze(
        payload["issue"],
        open_issues=payload.get("open_issues"),
        repo_labels=payload.get("repo_labels"),
    )
    evidence_paths = [item.path for item in triage.evidence]
    note = (
        f"priority={triage.priority} labels={triage.suggested_labels} "
        f"milestone={triage.milestone or '-'} duplicates={len(triage.duplicate_of)}"
    )
    if payload.get("repo_labels") is not None:
        allowed = {label.lower() for label in payload["repo_labels"]}
        ok_labels = all(label.lower() in allowed for label in triage.suggested_labels)
        note += f" labels_within_repo={ok_labels}"
    hallucinated = [p for p in evidence_paths if p not in indexed]
    return CaseResult(
        case_id=case.id,
        actual_answer=f"triage for #{triage.issue_number}: {note}",
        cited_files=evidence_paths,
        cited_services=["IssueAssistant.analyze"],
        evidence_grounded=not hallucinated,
        evidence_count=len(evidence_paths),
        hallucinated_citations=hallucinated,
        behaviour_met=_issue_behaviour_met(case, triage, payload),
        notes=note,
    )


def _handle_review(runner: BenchmarkRunner, case: BenchmarkCase, indexed: set[str]) -> CaseResult:
    from app.review.fixtures import demo_pull_request
    from app.review.pr_provider import FixturePullRequestProvider
    from app.review.review_agent import ReviewAgent
    from app.review.review_context import RepositoryProbe
    from app.review.review_engine import ReviewEngine
    from app.review.review_models import ReviewRequest

    payload = case.payload
    probe = RepositoryProbe(runner.container)
    agent = ReviewAgent(FixturePullRequestProvider(), probe, ReviewEngine(probe))
    review = agent.review(
        ReviewRequest(repository=payload["repository"], pr_number=payload["pr_number"])
    )
    diff_files = {f.path for f in demo_pull_request().files}
    findings = review.findings
    rule_ids = sorted({f.rule_id for f in findings})
    categories = sorted({f.category for f in findings})
    cited_files = sorted({f.file_path for f in findings})
    outside = [f.file_path for f in findings if f.file_path not in diff_files]
    summary = (
        f"{len(findings)} findings across {', '.join(categories)}; "
        f"rules: {', '.join(rule_ids[:12])}"
    )
    return CaseResult(
        case_id=case.id,
        actual_answer=summary,
        cited_files=cited_files,
        cited_services=rule_ids,
        evidence_grounded=not outside,
        evidence_count=len(findings),
        hallucinated_citations=[],
        notes=f"diff files={len(diff_files)} findings={len(findings)} out_of_diff={len(outside)}",
    )


def _handle_documentation(
    runner: BenchmarkRunner, case: BenchmarkCase, indexed: set[str]
) -> CaseResult:
    from app.agents.doc_agent import DocAssistant, build_changelog_entry

    payload = case.payload
    if case.id == "dc-01-generate-changelog":
        section, entry = build_changelog_entry(
            payload["pr_number"], payload["pr_title"], "Adds the endpoint and tests."
        )
        return CaseResult(
            case_id=case.id,
            actual_answer=f"section={section} entry={entry}",
            cited_services=["build_changelog_entry", section or "none"],
            evidence_grounded=bool(section and entry),
            evidence_count=1,
            notes="entry generated" if section else "no entry for non-conventional title",
        )
    if case.id == "dc-03-explain-module":
        return _handle_search(runner, case, indexed)
    proposal = DocAssistant().analyze(
        {"number": payload["pr_number"], "title": payload["pr_title"]},
        changed_files=payload["changed_files"],
        pr_body="Adds the feature with tests.",
    )
    suggested = [update.doc_path for update in proposal.doc_updates]
    hallucinated = [p for p in suggested if p not in indexed]
    answer = (
        f"proposal for PR #{proposal.pr_number}: "
        f"changelog={proposal.changelog_section or '-'} "
        f"doc_updates={', '.join(suggested) or '<none>'}"
    )
    return CaseResult(
        case_id=case.id,
        actual_answer=answer,
        cited_files=suggested,
        cited_services=["DocAssistant.analyze"],
        evidence_grounded=not hallucinated,
        evidence_count=len(suggested),
        hallucinated_citations=hallucinated,
        notes=proposal.summary,
    )


def _handle_llm(runner: BenchmarkRunner, case: BenchmarkCase, indexed: set[str]) -> CaseResult:
    handler = CHECK_HANDLERS.get(case.payload.get("check", ""))
    if handler is None:
        return CaseResult(case_id=case.id, status="skipped", notes="unknown check")
    return handler()


_HANDLERS = {
    "repository_search": _handle_search,
    "architecture": _handle_architecture,
    "issue_assistant": _handle_issue,
    "pr_review": _handle_review,
    "documentation": _handle_documentation,
    "llm_layer": _handle_llm,
}
