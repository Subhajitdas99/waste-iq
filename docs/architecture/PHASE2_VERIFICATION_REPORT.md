# Phase 2 — PR Review Agent: Verification Report

Date: 2026-08-05
Scope: `agent/` — deterministic, evidence-backed pull request review (no LLM calls, no GitHub writes).

## 1. Deliverables

| Deliverable | Location |
|---|---|
| Settings (additive) | `agent/app/core/config.py` (AGENT_REVIEW_*, AGENT_GITHUB_API_BASE_URL) |
| DB models: `review_sessions`, `review_findings`, `review_evidence` | `agent/app/db/models.py` |
| Alembic migration `0002_review` (chained from `0001_initial`) | `agent/alembic/versions/0002_review.py` |
| Review domain models | `agent/app/review/review_models.py` |
| Diff parser | `agent/app/review/diff.py` |
| Rule catalog (~28 rules, 9 categories) | `agent/app/review/review_prompts.py` |
| Deterministic engine (AST + regex + cross-file) | `agent/app/review/review_engine.py` |
| Context probe (evidence via Phase 1 search) | `agent/app/review/review_context.py` |
| Providers (GitHub read-only + fixture) | `agent/app/review/pr_provider.py`, `fixtures.py` |
| Agent / service / persistence / formatter | `agent/app/review/review_agent.py`, `review_service.py`, `review_repository.py`, `review_formatter.py` |
| API routes + middleware + webhook dispatch | `agent/app/api/routes/review.py`, `agent/app/core/middleware.py`, `agent/app/api/routes/webhooks.py`, `agent/app/api/dependencies.py`, `agent/app/api/router.py`, `agent/app/main.py` |
| Sync installation-token issuance | `agent/app/clients/github_app.py` (`request_installation_token_sync`) |
| Tests | `agent/tests/test_review_*.py` (14 files) |
| Docs | `docs/architecture/PR_REVIEW_AGENT.md`, updated `AI_ENGINEERING_AGENT.md`, ADR-008 |

## 2. Verification runs (agent venv, Python 3.12)

### Lint / format / types (CI flags)

```
ruff check app tests   -> All checks passed!
black --check app tests -> 89 files would be left unchanged.
mypy app               -> Success: no issues found in 56 source files
```

### Tests + coverage (CI flags)

```
pytest tests --tb=short --cov=app --cov-report=term-missing --cov-fail-under=95
266 passed, 2 warnings
TOTAL  2812 stmts, 132 missed -> 95.59% coverage
Required test coverage of 95% reached.
```

### Migrations

```
AGENT_DATABASE_URL=sqlite:///./_smoke_test.db alembic upgrade head
Running upgrade -> 0001_initial, initial schema for the agent service
Running upgrade 0001_initial -> 0002_review, PR review sessions, findings and evidence
```

### End-to-end smoke (deterministic engine on the demo fixture)

```
review(repo=waste-iq/demo, pr=1) -> 22 findings
  critical=1 high=3 medium=10 low=8
  categories: correctness=3, architecture=1, security=1, fastapi=1,
              sqlalchemy=2, react=3, testing=4, documentation=6
  e.g. SEC-EVAL payments.py:16, FASTAPI-MISSING-PATH-PARAM payments.py:12,
       SA-SYNC-IN-ASYNC payments.py:13, ARCH-ROUTE-DB payments.py:7,
       CORR-PY-DEFAULT-MUTABLE analytics.py:4, PERF-NPLUS payments.py:24,
       REACT-DANGEROUS-HTML PaymentList.jsx:16, REACT-KEY PaymentList.jsx:6,
       TEST-GAP/SLEEP/SKIP, DOC-MISSING-DOCSTRING x6
  no duplicate findings (dedupe by rule_id+file+line)
```

### Live boot (uvicorn :8711)

```
GET  /api/health           -> {"status":"ok", ...}
GET  /api/review/status    -> {"healthy":true,"enabled":true,"engine_version":"2.0.0",
                               "total_sessions":0,...}
POST /api/review/pr        -> {"session_id":1, "findings":22,
                               "counts_by_severity":{"critical":1,"high":3,"medium":10,"low":8}}
```

### Webhook dispatch (unit-level)

- `pull_request.opened` / `synchronize` → response contains `review: {session_id, findings_count}`.
- `workflow_run.completed` (known head branch) → review triggered via PR lookup.
- `issues` events → no review key; non-demo repos → no network, graceful 202.
- Review failure never fails the webhook acknowledgement.

## 3. Bugs found and fixed during verification

1. `ReviewSummary.build` computed per-category `top_severity` from the global
   severity histogram instead of each category's own severities → per-category
   top severity corrected (e.g. `security=critical`, `correctness=low`).
2. `DiffHunk.new_lines()` collided with the `new_lines` field (mypy `no-redef`)
   → renamed `new_side_lines()`.
3. `ReviewEngine` sync-SQLAlchemy checks matched string prefixes instead of exact
   names → `SessionLocal()`/`Session()` now caught (`_SYNC_SA_NAMES`).
4. React checks loop applied only `REACT-KEY-INDEX` → all regex checks are applied.
5. `_target_blank_check` could return a non-finding → typed to return
   `ReviewFinding | None`.
6. `ChangedFile.added_lines` returned `[]` for added files whose full content was
   not yet attached → fall back to hunk added lines when `content is None`.
7. `snippet_around` indexed out of bounds for the first line → index clamped.
8. Context probe symbol regex captured the last token of a call signature instead
   of the function name → captures the declared name (`refunds_by_amount`).

## 4. Security notes

- GitHub access is **read-only** (`GET /repos/{owner}/{repo}/pulls`, `…/files`,
  `…/contents`), authenticated with a short-lived installation token issued from
  the app JWT; only the sync path (`request_installation_token_sync`) was added,
  mirroring the existing async `GitHubAppAuth`.
- Equality Review process never reads secrets; path/content retrieval inherits the
  Phase 1 deny-list and repository rootedness.
- The demo fixture contains no secrets and is used only to exercise rules
  deterministically.

## 5. Out of scope (next phases)

- LLM-based prose review and inline GitHub review comments (Approval Engine v1).
- Auto-find behavior via `AGENT_REVIEW_FIND_PULL_REQUEST` is config-ready but not
  auto-triggered beyond webhook dispatch.
- Issue Assistant and subsequent phases begin only after this phase is reviewed.