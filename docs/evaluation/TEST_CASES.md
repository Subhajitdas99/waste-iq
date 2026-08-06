# Benchmark Test Cases

The authoritative registry lives in `agent/app/evaluation/cases.py`; this
document mirrors it. Cases are deterministic: no LLM calls, no network, no
time-of-day dependence. Manual cases are marked `manual`.

## Repository Search (6)

| ID | Question | Search query | Expected file |
|---|---|---|---|
| rs-01 | Find NotificationService | `notification service backend` | `backend/app/services/notifications.py` |
| rs-02 | Find Marketplace APIs | `marketplace reserve inventory backend` | `backend/app/api/routes/marketplace.py` |
| rs-03 | Find review_engine | `review engine implementation` | `agent/app/review/review_engine.py` |
| rs-04 | Find RepositoryIndexer | `repository indexer` | `agent/app/context/repository_indexer.py` |
| rs-05 | Find JWTService | `JWT access token create` | `backend/app/core/security.py` |
| rs-06 | Explain Dealer Approval | `dealer approval workflow` | `backend/app/services/dealer_approval.py` |

The expected file must appear in the top-5 results (rank 1 scores 10,
rank 5 scores 2). Queries are natural user phrasing, not path-shaped hacks.

## Architecture (4)

| ID | Question | Search query | Expected |
|---|---|---|---|
| ar-01 | Explain ADR-004 | `ADR-004 propose-only` | ADR-004 in `docs/architecture/ARCHITECTURE_DECISIONS.md` |
| ar-02 | Explain ADR-008 | `ADR-008 review evidence-backed deterministic` | ADR-008 in `docs/architecture/ARCHITECTURE_DECISIONS.md` |
| ar-03 | Explain Repository Pattern | `backend layered architecture routes services repositories models` | ADR-001 + repository-layer files |
| ar-04 | Explain Marketplace Architecture | `marketplace module router service order model` | marketplace router, service, model + ADR-001 |

The ADR check requires the ADR id to appear in the section title of an
`ARCHITECTURE_DECISIONS.md` chunk in the top-5.

## Issue Assistant (6, of which 2 manual)

| ID | Question | Assertion |
|---|---|---|
| ia-01 | Generate Issue Draft | Crash issue on dealer approval → priority high/critical, repo-valid labels, ≥1 evidence citation |
| ia-02 | Duplicate Detection | Nearly identical open issue is flagged (`duplicates ≥ 1`) |
| ia-03 | Label Suggestions | Suggested labels ⊆ repository labels, non-empty |
| ia-04 | Milestone Suggestions | WIQ-V1-### token in retrieved roadmap evidence → milestone suggested |
| ia-05 | Acceptance Criteria | manual — human-scored per SCORING_GUIDE.md |
| ia-06 | Complexity Estimation | manual — human-scored per SCORING_GUIDE.md |

`ia-01` uses a dealer-approval crash issue so the expected evidence
(`backend/app/services/dealer_approval.py`) is what a real user would
retrieve; `ia-04` asserts milestone suggestion behaviour without pinning
which exact roadmap file must be cited.

## PR Review (6)

All cases submit the demo fixture PR (`waste-iq/demo#1`, see
`app/review/fixtures.py` — payments/analytics routes, test file, React
component) through the real deterministic rule engine.

| ID | Question | Rules that must fire |
|---|---|---|
| pr-01 | Review Sample PR | Findings across ≥6 categories, summary produced, all findings on diff files |
| pr-02 | Missing Tests | TEST-GAP, TEST-SKIP-NEW, TEST-SLEEP |
| pr-03 | Security Findings | SEC-EVAL |
| pr-04 | Architecture Findings | ARCH-ROUTE-DB |
| pr-05 | Performance Findings | PERF-NPLUS |
| pr-06 | Evidence Validation | Every finding cites a diff file (`out_of_diff = 0`) |

Note: the fixture exercises a *subset* of the rule registry. Rules like
SEC-SQL-INJECTION, SEC-PICKLE, SEC-SHELL, PERF-COMMIT-IN-LOOP are covered
by the rule unit tests, not by this fixture.

## Documentation Agent (5)

| ID | Question | Assertion |
|---|---|---|
| dc-01 | Generate Changelog | Conventional-commit title → Keep a Changelog section + entry referencing PR number |
| dc-02 | Summarize Pull Request | Proposal names the PR and lists changelog/doc actions |
| dc-03 | Explain Module | NotificationService retrievable (same query as rs-01) |
| dc-04 | Generate API Documentation | Route-touching PR → suggestion for `docs/API_SPECIFICATION.md` |
| dc-05 | Detect Documentation Drift | Model-touching PR → suggestion for `docs/DATABASE_SCHEMA.md` |

## LLM Layer (7)

| ID | Check | Assertion |
|---|---|---|
| ll-01 | Grounding Validation | Grounded response accepted (`supported=True`, `unsupported=0`) |
| ll-02 | Prompt Quality | System/user prompts embed evidence; secrets redacted |
| ll-03 | JSON Validation | Fenced JSON parses; malformed output raises `MalformedResponseError` |
| ll-04 | Cache Validation | Identical requests hash identically; cache hit/miss deterministic |
| ll-05 | Telemetry | Recorded calls/cache events appear in the snapshot |
| ll-06 | Provider Selection | Resolver selects the deterministic mock provider without credentials |
| ll-07 | Hallucination Rejection | Claim outside the evidence universe is rejected with `GroundingViolationError` |

## Adding a case

1. Append to the matching list in `agent/app/evaluation/cases.py` (or add a
   list for a new category and register a handler in
   `agent/app/evaluation/runner.py`).
2. Give it a unique `rs-`/`ar-`/`ia-`/`pr-`/`dc-`/`ll-` id and a payload the
   handler consumes.
3. Only use `mode="manual"` for behaviour the deterministic assistants do
   not produce yet (LLM prose).
4. Re-run `python scripts/run_evaluation.py` and confirm the case scores as
   expected; add/update unit tests in `tests/test_evaluation_*.py`.
