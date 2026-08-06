# Waste-IQ Architecture Decisions (ADR)

> **Status:** Active living document
> **Owner:** Lead AI Engineer (maintained by the Architecture Agent)
> **Purpose:** Record engineering decisions (ADRs) and the architectural principles the
> Waste-IQ team commits to. The **Architecture Agent** uses this file as its authoritative
> ruleset to detect and report architectural drift.
> **Convention:** New decisions are appended as new entries. Decisions are never deleted —
> only superseded (mark the old entry `Superseded by ADR-0XX`).

---

## Principles (non-negotiable)

P1. **Human in the loop for all AI writes.** Automated tooling may propose, review, and
    patch, but **nothing merges, publishes, or reconfigures without explicit human approval**.
P2. **Layered modularity with clean boundaries.** Code is organized as
    `api (routes) → services (business logic) → repositories (data access) → models`, with
    schemas as the transport contract. Cross-layer imports are forbidden (see ADR-001).
P3. **Security by default.** Authentication, authorization, input validation, and secrets
    handling are enforced centrally (`core/security.py`, `core/dependencies.py`) and never
    reimplemented ad hoc.
P4. **Test coverage as a gate.** Backend requires ≥ 80 % coverage in CI; new behavior ships
    with tests (pytest for backend, Vitest for frontend).
P5. **Type safety and lint discipline.** Backend is Python 3.12 with ruff + black + mypy
    enforced in CI; frontend is strict TypeScript with ESLint. Formatting is not optional.
P6. **Documentation is code.** Architectural decisions, API specs, database schema, and
    roadmap live in `docs/` and must be updated in the same PR as the change they describe.
P7. **Env-driven configuration.** All configuration flows through `pydantic-settings`
    (`Settings` classes with env aliases). No hard-coded secrets, URLs, or feature flags in
    application code.
P8. **Event-driven, idempotent automation.** Automation reacts to GitHub webhook events,
    records every run, and tolerates duplicate delivery.

---

## Decision Log

### ADR-001 — Backend layered architecture
**Status:** Accepted · **Date:** 2025-06 · **Scope:** backend/app

- Context: The API grew feature modules (auth, marketplace, collector, dealer, pickup
  requests) and needed a consistent structure.
- Decision: Enforce `api/routes → services → repositories → models` with Pydantic schemas as
  the only cross-layer payload type. Routes handle HTTP concerns; services hold business
  logic; repositories own SQLAlchemy queries. Use Alembic for all schema migrations (never
  hand-written DDL).
- Consequences: Predictable review surface; architecture violations are machine-detectable by
  import rules. Added indirection is worth the maintainability.

### ADR-002 — Frontend stack: React 19 + Vite + TypeScript + Tailwind
**Status:** Accepted · **Date:** 2025-06 · **Scope:** frontend

- Context: Needed a fast, typed SPA matching backend feature velocity.
- Decision: React 19 SPA built with Vite 5, strict TypeScript, Tailwind CSS 3 with
  shadcn/ui-style Radix primitives; TanStack Query + axios for server state; React Router for
  routing; Vitest + Testing Library + MSW for tests (no E2E in v1).
- Consequences: High DX, small bundle control via Vite; MSW keeps tests hermetic. Server state
  must live in the query client, not redux-style stores.

### ADR-003 — GitHub Projects (v2) drives delivery, not spreadsheets
**Status:** Accepted · **Date:** 2026-08 · **Scope:** project management

- Context: Milestones M0–M4, 26 labels, and 23 roadmap issues exist on the "Waste-IQ v1.0"
  project; the AI agent must read from, but never reconfigure, this source of truth.
- Decision: The GitHub Project (v2) "Waste-IQ v1.0" is the authoritative roadmap. AI-assisted
  tools read milestone/label/status via GraphQL and treat project configuration as
  read-only.
- Consequences: One source of truth; agent automation cannot orphan issues or drift from the
  roadmap.

### ADR-004 — AI assistance is propose-only by default
**Status:** Accepted · **Date:** 2026-08 · **Scope:** AI Engineering Agent

- Context: The AI Engineering Agent automates issue triage, PR review, tests, docs, CI
  diagnosis, quality, and releases.
- Decision: All agent write behavior defaults to **propose-only** (comments/reports). Code
  changes require explicit human approval via the `/agent approve` protocol. The agent holds
  **no merge permission** and never writes to `main`/`develop`.
- Consequences: Safe automation with a clear audit trail; merge remains a human, CI-verified
  act.

### ADR-005 — GitHub App installation tokens, never PATs
**Status:** Accepted · **Date:** 2026-08 · **Scope:** AI Engineering Agent

- Context: The agent needs scoped API access without a long-lived personal token.
- Decision: The agent authenticates as a GitHub App scoped to `waste-iq`, with least-privilege
  permissions, issuing short-lived installation tokens (1 h) from an RS256-signed app JWT held
  in deployment secrets.
- Consequences: Tokens self-rotate and are discarded; no shared credential; scope limits blast
  radius.

### ADR-006 — Repository Knowledge Base via vector index (Qdrant or pgvector)
**Status:** Accepted · **Date:** 2026-08 · **Scope:** AI Engineering Agent

- Context: Assistants need precise, evidence-backed repository retrieval (code, docs, ADRs)
  with `path:line` grounding.
- Decision: Index repo-owned content into a **vector store** (Qdrant if a dedicated service is
  acceptable; pgvector if reusing the existing PostgreSQL). Hybrid retrieval (semantic +
  keyword) returns anchored evidence. Only repo-owned files are indexed; untrusted webhook/issue
  text is never embedded.
