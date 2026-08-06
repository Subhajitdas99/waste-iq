"""LLM Intelligence Layer service.

Orchestrates prompt building -> caching -> provider call (with retries and
rate limiting) -> strict parsing -> grounding validation -> telemetry.
The provider is only an assistant: findings and repository facts come from
the evidence the caller supplied, and any response that cannot be grounded is
rejected.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from typing import cast

from app.core.config import get_settings
from app.llm import cache as cache_module
from app.llm import provider as provider_module
from app.llm import telemetry as telemetry_module
from app.llm.grounding import EvidenceUniverse, validate
from app.llm.models import (
    AnalyzeRequest,
    AnalyzeResponse,
    ExplainRequest,
    ExplainResponse,
    GroundingViolationError,
    LLMError,
    LLMNotConfigured,
    LLMProviderError,
    LLMRequest,
    LLMRetryableError,
    LLMRole,
    LLMStatus,
    LLMTimeoutError,
    LLMProviderName,
    MalformedResponseError,
    ProviderInfo,
    ProviderRequest,
    ProviderResponse,
    RateLimitedError,
    SummarizeRequest,
    SummarizeResponse,
)
from app.llm.prompt_builder import PromptBuilder
from app.llm.response_parser import ResponseParser

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple in-process sliding-window rate limiter."""

    def __init__(self, max_per_minute: int) -> None:
        self._max = max(1, max_per_minute)
        self._window: deque[float] = deque()

    def allow(self) -> bool:
        now = time.monotonic()
        while self._window and self._window[0] <= now - 60.0:
            self._window.popleft()
        if len(self._window) >= self._max:
            return False
        self._window.append(now)
        return True

    def reset(self) -> None:
        self._window.clear()


