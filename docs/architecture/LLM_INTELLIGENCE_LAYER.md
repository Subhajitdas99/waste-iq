# LLM Intelligence Layer — Architecture

> **Status:** ✅ Implemented (Phase 2.5, extended Phase 5.1 — OpenRouter provider)
> **Owner:** Lead AI Engineer
> **Phase:** 2.5 — LLM Intelligence Layer · 5.1 — OpenRouter provider
> **Related:** `agent/app/llm/`, `docs/architecture/ADR-009`, Phase 2 (PR Review Agent), Phase 5 (Developer Chat Assistant)

---

## 1. Purpose

The **LLM Intelligence Layer** introduces a provider-agnostic, repository-grounded reasoning
capability to the Waste-IQ AI Engineering Agent. It enhances the deterministic PR Review
Agent with the ability to explain, summarize, prioritize, and classify findings — without
replacing any deterministic analysis.

> **Core principle:** The LLM is an *assistant*, not a *decision maker*.
> All conclusions remain grounded in repository evidence. The LLM may never invent
> repository facts, fabricate file references, create findings without evidence, approve
> PRs, or merge PRs.

---

## 2. Design Principles

| Principle | Detail |
|---|---|
| **Evidence-only prompts** | Prompts are constructed exclusively from retrieved evidence. The entire repository is never included. |
| **Grounding-before-acceptance** | Every LLM response is validated against the evidence universe. Unverifiable references are rejected. |
| **Deterministic fallback** | When no provider is configured, the MockProvider delivers a deterministic, grounded response — no LLM calls, no failures. |
| **No writes** | The LLM layer never comments, merges, or modifies anything. It only reasons. |
| **Security-first** | All prompts are automatically redacted before dispatch. Token limits and timeouts apply unconditionally. |

---

## 3. Component Overview

```
agent/app/llm/
├── __init__.py         — public surface: LLMService
├── models.py           — Pydantic schemas (requests, responses, errors, telemetry)
├── provider.py         — Provider abstraction + registry + MockProvider
├── client.py           — Concrete HTTP clients (OpenAI, Anthropic, Gemini, Ollama)
├── providers/
│   ├── __init__.py     — Provider sub-package
│   └── openrouter.py   — OpenRouter client (Phase 5.1, OpenAI-compatible API)
├── prompt_builder.py   — Evidence-grounded, redacted prompt construction
├── response_parser.py  — Strict JSON extraction + Pydantic validation
├── grounding.py        — Evidence universe + grounding validation gate
├── cache.py            — Memory / SQLite / Redis cache backends
├── telemetry.py        — Latency, token usage, cost, failure, retries, Prometheus
└── service.py          — Orchestration: build → cache → call → parse → ground → record
```

---

## 4. Provider Abstraction

### 4.1 Protocol

```python
class LLMProvider(Protocol):
    name: str
    def complete(self, request: ProviderRequest) -> ProviderResponse: ...
```

All concrete providers (`OpenAIProvider`, `AnthropicProvider`, `GeminiProvider`,
`OllamaProvider`, `OpenRouterProvider`) implement this protocol. The `MockProvider` is
always available as the deterministic fallback.

### 4.2 Provider Matrix

| Provider | Key required | Default model | Base URL |
|---|---|---|---|
| `openai` | `AGENT_LLM_API_KEY` / `AGENT_OPENAI_API_KEY` | `gpt-4o-mini` | `https://api.openai.com/v1` |
| `anthropic` | `AGENT_LLM_API_KEY` / `AGENT_ANTHROPIC_API_KEY` | `claude-3-5-haiku-latest` | `https://api.anthropic.com` |
| `google` | `AGENT_LLM_API_KEY` / `AGENT_GOOGLE_API_KEY` | `gemini-2.0-flash` | `https://generativelanguage.googleapis.com/v1beta` |
| `ollama` | none (local) | `llama3.2` | `http://localhost:11434` |
| `openrouter` | `AGENT_OPENROUTER_API_KEY` | `openai/gpt-4o-mini` | `https://openrouter.ai/api/v1` |
| `mock` | none | `mock-model` | in-process |

### 4.2.1 OpenRouter (Phase 5.1)

`OpenRouterProvider` (`app/llm/providers/openrouter.py`) speaks the OpenAI-compatible
Chat Completions API (`POST /chat/completions`) and accepts any model id that OpenRouter
routes, e.g. `openai/gpt-4o-mini`, `anthropic/claude-3.5-haiku`, `meta-llama/llama-3.3-70b-instruct`.

