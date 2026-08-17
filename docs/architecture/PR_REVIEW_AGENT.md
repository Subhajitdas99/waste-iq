# PR Review Agent — Phase 2 Design & Implementation

> **Status:** ✅ Implemented (Phase 2 of the AI Engineering Agent)
> **Scope:** `agent/app/review/` — deterministic, evidence-backed pull request review
> **Related:** `docs/architecture/AI_ENGINEERING_AGENT.md` (§3.5), ADR-008

---

## 1. Purpose

The PR Review Agent analyzes pull requests — metadata + unified diff + head file
contents — and produces a structured, **evidence-backed review**: per-file findings
with rule IDs, severities, line anchors, code snippets, suggestions, confidence
scores, and references into the repository knowledge base (files, docs, ADRs,
roadmap, similar code).

It is **fully deterministic** (no LLM calls in Phase 2), so every run is
reproducible and testable. The rule catalog and the analysis pipeline live in the
repository and are versioned with the code.

## 2. Non-negotiable behavior

- **Read-only.** The agent never comments, never merges, never approves, never
  edits code, never opens PRs. It only reads GitHub (metadata, diff, files) via a
  short-lived installation token.
- **Evidence before findings.** Every finding must be grounded in the diff or in
  repository content retrieved through the Phase 1 Context Service. Anything
  without evidence is excluded rather than guessed.
- **Humans stay in charge.** Reviews are returned as objects; acting on them is a
  human decision.

## 3. Package layout

```text
agent/app/review/
├── __init__.py            # version 2.0.0
├── review_models.py       # typed review domain: diff, findings, summary, PR review
├── diff.py                # unified-diff parser (added/modified/renamed/removed, exact lines)
├── review_prompts.py      # rule catalog (~28 rules) + per-category guidelines
├── review_engine.py       # deterministic analyzers (AST + line + cross-file)
├── review_context.py      # RepositoryProbe — grounding via Phase 1 hybrid search
├── pr_provider.py         # GitHub (read-only) + fixture providers
├── fixtures.py            # built-in demo PR used by tests and smoke runs
├── review_agent.py        # fetch PR → run engine → build PRReview
├── review_repository.py   # persistence (sessions, findings, evidence)
├── review_service.py      # application service + webhook dispatch
└── review_formatter.py    # markdown / console formatting
```

## 4. Rule catalog

Rules are declared in `review_prompts.py` as `RuleDefinition` records
(`rule_id`, `category`, `severity`, `guidance`, `fix`, `base_confidence`,
`languages`). Categories (9):

| Category | Example rules |
|---|---|
| correctness | mutable default args, bare except, `== None`, `while True` without exit, JS loose equality |
| security | `eval`/`exec`, SQL injection, pickle, hard-coded secrets, shell injection, XSS |
| performance | N+1 queries, commits inside loops, string concatenation in loops |
| fastapi | handler signature missing a declared path parameter, blocking calls in endpoints |
| sqlalchemy | sync SQLAlchemy calls in async context, lazy-load in async |
| react | missing/invalid `key=`, `target="_blank"` without `rel`, `dangerouslySetInnerHTML`, legacy lifecycle |
| architecture | route modules importing DB layer directly, oversized files |
| testing | changed modules without tests, `time.sleep` in tests, new tests skipped |
| documentation | missing docstrings, PR not referencing roadmap/issues |

## 5. Evidence model

Every `ReviewFinding` carries:

```text
rule_id, category, severity, title, explanation
file_path, start_line, end_line, snippet, suggestion, confidence
related_adrs[], related_files[], evidence[] (kind, reference, content, confidence)
```

`evidence` entries are one of `code | context | adr | doc | roadmap | similar |
test | coverage` — always resolvable to a `path:line` or repository document.

## 6. Engine pipeline

1. **Fetch** (`pr_provider`) — metadata + diff via the GitHub API; file list from
   `/pulls/{n}/files`, full head content from `/contents/{path}?ref={sha}`. Falls
   back to parsing the unified diff when the file list is empty. Retries on
   429/5xx; 404 → `ReviewUnavailable`.
2. **Analyze** (`review_engine`) — per changed file (added/modified/renamed;
   removed files are skipped):
   - Python files: `ast` parse with **added-line gating** (findings only on lines
     actually added), fallback to regex checks when the file does not parse.
   - Line-level regex tables for security, correctness, React patterns.
   - FastAPI route signature inspection.
   - Cross-file checks: test-gap detection (known test files from the index),
     PR-reference check, oversized files.
   - Caps: max files (100), max findings per file (25), confidence floor (0.4);
     dedupe by `(rule_id, file_path, start_line)`.
3. **Ground** (`review_context.RepositoryProbe`) — related files (namespace),
   docs, ADR, roadmap, similar code via Phase 1 hybrid search; tracks query/ref
   metrics.
4. **Summarize** — `ReviewSummary` (totals, per-category/per-severity counts,
   per-category top severity), `ReviewMetrics` (files, lines, queries, references,
   duration), disclaimers.

## 7. API & integration

| Endpoint / hook | Behavior |
|---|---|
| `POST /api/review/pr` | `ReviewRequest {repository, pr_number}` → `PRReview` (422 on unavailable); `x-request-id` → correlation id |
| `GET /api/review/status` | enabled/engine version/session and finding statistics |
| `GET /api/review/sessions` | recent review sessions |
| `GET /api/review/sessions/{id}` | session detail incl. metrics |
| Webhook `pull_request` (opened/synchronize/reopened/ready_for_review) | runs a review; response gains `review: {session_id, findings_count}` |
| Webhook `workflow_run.completed` | finds the open PR for the head branch, then reviews it |

Dispatch is gated by `AGENT_REVIEW_ENABLED` + `AGENT_REVIEW_AUTO_RUN`; a failed
review never fails the webhook acknowledgement. Persistence: `review_sessions`,
`review_findings`, `review_evidence` (migration `0002_review`, chained from
`0001_initial`). Sessions are idempotent per `X-GitHub-Delivery`.

## 8. Configuration (additive)

| Setting | Default |
|---|---|
| `AGENT_REVIEW_ENABLED` | `true` |
| `AGENT_REVIEW_AUTO_RUN` | `true` |
| `AGENT_REVIEW_FIXTURE_REPO` | `waste-iq/demo` |
| `AGENT_REVIEW_ENGINE_VERSION` | `2.0.0` |
| `AGENT_REVIEW_MAX_FILES` | `100` |
| `AGENT_REVIEW_MAX_LINES_PER_FILE` | `3000` |
| `AGENT_REVIEW_MAX_FINDINGS_PER_FILE` | `25` |
| `AGENT_REVIEW_CONFIDENCE_FLOOR` | `0.4` |
| `AGENT_REVIEW_FIND_PULL_REQUEST` | `true` |
| `AGENT_GITHUB_API_BASE_URL` | `https://api.github.com` |

## 9. Demo fixture

`AGENT_REVIEW_FIXTURE_REPO` (`waste-iq/demo`) is served by
`FixturePullRequestProvider` — a 4-file PR (payments.py, analytics.py,
test_payments.py, PaymentList.jsx) that deliberately exercises all 9 categories
(22 findings: critical=1, high=3, medium=10, low=8) and is used by the test suite
and local smoke runs. This keeps CI hermetic: no network, no live GitHub.
