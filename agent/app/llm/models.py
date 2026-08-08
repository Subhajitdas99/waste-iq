"""Typed models for the LLM Intelligence Layer.

All LLM output is validated with these Pydantic schemas before it may be
returned or cached. `extra="forbid"` rejects injected or unsupported keys.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.review.review_models import RepositoryContext, ReviewFinding

LLMProviderName = Literal["openai", "anthropic", "google", "ollama", "openrouter", "mock"]
LLMRole = Literal["analyze", "explain", "summarize"]

PROVIDER_NAMES: tuple[str, ...] = (
    "openai",
    "anthropic",
    "google",
    "ollama",
    "openrouter",
    "mock",
)
DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-haiku-latest",
    "google": "gemini-2.0-flash",
    "ollama": "llama3.2",
    "openrouter": "openai/gpt-4o-mini",
    "mock": "mock-model",
}
PROVIDER_DESCRIPTIONS: dict[str, str] = {
    "openai": "OpenAI Chat Completions API",
    "anthropic": "Anthropic Messages API",
    "google": "Google Gemini generateContent API",
    "ollama": "Local Ollama chat API (no network)",
    "openrouter": "OpenRouter unified Chat Completions API",
    "mock": "Deterministic in-process provider (no LLM calls)",
}


class EvidenceRef(BaseModel):
    """A reference that must resolve to retrieved repository evidence."""

    model_config = ConfigDict(extra="forbid")

    file_path: str = Field(min_length=1, max_length=512)
    start_line: int | None = Field(default=None, ge=1)
    end_line: int | None = Field(default=None, ge=1)
    evidence_id: str | None = Field(default=None, max_length=256)
    chunk_id: str | None = Field(default=None, max_length=256)


class GroundedClaim(BaseModel):
    """A single claim the model wants to make, with its evidence refs."""

    model_config = ConfigDict(extra="forbid")

    claim: str = Field(min_length=1, max_length=2000)
    references: list[EvidenceRef] = Field(default_factory=list)


class LLMResponseBase(BaseModel):
    """Common envelope for every accepted LLM response."""

    model_config = ConfigDict(extra="forbid")

    role: LLMRole
    confidence: float = Field(default=0.0)
    references: list[EvidenceRef] = Field(default_factory=list)
    claims: list[GroundedClaim] = Field(default_factory=list)
    disclaimer: str = Field(default="", max_length=500)
    provider: str = ""
    model: str = ""
    cached: bool = False
    correlation_id: str | None = None
    latency_ms: int = 0

    @field_validator("confidence")
    @classmethod
    def _bounded(cls, value: float) -> float:
        return max(0.0, min(1.0, value))


class AnalyzeResponse(LLMResponseBase):
    summary: str = Field(min_length=1, max_length=4000)
    priorities: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class ExplainResponse(LLMResponseBase):
    explanation: str = Field(min_length=1, max_length=8000)


class SummarizeResponse(LLMResponseBase):
    overview: str = Field(min_length=1, max_length=4000)
    key_points: list[str] = Field(default_factory=list)


class LLMRequest(BaseModel):
    """Input shared by the analyze/explain/summarize endpoints."""

    model_config = ConfigDict(extra="forbid")

    repository: str = Field(min_length=1, max_length=256)
    question: str | None = Field(default=None, max_length=4000)
    findings: list[ReviewFinding] = Field(default_factory=list)
    context: RepositoryContext | None = None
    rules_used: list[str] = Field(default_factory=list)
    provider: str | None = Field(default=None, max_length=64)
    model: str | None = Field(default=None, max_length=128)
    max_tokens: int | None = Field(default=None, ge=16, le=8192)

    @field_validator("provider")
    @classmethod
    def _known_provider(cls, value: str | None) -> str | None:
        if value is not None and value not in PROVIDER_NAMES:
            raise ValueError(f"unknown provider '{value}'; expected one of {PROVIDER_NAMES}")
        return value


class AnalyzeRequest(LLMRequest):
    focus: str | None = Field(default=None, max_length=500)


class ExplainRequest(LLMRequest):
    @model_validator(mode="after")
    def _question_required(self) -> ExplainRequest:
        if not self.question or not self.question.strip():
            raise ValueError("question is required for explain")
        return self


class SummarizeRequest(LLMRequest):
    pass


class ProviderRequest(BaseModel):
    """Payload sent to a concrete LLM provider."""

    model_config = ConfigDict(extra="forbid")

    model: str = Field(min_length=1, max_length=128)
    system_prompt: str
    user_prompt: str
    max_tokens: int = Field(default=1500, ge=1, le=8192)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    timeout: float = Field(default=60.0, gt=0.0)


class ProviderResponse(BaseModel):
    """Normalized response returned by any provider."""

    model_config = ConfigDict(extra="forbid")

    content: str
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    finish_reason: str = ""
    raw: dict = Field(default_factory=dict)
    retries: int = 0


class GroundingValidation(BaseModel):
    """Result of validating that every reference resolves to evidence."""

    model_config = ConfigDict(extra="forbid")

    supported: bool
    enabled: bool = True
    claims: int = 0
    references: int = 0
    matched: int = 0
    unsupported: int = 0
    violations: list[str] = Field(default_factory=list)


class ProviderInfo(BaseModel):
    name: str
    configured: bool
    deterministic: bool = False
    description: str = ""
    default_model: str | None = None
    base_url: str | None = None


class ProviderAggregate(BaseModel):
    """Rolled-up telemetry per provider."""

    provider: str
    calls: int = 0
    failures: int = 0
    retries: int = 0
    average_latency_ms: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    estimated_cost: float = 0.0


class LLMStatus(BaseModel):
    enabled: bool
    provider: str
    configured: bool
    model: str
    deterministic_fallback: bool
    cache_backend: str
    cache_hits: int = 0
    cache_misses: int = 0
    total_calls: int = 0
    failed_calls: int = 0
    retries: int = 0
    average_latency_ms: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    estimated_cost: float = 0.0
    by_provider: list[ProviderAggregate] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Errors


class LLMError(Exception):
    """Base class for LLM Intelligence Layer errors."""


class LLMNotConfigured(LLMError):
    """The requested provider has no credentials configured."""


class LLMProviderError(LLMError):
    """The provider returned an error that will not be retried."""


class LLMRetryableError(LLMError):
    """The provider is temporarily unavailable (429/5xx/network); may be retried."""


class LLMTimeoutError(LLMError):
    """The provider call exceeded the configured timeout."""


class MalformedResponseError(LLMError):
    """The provider output could not be parsed or validated."""


class GroundingViolationError(LLMError):
    """The provider output contained unsupported claims or references."""


class RateLimitedError(LLMError):
    """The local rate limit budget for a provider is exhausted."""