class LLMService:
    def __init__(
        self,
        settings=None,
        provider=None,
        cache=None,
        telemetry=None,
        builder: PromptBuilder | None = None,
        parser: ResponseParser | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._provider = provider
        self._parser = parser or ResponseParser()
        self._telemetry = telemetry or telemetry_module.Telemetry(
            cost_input_per_1m=self._settings.agent_llm_cost_input_per_1m,
            cost_output_per_1m=self._settings.agent_llm_cost_output_per_1m,
        )
        self._cache = cache if cache is not None else self._build_cache()
        self._builder = builder or PromptBuilder(
            max_input_tokens=self._settings.agent_llm_max_input_tokens
        )
        self._limiter = RateLimiter(self._settings.agent_llm_rate_limit_per_minute)
        self._metrics = telemetry_module.Metrics(enabled=self._settings.agent_enable_prometheus)

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def analyze(
        self, request: AnalyzeRequest, *, correlation_id: str | None = None
    ) -> AnalyzeResponse:
        return cast(AnalyzeResponse, self._run("analyze", request, correlation_id=correlation_id))

    def explain(
        self, request: ExplainRequest, *, correlation_id: str | None = None
    ) -> ExplainResponse:
        return cast(ExplainResponse, self._run("explain", request, correlation_id=correlation_id))

    def summarize(
        self, request: SummarizeRequest, *, correlation_id: str | None = None
    ) -> SummarizeResponse:
        return cast(
            SummarizeResponse, self._run("summarize", request, correlation_id=correlation_id)
        )

    def providers(self) -> list[ProviderInfo]:
        return provider_module.providers_info(self._settings)

    def status(self) -> LLMStatus:
        name, configured = self._resolved()
        status = self._telemetry.snapshot(
            enabled=self._settings.agent_llm_enabled,
            provider=name,
            configured=configured,
            model=self._active_model(name),
            deterministic_fallback=not configured,
            cache_backend=self._settings.agent_llm_cache_backend,
        )
        self._metrics.publish(status)
        return status

    # ------------------------------------------------------------------
    def _run(
        self, role: LLMRole, request: LLMRequest, *, correlation_id: str | None
    ) -> AnalyzeResponse | ExplainResponse | SummarizeResponse:
        if not self._settings.agent_llm_enabled:
            raise LLMNotConfigured("LLM intelligence layer is disabled")
        provider = self._provider_for(request)
        name = provider.name
        model = request.model or self._active_model(name)
        trace = telemetry_module.TraceContext(correlation_id=correlation_id)

        built = self._builder.build(role, request)
        if built.redactions:
            logger.info(
                "llm redaction applied count=%d role=%s provider=%s " "correlation_id=%s",
                built.redactions,
                role,
                name,
                trace.correlation_id,
            )
        cache_key = cache_module.hash_request(name, model, built.system_prompt, built.user_prompt)
        cached = None
        if self._cache_enabled():
            cached = self._cache.get(cache_key)
        if cached is not None:
            self._telemetry.record_cache(hit=True)
            parsed = self._parser.parse(cached, role)
            return self._decorate(parsed, name, model, correlation_id, cached=True, latency_ms=0)

        self._telemetry.record_cache(hit=False)
        if not self._limiter.allow():
            raise RateLimitedError(
                f"rate limit exceeded for provider '{name}' "
                f"({self._settings.agent_llm_rate_limit_per_minute}/min)"
            )

        universe = EvidenceUniverse(built.evidence)
        start = time.monotonic()
        provider_response = self._call_with_retries(
            provider,
            ProviderRequest(
                model=model,
                system_prompt=built.system_prompt,
                user_prompt=built.user_prompt,
                max_tokens=request.max_tokens or self._settings.agent_llm_max_output_tokens,
                temperature=self._settings.agent_llm_temperature,
                timeout=self._settings.agent_llm_timeout_seconds,
            ),
            trace=trace,
        )
        latency_ms = int((time.monotonic() - start) * 1000)

        parsed = self._parser.parse(provider_response.content, role)
        validation = validate(parsed, universe)
        if not validation.supported:
            raise GroundingViolationError(
                "response rejected: " + "; ".join(validation.violations[:3])
            )
        self._record(
            provider,
            latency_ms,
            provider_response,
            retries=provider_response.retries,
            trace=trace,
        )
        if self._cache_enabled():
            self._cache.set(
                cache_key, provider_response.content, ttl=self._settings.agent_llm_cache_ttl_seconds
            )
        return self._decorate(
            parsed, name, model, correlation_id, cached=False, latency_ms=latency_ms
        )

    def _call_with_retries(
        self, provider, provider_request: ProviderRequest, *, trace
    ) -> ProviderResponse:
        max_retries = self._settings.agent_llm_max_retries
        backoff = self._settings.agent_llm_retry_backoff_seconds
        retries = 0
        for attempt in range(max_retries + 1):
            try:
                response = provider.complete(provider_request)
                if not response.content:
                    raise MalformedResponseError("provider returned empty content")
                response.retries = retries
                return response
            except LLMRetryableError as exc:
                if attempt >= max_retries:
                    self._record_failure(provider, retries=retries, trace=trace)
                    raise LLMProviderError(
                        f"provider '{provider.name}' unavailable after {attempt + 1} attempts"
                    ) from exc
                retries += 1
                logger.warning(
                    "llm provider retry attempt=%d provider=%s error=%s " "correlation_id=%s",
                    attempt + 1,
                    provider.name,
                    exc,
                    trace.correlation_id,
                )
                time.sleep(backoff * (attempt + 1))
            except LLMTimeoutError:
                self._record_failure(provider, retries=retries, trace=trace)
                raise
            except LLMError:
                self._record_failure(provider, retries=retries, trace=trace)
                raise
        raise LLMProviderError("provider call failed")  # pragma: no cover - unreachable

    def _record_failure(self, provider, *, retries: int, trace) -> None:
        self._telemetry.record_call(
            provider.name,
            latency_ms=0,
            prompt_tokens=0,
            completion_tokens=0,
            failure=True,
            retries=retries,
            request_id=trace.request_id,
        )
        self._metrics.record_call(provider.name, failure=True)

    def _record(
        self, provider, latency_ms: int, response: ProviderResponse, *, retries: int, trace
    ) -> None:
        self._telemetry.record_call(
            provider.name,
            latency_ms=latency_ms,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            failure=False,
            retries=retries,
            request_id=trace.request_id,
        )
        self._metrics.record_call(provider.name, failure=False)

    def _decorate(
        self,
        parsed,
        provider: str,
        model: str,
        correlation_id: str | None,
        *,
        cached: bool,
        latency_ms: int,
    ):
        parsed.provider = provider
        parsed.model = model
        parsed.cached = cached
        parsed.correlation_id = correlation_id
        parsed.latency_ms = latency_ms
        return parsed

    # ------------------------------------------------------------------
    def _resolved(self) -> tuple[str, bool]:
        return provider_module.resolve_provider(self._settings)

    def _active_model(self, name: str) -> str:
        return self._settings.agent_llm_model or provider_module.provider_default_model(name)

    def _provider_for(self, request: LLMRequest):
        if self._provider is not None:
            return self._provider
        if request.provider:
            return provider_module.provider_for_name(
                cast(LLMProviderName, request.provider),
                self._settings,
                self._settings.agent_llm_timeout_seconds,
            )
        return provider_module.build_provider(self._settings)

    def _cache_enabled(self) -> bool:
        return bool(self._settings.agent_llm_cache_enabled)

    def _build_cache(self):
        return cache_module.build_cache(self._settings)