- **Authentication:** `Authorization: Bearer <AGENT_OPENROUTER_API_KEY>`.
- **Attribution headers (optional):** `HTTP-Referer` (site URL) and `X-Title` (app name)
  from `AGENT_OPENROUTER_HTTP_REFERER` / `AGENT_OPENROUTER_APP_NAME` — required by the
  OpenRouter free-tier policy and good practice for paid tiers.
- **Endpoint override:** `AGENT_OPENROUTER_BASE_URL` (default `https://openrouter.ai/api/v1`),
  useful for proxies or regional routing.
- **Shared behavior:** the provider reuses the common HTTP client helpers in
  `client.py` (`_send_single`, `_estimate_tokens`), so timeout/retryable/error
  semantics, telemetry aggregation (`provider=openrouter`), caching
  (`hash_request` already includes provider + model + prompt), and rate limiting
  behave identically to the other providers — no special cases anywhere else.
- **Selection:** `AGENT_LLM_PROVIDER=openrouter` + a set key resolves to
  `OpenRouterProvider`; without the key the agent falls back to `MockProvider`.
  Unknown provider names raise `LLMNotConfigured` with a clear message listing the
  valid providers.

### 4.3 Selection Logic

```
AGENT_LLM_PROVIDER = "openai"  # but no API key set
  → resolve_provider() detects unconfigured
  → fallback to MockProvider (deterministic_fallback = True)
```

`build_provider()` and `provider_for_name()` handle both the default and per-request
provider overrides. The `providers_info()` function populates `GET /api/llm/providers`.

---

## 5. Prompt Builder

`PromptBuilder` constructs grounded, redacted prompts from:

- **Repository Context** — related files, docs, ADRs, roadmap entries, similar code
- **Review Findings** — rule id, severity, category, title, explanation, snippet
- **Role instructions** — `analyze`, `explain`, `summarize`
- **JSON schema** — injected into the system prompt; the LLM must emit exactly this shape

### 5.1 What is never included

- The complete repository file tree
- Files not retrieved by the evidence query
- Secrets, tokens, credentials (all redacted before prompt construction)

### 5.2 Evidence Block Format

```
# EVIDENCE (the only files/lines you may reference):
- evidence_id: code:src/app.py:10 | chunk_id: chunk:src/app.py:10
  | file: src/app.py | lines: 10-20 | source: code
  | <redacted snippet>
```

### 5.3 Redaction

`Redactor` scrubs the following shapes before any text enters a prompt:

- PEM private keys (`BEGIN PRIVATE KEY`, `BEGIN OPENSSH PRIVATE KEY`)
- Bearer tokens (JWT and generic)
- GitHub tokens (`ghp_`, `gho_`, `ghu_`, `ghs_`, `ghr_`)
- OpenAI API keys (`sk-…`)
- AWS access keys (`AKIA…`)
- Google API keys (`AIza…`)
- Password/secret assignments (`password = …`, `api_key: …`)
- Session IDs
- `Authorization`/`Proxy-Authorization`/`X-Api-Key` headers

---

## 6. Grounding

Every LLM response passes through `grounding.validate()` before it is returned to the
caller. The **evidence universe** is built exclusively from:

- `ReviewFinding` entries supplied by the deterministic Review Engine
- `RepositoryContext` retrieved by the Phase 1 Repository Context Service

### 6.1 Validation Rules

| Rule | Rejection message |
|---|---|
| Response references a file not in the evidence universe | `unsupported reference <path>:<start>-<end>` |
| Response references line range not overlapping evidence | `unsupported reference <path>:<start>-<end>` |
| Claim carries zero references | `claim without evidence: <claim[:120]>` |
| Claim references unverifiable file/lines | `unsupported claim reference <path>:<start>-<end>` |
| Response has zero references when `require_references=True` | `response contains no references to repository evidence` |

Violations → `GroundingViolationError` → `HTTP 422 Unprocessable Entity`.

---

## 7. Response Parser

`ResponseParser.parse()` accepts raw provider output and:

1. Extracts the first JSON object (handles bare JSON, markdown fences, prose wrapper)
2. Validates against the role-specific Pydantic schema (`extra="forbid"`)
3. Returns a typed `AnalyzeResponse`, `ExplainResponse`, or `SummarizeResponse`
4. Raises `MalformedResponseError` on any parsing or validation failure

### 7.1 Role Schemas

| Role | Required keys |
|---|---|
| `analyze` | `summary`, `priorities[]`, `recommendations[]`, `risks[]`, `confidence`, `references[]` |
| `explain` | `explanation`, `confidence`, `references[]` |
| `summarize` | `overview`, `key_points[]`, `confidence`, `references[]` |

All schemas share the optional `claims[]` list for fine-grained claim-level grounding.

