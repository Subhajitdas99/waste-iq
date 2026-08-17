"""Run the full AI Engineering Agent benchmark and generate EVALUATION_RESULTS.md.

One command to evaluate the whole agent:

    python scripts/run_evaluation.py [--repository-root PATH] [--output PATH]

Exits 0 only when every quality gate passes:

- Repository Search average >= 90
- Grounding average = 100 (every citation resolves)
- Hallucinated citations = 0
- Overall score >= 90

Optionally compares against a stored baseline JSON (--baseline) and exits
non-zero on regressions.
"""

from __future__ import annotations

import argparse
import os
import sys
import time

from pathlib import Path

AGENT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AGENT_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", default=None)
    parser.add_argument(
        "--output",
        default=str(AGENT_ROOT.parent / "docs" / "evaluation" / "EVALUATION_RESULTS.md"),
    )
    parser.add_argument("--json-output", default=None)
    parser.add_argument("--baseline", default=None)
    parser.add_argument("--skip-index", action="store_true")
    parser.add_argument("--version", action="store_true")
    args = parser.parse_args()

    if args.repository_root:
        os.environ["AGENT_REPOSITORY_ROOT"] = args.repository_root
    os.environ.setdefault("AGENT_DATABASE_URL", f"sqlite:///{AGENT_ROOT / 'agent.db'}")

    from app.core.config import settings
    from app.evaluation.regression import compare_reports
    from app.evaluation.report import (
        load_json,
        save_json,
        save_report,
        save_state,
    )
    from app.evaluation.runner import BenchmarkRunner

    if args.version:
        print(settings.agent_benchmark_version)
        return 0

    from app.context.di import Container
    from app.db.session import SessionLocal

    container = Container(SessionLocal)

    print("=" * 78)
    print("AI ENGINEERING AGENT — EVALUATION BENCHMARK")
    print(f"benchmark version : {settings.agent_benchmark_version}")
    print(f"repository root   : {container.repository_root}")
    print("=" * 78)

    if not args.skip_index:
        t0 = time.monotonic()
        summary = container.pipeline().run()
        took = time.monotonic() - t0
        status = container.status()
        print(
            f"index  : {status['indexed_files']} files, {status['chunk_count']} chunks, "
            f"{status['vector_count']} vectors ({took:.1f}s, "
            f"{summary.new_files} new / {summary.updated_files} updated)"
        )
        if status["vector_count"] != status["chunk_count"]:
            print("!! VECTOR INDEX MISMATCH")
            return 1
    else:
        status = container.status()
        if status["vector_count"] == 0:
            print("!! vector store is empty (in-memory store) — indexing anyway")
            t0 = time.monotonic()
            summary = container.pipeline().run()
            took = time.monotonic() - t0
            status = container.status()
            print(
                f"index  : {status['indexed_files']} files, {status['chunk_count']} chunks, "
                f"{status['vector_count']} vectors ({took:.1f}s, "
                f"{summary.new_files} new / {summary.updated_files} updated)"
            )

    t0 = time.monotonic()
    report = BenchmarkRunner(container).run()
    took = time.monotonic() - t0
    print(f"benchmark run      : {took:.1f}s, {len(report.cases)} cases")

    report.index_files = container.status()["indexed_files"]
    report.index_chunks = container.status()["chunk_count"]

    output = Path(args.output)
    save_report(report, output)
    if args.json_output:
        save_json(report, args.json_output)
    save_state(report, settings.agent_evaluation_state_path)
    print(f"report             : {output}")
    print(f"state              : {settings.agent_evaluation_state_path}")

    print("-" * 78)
    for summary in report.categories:
        print(
            f"{summary.category:<20} avg={summary.average:6.2f}  "
            f"grounding={summary.grounding:6.2f}  "
            f"(executed {summary.executed}/{summary.cases}, manual {summary.manual})"
        )
    print("-" * 78)
    print(f"OVERALL SCORE      : {report.overall_score:.2f}")
    print(f"HALLUCINATIONS     : {report.hallucinations}")
    gates = report.gates
    print(
        f"GATES              : search>=90 {gates.repository_search_ge_90} | "
        f"grounding=100 {gates.grounding_eq_100} | "
        f"halluc=0 {gates.hallucinations_zero} | "
        f"overall>=90 {gates.overall_ge_90}"
    )
    print(f"VERDICT            : {'PASS' if gates.passed else 'FAIL'}")

    exit_code = 0 if gates.passed else 1

    if args.baseline:
        baseline = load_json(args.baseline)
        if baseline is None:
            print(f"!! baseline not found: {args.baseline}")
            return 2
        regression = compare_reports(baseline, report)
        print(
            f"REGRESSION         : baseline={regression.baseline_overall:.2f} "
            f"current={regression.current_overall:.2f} "
            f"delta={regression.overall_delta:+.2f} regressions={len(regression.regressions)}"
        )
        for item in regression.regressions:
            print(
                f"  REGRESSION {item.case_id}: "
                f"{item.baseline_score:.2f} -> {item.current_score:.2f}"
            )
        if not regression.passed:
            print("VERDICT            : FAIL (regression detected)")
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
