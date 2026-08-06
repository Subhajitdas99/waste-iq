"""Phase 2.6 retrieval benchmark for the Repository Context Service.

Runs a known-query suite against the real repository index and reports
recall@5 plus the rank of each expected file. The three validation
queries (dealer approval, refresh token, review_engine) must land their
expected file in the top-5; the script exits non-zero otherwise.

Usage:
    python scripts/retrieval_benchmark.py [--repository-root PATH] [--limit N]
"""

from __future__ import annotations

import argparse
import os
import sys
import time

from pathlib import Path

AGENT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AGENT_ROOT))

# Validation queries are STRICT: the exact expected file must rank in the
# top-N. Additional queries are domain checks (any-of): the top-N must
# contain a file that is genuinely relevant to the query.
VALIDATION_QUERIES: list[tuple[str, list[str]]] = [
    ("dealer approval", ["backend/app/services/dealer_approval.py"]),
    ("refresh token", ["frontend/src/api/client.ts"]),
    ("review_engine", ["agent/app/review/review_engine.py"]),
]

ADDITIONAL_QUERIES: list[tuple[str, list[str]]] = [
    (
        "dealer inventory",
        [
            "backend/app/services/dealer_inventory.py",
            "backend/app/repositories/dealer_inventory.py",
        ],
    ),
    (
        "collector pickup",
        [
            "backend/app/services/pickup_requests.py",
            "backend/app/services/collector_map.py",
            "backend/app/services/collector_summary.py",
            "backend/app/api/routes/collector.py",
        ],
    ),
    (
        "marketplace",
        [
            "backend/app/services/marketplace.py",
            "backend/app/repositories/marketplace.py",
            "backend/app/api/routes/marketplace.py",
        ],
    ),
    (
        "review agent",
        [
            "agent/app/review/review_agent.py",
            "docs/architecture/PR_REVIEW_AGENT.md",
            "agent/tests/test_review_agent.py",
        ],
    ),
    (
        "notifications",
        [
            "backend/app/services/notifications.py",
            "frontend/src/api/notifications.ts",
            "frontend/src/hooks/useNotifications.ts",
            "frontend/src/components/dashboard/notifications/",
        ],
    ),
    (
        "auth login",
        [
            "backend/app/services/auth.py",
            "backend/app/api/routes/auth.py",
            "frontend/src/hooks/useLogin.ts",
            "frontend/src/pages/auth/LoginPage.tsx",
        ],
    ),
    (
        "roadmap",
        ["docs/project-management/launch-roadmap.md", "docs/SPRINT_ROADMAP.md"],
    ),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", default=None)
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    if args.repository_root:
        os.environ["AGENT_REPOSITORY_ROOT"] = args.repository_root
    os.environ.setdefault("AGENT_DATABASE_URL", f"sqlite:///{AGENT_ROOT / 'agent.db'}")

    from app.context.di import Container
    from app.context.models import SearchRequest
    from app.db.session import SessionLocal

    container = Container(SessionLocal)

    print("=" * 78)
    print("RETRIEVAL BENCHMARK — Phase 2.6")
    print(f"repository root : {container.repository_root}")
    print("=" * 78)

    t0 = time.monotonic()
    summary = container.pipeline().run()
    took = time.monotonic() - t0
    status = container.status()
    print(
        f"index  : {status['indexed_files']} files, {status['chunk_count']} chunks, "
        f"{status['vector_count']} vectors (run took {took:.1f}s, "
        f"{summary.new_files} new / {summary.updated_files} updated)"
    )
    if status["vector_count"] != status["chunk_count"]:
        print(
            f"!! VECTOR INDEX MISMATCH: chunk_count={status['chunk_count']} "
            f"vector_count={status['vector_count']}"
        )
        return 1
    print()

    service = container.search_service()
    all_queries = VALIDATION_QUERIES + ADDITIONAL_QUERIES
    hits = 0
    rows: list[tuple[str, list[str], int | None, list[tuple[float, str]]]] = []

    for query, expected in all_queries:
        response = service.hybrid_search(SearchRequest(query=query, limit=args.limit))
        top = [(r.score, r.path) for r in response.results]
        rank: int | None = None
        for i, (_score, path) in enumerate(top):
            if any(fragment in path for fragment in expected):
                rank = i
                break
        if rank is not None:
            hits += 1
        rows.append((query, expected, rank, top))

    for query, expected, rank, top in rows:
        expected_label = next(
            (part for fragment in expected for part in reversed(fragment.split("/")) if part),
            "?",
        )
        ok = rank is not None and rank < args.limit
        marker = "PASS" if ok else "FAIL"
        print(f"[{marker}] {query!r:<22} expected={expected_label:<32} rank={rank}")
        for score, path in top[: args.limit]:
            print(f"        {score:8.4f}  {path}")

    validation_ok = all(
        rank is not None and rank < args.limit
        for query, expected, rank, _top in rows
        if query in [q for q, _ in VALIDATION_QUERIES]
    )

    recall = hits / len(all_queries)
    print("-" * 78)
    print(f"recall@{args.limit}: {hits}/{len(all_queries)} ({recall:.0%})")
    print(
        f"validation queries: "
        f"{'PASS' if validation_ok else 'FAIL'} (all expected files in top {args.limit})"
    )
    return 0 if validation_ok else 1


if __name__ == "__main__":
    sys.exit(main())