---

## 8. Caching

`cache.build_cache()` selects a backend from `AGENT_LLM_CACHE_BACKEND`:

| Backend | Key | Notes |
|---|---|---|
| `memory` | in-process dict | TTL via monotonic clock. Default for tests. |
| `sqlite` | `AGENT_LLM_CACHE_PATH` | WAL mode, thread-safe, durable across restarts |
| `redis` | `AGENT_LLM_REDIS_URL` | Requires optional `redis` package; falls back to memory |

Cache keys are computed by `hash_request()`:

```python
key = SHA-256(provider + "\x1f" + model + "\x1f" + normalize(system_prompt) + "\x1f" + normalize(user_prompt))
```

Whitespace is normalized before hashing so prompts that differ only in line endings
produce the same key.

---

## 9. Telemetry

`Telemetry` tracks per-provider aggregates in-memory (thread-safe):

| Metric | Field |
|---|---|
| Total calls | `total_calls` |
| Failed calls | `failed_calls` |
| Retry count | `retries` |
| Average latency (ms) | `average_latency_ms` |
| Prompt tokens | `total_prompt_tokens` |
| Completion tokens | `total_completion_tokens` |
| Estimated cost | `estimated_cost` |
| Cache hits / misses | `cache_hits`, `cache_misses` |

`Metrics` publishes optional Prometheus counters/gauges when `AGENT_ENABLE_PROMETHEUS=true`:

- `agent_llm_calls_total{provider}` — counter
- `agent_llm_failures_total{provider}` — counter
- `agent_llm_cache_hits_total` — counter
- `agent_llm_cache_misses_total` — counter
- `agent_llm_tokens_total{kind}` — gauge

---

## 10. Service Orchestration

`LLMService._run()` coordinates the full call path:

```
build prompt (evidence + redaction)
  → check cache (skip provider call on hit)
  → check rate limit (RateLimiter: sliding-window, per-minute)
  → build evidence universe
  → call provider with retries (exponential back-off)
  → parse JSON response (Pydantic validation)
  → validate grounding (reject unverifiable claims)
  → record telemetry (latency, tokens, cost, retries)
  → store in cache
  → decorate with provider/model/correlation_id/latency_ms
  → return typed response
```

### 10.1 Retry Policy

| Setting | Default |
|---|---|
| `AGENT_LLM_MAX_RETRIES` | 2 |
| `AGENT_LLM_RETRY_BACKOFF_SECONDS` | 0.5 |
| Retryable conditions | HTTP 429, 500, 502, 503, 504; network errors |
| Non-retryable | 4xx (other than 429), timeout, malformed response |

### 10.2 Rate Limiter

In-process sliding-window limiter: `AGENT_LLM_RATE_LIMIT_PER_MINUTE` (default 120/min).
Exceeded → `RateLimitedError` → `HTTP 429`.

---

## 11. Security Controls

| Control | Implementation |
|---|---|
| Secret redaction | `Redactor` scrubs 10+ secret shape patterns before any prompt is sent |
| Token limits | `AGENT_LLM_MAX_INPUT_TOKENS` (default 14000) caps prompt size via `_cap()` |
| Output limits | `AGENT_LLM_MAX_OUTPUT_TOKENS` (default 1500) passed as `max_tokens` |
| Timeout | `AGENT_LLM_TIMEOUT_SECONDS` (default 60s) enforced per HTTP call |
| Rate limiting | 120 calls/min default, configurable via settings |
| No credentials in prompts | API keys are injected as HTTP headers only, never in prompt text |
| Schema enforcement | `extra="forbid"` on all Pydantic models; injected keys rejected |

---

