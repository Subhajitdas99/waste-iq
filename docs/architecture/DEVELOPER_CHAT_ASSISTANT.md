# Developer Chat Assistant — Design

> **Status:** ✅ Implemented (Phase 5, 2026-08)
> **Scope:** `agent/app/chat/` — conversational facade over the existing services
> **Related:** ADR-010 · `docs/architecture/AI_ENGINEERING_AGENT.md` (Phase 5 status)
> **Verification:** `docs/architecture/PHASE5_VERIFICATION_REPORT.md`

---

## 1. Purpose

The Developer Chat Assistant gives engineers a natural-language interface to the
repository: "Where is NotificationService?", "Review PR #1", "Generate an issue
draft for the login crash", "Explain the dealer approval workflow". Every answer
must be **grounded in repository evidence** and every question is routed to the
existing, already-verified services — nothing is re-implemented.

The chat layer is a **thin orchestration facade**. It does not replace the
Repository Context Service, PR Review Agent, Issue Assistant, Documentation
Agent, or Grounding Validator; it composes them.

## 2. Design principles

| Principle | Implementation |
|---|---|
| Deterministic intent detection | Keyword/pattern rules only — **no LLM classification**. Identical questions always yield identical intents, confidence, and answers. |
| Only the required evidence reaches the LLM | The planner picks the retrieval query, source types, and limit per intent; the chat layer never sends the whole repository. |
| Mandatory grounding | Evidence-requiring intents that produce zero references are rejected (`ChatNoEvidenceError`); the LLM layer's own grounding gate still rejects unsupported responses. |
| Bounded, non-vector memory | Conversations are in-process, max **10 turns** (`AGENT_CHAT_MAX_TURNS`), no persistence, no embeddings, no re-indexing. |
| Deterministic fallback | With no provider configured the LLM layer's `MockProvider` keeps the whole chat flow testable and offline-deterministic. |
| Security by default | Questions are length-limited and redaction-scanned before dispatch; request/correlation ids propagate; secrets never reach prompts. |
| Propose-only | The chat layer adds no write path; it only reads (retrieval, review, triage, docs). |

## 3. Components (`agent/app/chat/`)

| Module | Responsibility |
|---|---|
| `models.py` | `ChatRequest`, `FollowUpRequest`, `ChatReference`, `ChatResponse`, `ChatStatus`, typed errors (`ChatValidationError`, `ChatNoEvidenceError`, `ChatNotFoundError`), `IntentName` literal. |
| `intent.py` | `detect_intent()` — ordered keyword rules (most specific first), confidence `min(0.99, base + 0.02 × matches)`, subject extraction (stopwords + matched keywords stripped). |
| `planner.py` | `plan_for()` — intent → retrieval plan + agent dispatch (`llm_explain`, `llm_summarize`, `issue_assistant`, `doc_assistant`, `review_agent`, `none`), plus the capabilities `help_answer()`. |
| `context_builder.py` | Retrieved chunks → `RepositoryContext` buckets (files/docs/ADRs/roadmap), evidence entries and chat citations in the exact `grounding` id formats (`code:path:line`, `doc|adr|roadmap:path:start-end`). |
| `response.py` | Raw agent output → `ChatResponse` (evidence refs, triage evidence, review context refs). |
| `orchestrator.py` | End-to-end `handle()`: detect → plan → retrieve → dispatch → latency/grounding check. |
| `service.py` | Sanitization, conversation memory, intent statistics, status aggregation. |
| `memory.py` / `conversation.py` | Thread-safe bounded `MemoryStore`; `ConversationTurn`, `Conversation`, `resolve_query()` follow-up reuse. |
| `router.py` | `POST /api/chat`, `POST /api/chat/followup`, `GET /api/chat/status`. |

## 4. Intent → plan → agent mapping

| Intent | Retrieval | Agent |
|---|---|---|
| `explain_architecture` | all source types, query + "architecture" | `llm_explain` |
| `explain_code` | code only | `llm_explain` |
| `find_implementation` | code only | `llm_explain` |
| `repository_search` | all source types | `llm_explain` |
| `summarize_changes` | all source types | `llm_summarize` |
| `generate_issue` | all source types (triage evidence) | `issue_assistant` |
| `generate_documentation` | all source types (touched files) | `doc_assistant` |
| `review_pr` | limit 2 (fallback repo `waste-iq/demo`) | `review_agent` + `llm_analyze` |
| `unknown` | none | capabilities help text |

Follow-ups: when a question carries no subject (e.g. "what does it do?"), the
planner reuses the previous turn's `search_query` so the follow-up resolves
against the same evidence (`notes: ["follow-up: …"]`).

## 5. Endpoints

| Endpoint | Behavior |
|---|---|
| `POST /api/chat` | Answer a question; `conversation_id` optional (fresh conversation when omitted). `X-Request-ID` header becomes the `correlation_id`. |
| `POST /api/chat/followup` | Answer against an existing conversation; unknown id → 404. |
| `GET /api/chat/status` | Provider, configured, model, cache backend/hits, conversation counts, `intent_counts`. |

Error mapping (`router._consider`): validation 422 · no evidence 422 ·
unknown conversation 404 · `ReviewUnavailable` 422 · LLM-layer errors via the
existing `llm._consider` (429/502/503/504) · anything else 502.

## 6. Configuration (`AGENT_CHAT_*`)

| Setting | Default | Meaning |
|---|---|---|
| `agent_chat_enabled` | `true` | Master switch |
| `agent_chat_max_turns` | `10` | Conversation memory bound |
| `agent_chat_retrieval_limit` | `6` | Chunks per retrieval |
| `agent_chat_max_question_chars` | `4000` | Question length cap (matches `ChatRequest` validation) |
| `agent_chat_repository` | `waste-iq` | Default repository for LLM requests |

## 7. Security

- Questions are scanned with the LLM layer's `Redactor` (secret shapes rejected
  before dispatch).
- Oversized questions are rejected before any retrieval or LLM call.
- Prompts are built exclusively from retrieved evidence, never the whole repo
  (ADR-009).
- The chat layer performs no writes and holds no credentials.

## 8. Test coverage

`app/chat/` is covered by 100 tests (intent, planner, memory, context builder,
response assembly, orchestrator integration against real services, service,
API). Coverage on `app/chat/`: **100 %** (pytest-cov). Full suite: 685 passing.