- Consequences: Higher-quality retrieval; small infra addition. Index builds are triggered by
  events, never by LLM output.

### ADR-007 — Assistants are built incrementally in dependency order
**Status:** Accepted · **Date:** 2026-08 · **Scope:** AI Engineering Agent

- Context: Nine assistants were specified; building all at once creates an un-reviewable
  change.
- Decision: Build sequence: GitHub App & Webhooks → Repository Context Service → PR Review →
  Issue → Docs → CI Failure → Test → Code Quality → Architecture → Release. Each slice is
  complete, tested, and reviewed before the next begins. Phase 0 (GitHub App & Webhooks) is
  the current slice.
- Consequences: Small reviewable increments; infrastructure is proven before intelligence is
  layered on.

### ADR-008 — PR review is deterministic and evidence-backed first (no writes)
**Status:** Accepted · **Date:** 2026-08 · **Scope:** AI Engineering Agent (Phase 2)

- Context: The PR Review Agent must deliver correct, auditable reviews before any LLM prose or
  write path is introduced.
- Decision: Phase 2 review is fully deterministic — a versioned rule catalog (9 categories,
  ~28 rules) analyzed over the PR diff + head file contents with AST and regex checks, plus
  grounding from the Phase 1 repository index (files/docs/ADR/roadmap/similar code). Every
  finding carries a rule id, severity, line anchors, snippet, suggestion, confidence and
  evidence; anything without evidence is excluded. The agent holds read-only GitHub access
  (installation token), never comments/merges/edits, and exposes `POST /api/review/pr` +
  status/session endpoints plus webhook dispatch (`pull_request`, `workflow_run.completed`).
- Consequences: Reproducible, testable reviews with zero write risk; LLM prose and inline
  review comments are deferred to a later phase behind the same review pipeline.

### ADR-009 — LLM is an evidence-grounded assistant, not a decision maker
**Status:** Accepted · **Date:** 2026-08 · **Scope:** AI Engineering Agent (Phase 2.5)

- Context: After the deterministic PR Review Agent (Phase 2), the next step is to introduce
  LLM-powered natural language reasoning (explain, summarize, prioritize). The risk is that
  LLM output contains hallucinated file paths, invented findings, or unsupported claims —
  all of which would undermine the trust model established by Phases 0–2.
- Decision: Introduce a **provider-agnostic LLM Intelligence Layer** (`agent/app/llm/`) that
  wraps every provider call in a mandatory grounding gate. Prompts are constructed only from
  retrieved evidence (never from the whole repository). Every response is validated against
  an **evidence universe** derived exclusively from Review Engine findings and Repository
  Context Service output. Responses containing unverifiable references are **rejected**
  before the caller sees them. When no provider is configured, a deterministic `MockProvider`
  runs in-process so the system degrades gracefully with zero LLM dependency. The layer
  supports five providers (`openai`, `anthropic`, `google`, `ollama`, `mock`) selectable via
  `AGENT_LLM_PROVIDER`. Caching (memory/SQLite/Redis), telemetry (latency/cost/tokens/
  retries/Prometheus), timeout, retry-with-backoff, and in-process rate limiting are built in.
  The LLM layer **never** posts comments, approves PRs, merges, or generates code.
- Consequences: LLM prose reasoning is now available to any assistant without relaxing the
  evidence discipline established in Phases 1–2. Adding a new provider requires implementing
  one `complete()` method. Coverage ≥ 99 % (895 statements) enforced in CI.
  See `docs/architecture/LLM_INTELLIGENCE_LAYER.md` for full design.

### ADR-010 — Chat is a deterministic orchestrator, not another assistant
**Status:** Accepted · **Date:** 2026-08 · **Scope:** AI Engineering Agent (Phase 5)

- Context: Engineers want natural-language access to the repository ("where is
  NotificationService?", "review PR #1", "generate an issue draft") without a new
  intelligence stack or a second opinion that can contradict the reviewed agents.
- Decision: The Developer Chat Assistant (`agent/app/chat/`) is a thin,
  deterministic orchestration facade over the existing services. Intent detection
  is keyword/pattern based (no LLM classification); the planner maps intent to a
  retrieval plan (query, source types, limit) and exactly one existing agent
  (LLM explain/summarize, Issue Assistant, Documentation Agent, PR Review Agent).
  Every evidence-requiring answer must carry repository references — answers
  without evidence are rejected before the caller sees them, and the existing
  Grounding Validator (ADR-009) still rejects unsupported LLM responses.
  Conversation memory is in-process, bounded to 10 turns, with no vector memory
  and no re-indexing. Inputs are length-limited and redaction-scanned.
- Consequences: Chat inherits the evidence discipline of Phases 1–4.5 unchanged;
  new capabilities require only a new intent rule + planner row, never a new
  assistant. Deterministic detection keeps tests fast and offline (mock provider).
  See `docs/architecture/DEVELOPER_CHAT_ASSISTANT.md` for the full design.

---

## Drift Checks Enforced by the Architecture Agent

The Architecture Agent continuously verifies the repository against this file. Reported as
findings when violated:

| Check | Rule source | Example violation |
|---|---|---|
| Layer imports | ADR-001 | route importing repository directly, skipping service |
| No hand-written DDL | ADR-001 | raw `CREATE TABLE` in app code |
| Env-driven config | P7, ADR-002 | hard-coded URL or secret literal |
| Merge discipline | ADR-004 | code path calling merge APIs |
| Test presence for new logic | P4 | shipped module with 0 tests |
| Docs updated with code | P6 | PR touching schema without doc change |
| No PAT/token leakage | ADR-005, P3 | credential string in committed code |
| Event idempotency | P8 | automation lacking delivery dedup |