## 12. APIs

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/llm/analyze` | Analyze findings + context; returns grounded `AnalyzeResponse` |
| `POST` | `/api/llm/explain` | Answer a question grounded in evidence; returns `ExplainResponse` |
| `POST` | `/api/llm/summarize` | Summarize findings + context; returns `SummarizeResponse` |
| `GET` | `/api/llm/providers` | List all providers with configuration status |
| `GET` | `/api/llm/status` | LLM health, config, and cumulative telemetry |

All endpoints accept `X-Request-Id` header for correlation. Errors map to standard HTTP
status codes: 422 (grounding violation), 429 (rate limit), 503 (not configured),
504 (timeout), 502 (provider error / malformed response).

---

## 13. Observability

| Signal | Mechanism |
|---|---|
| Request IDs | `X-Request-Id` header echoed on all responses via `RequestIDMiddleware` |
| Correlation IDs | Passed through `LLMService` to `TraceContext`; attached to structured log lines |
| Structured logs | Python `logging` with key=value context (`role`, `provider`, `correlation_id`, `redactions`) |
| Prometheus metrics | Optional `Metrics` class, gated by `AGENT_ENABLE_PROMETHEUS` |
| Telemetry snapshot | `GET /api/llm/status` exposes the live `LLMStatus` model |

---

## 14. Configuration Reference

All settings are read via `pydantic-settings` with `AGENT_LLM_*` env aliases:

| Variable | Default | Purpose |
|---|---|---|
| `AGENT_LLM_ENABLED` | `true` | Master switch. Disabled → 503 on all calls. |
| `AGENT_LLM_PROVIDER` | `mock` | Provider name (mock/openai/anthropic/google/ollama/openrouter) |
| `AGENT_LLM_MODEL` | `""` | Override model name (provider default used if empty) |
| `AGENT_LLM_API_KEY` | `""` | Shared API key (used by whichever cloud provider is active) |
| `AGENT_OPENAI_API_KEY` | `""` | OpenAI-specific key (preferred over shared) |
| `AGENT_ANTHROPIC_API_KEY` | `""` | Anthropic-specific key |
| `AGENT_GOOGLE_API_KEY` | `""` | Google Gemini-specific key |
| `AGENT_OPENROUTER_API_KEY` | `""` | OpenRouter key (`sk-or-…`); presence enables the provider |
| `AGENT_OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | OpenRouter endpoint override |
| `AGENT_OPENROUTER_HTTP_REFERER` | `""` | `HTTP-Referer` attribution header (site URL) |
| `AGENT_OPENROUTER_APP_NAME` | `""` | `X-Title` attribution header (app name) |
| `AGENT_LLM_BASE_URL` | provider default | Override base URL (e.g. Azure proxy) |
| `AGENT_LLM_TIMEOUT_SECONDS` | `60.0` | Per-call HTTP timeout |
| `AGENT_LLM_MAX_RETRIES` | `2` | Retryable failures before raising |
| `AGENT_LLM_RETRY_BACKOFF_SECONDS` | `0.5` | Backoff multiplier (attempt × backoff) |
| `AGENT_LLM_MAX_INPUT_TOKENS` | `14000` | Prompt token budget (soft cap) |
| `AGENT_LLM_MAX_OUTPUT_TOKENS` | `1500` | Completion token limit |
| `AGENT_LLM_TEMPERATURE` | `0.0` | Sampling temperature |
| `AGENT_LLM_CACHE_ENABLED` | `true` | Enable/disable response caching |
| `AGENT_LLM_CACHE_BACKEND` | `sqlite` | `memory` / `sqlite` / `redis` |
| `AGENT_LLM_CACHE_PATH` | `agent_llm_cache.db` | SQLite file path |
| `AGENT_LLM_CACHE_TTL_SECONDS` | `3600` | Cache entry lifetime |
| `AGENT_LLM_REDIS_URL` | `""` | Redis connection URL |
| `AGENT_LLM_RATE_LIMIT_PER_MINUTE` | `120` | In-process sliding-window rate cap |
| `AGENT_LLM_COST_INPUT_PER_1M` | `2.5` | Input token cost estimate (USD/1M tokens) |
| `AGENT_LLM_COST_OUTPUT_PER_1M` | `10.0` | Output token cost estimate (USD/1M tokens) |

---

## 15. Test Coverage

| Module | Coverage |
|---|---|
| `__init__.py` | 100% |
| `cache.py` | 100% |
| `grounding.py` | 100% |
| `models.py` | 100% |
| `prompt_builder.py` | 100% |
| `provider.py` | 100% |
| `providers/openrouter.py` | 100% |
| `service.py` | 100% |
| `telemetry.py` | 100% |
| `client.py` | 100% |
| `response_parser.py` | 100% |
| **TOTAL** | **100%** (935/935 statements) |

720 tests pass across the full suite (35 dedicated to OpenRouter in
`tests/test_llm_openrouter.py`, covering provider selection, client request
serialization/headers, response parsing, error mapping, timeout, retries, telemetry,
cache integration, redaction, grounding rejection, and the chat API over a mocked
OpenRouter transport). Requirements: coverage ≥ 95% ✅.

---

## 16. Constraints (by design)

The LLM Intelligence Layer **will not**:

- Post GitHub comments or inline review annotations
- Approve or merge pull requests
- Generate, modify, or execute code
- Invent repository facts not present in the supplied evidence
- Run without grounding validation

These constraints are enforced by the `grounding.validate()` gate (raises on any
unverifiable reference), by the `response_parser` (`extra="forbid"` schemas), and by
the absence of any write-path code in the `llm/` package.
