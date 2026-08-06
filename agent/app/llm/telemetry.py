"""Telemetry for the LLM Intelligence Layer.

Tracks latency, token usage, estimated cost, failure rate, retries and
per-provider aggregates. Exposes a `LLMStatus` snapshot consumed by the status
endpoint. Optional Prometheus counters are registered when enabled.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any

from app.llm.models import (
    LLMStatus,
    ProviderAggregate,
)


@dataclass
class _Agg:
    calls: int = 0
    failures: int = 0
    retries: int = 0
    latency_total_ms: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost: float = 0.0


class Telemetry:
    def __init__(self, *, cost_input_per_1m: float = 2.5, cost_output_per_1m: float = 10.0) -> None:
        self._lock = threading.Lock()
        self._agg: dict[str, _Agg] = {}
        self._cache_hits = 0
        self._cache_misses = 0
        self._cost_input_per_1m = cost_input_per_1m
        self._cost_output_per_1m = cost_output_per_1m

    def record_call(
        self,
        provider: str,
        *,
        latency_ms: int,
        prompt_tokens: int,
        completion_tokens: int,
        failure: bool,
        retries: int,
        request_id: str | None = None,
    ) -> None:
        cost = (
            prompt_tokens * self._cost_input_per_1m / 1_000_000
            + completion_tokens * self._cost_output_per_1m / 1_000_000
        )
        with self._lock:
            agg = self._agg.setdefault(provider, _Agg())
            agg.calls += 1
            if failure:
                agg.failures += 1
            agg.retries += retries
            if latency_ms:
                agg.latency_total_ms += latency_ms
            agg.prompt_tokens += prompt_tokens
            agg.completion_tokens += completion_tokens
            agg.cost += cost

    def record_cache(self, *, hit: bool) -> None:
        with self._lock:
            if hit:
                self._cache_hits += 1
            else:
                self._cache_misses += 1

    def reset(self) -> None:
        with self._lock:
            self._agg.clear()
            self._cache_hits = 0
            self._cache_misses = 0

    def snapshot(
        self,
        *,
        enabled: bool,
        provider: str,
        configured: bool,
        model: str,
        deterministic_fallback: bool,
        cache_backend: str,
    ) -> LLMStatus:
        with self._lock:
            aggregates = [
                ProviderAggregate(
                    provider=name,
                    calls=agg.calls,
                    failures=agg.failures,
                    retries=agg.retries,
                    average_latency_ms=(int(agg.latency_total_ms / agg.calls) if agg.calls else 0),
                    total_prompt_tokens=agg.prompt_tokens,
                    total_completion_tokens=agg.completion_tokens,
                    estimated_cost=round(agg.cost, 6),
                )
                for name, agg in sorted(self._agg.items())
            ]
            calls = sum(a.calls for a in aggregates)
            failed = sum(a.failures for a in aggregates)
            retries = sum(a.retries for a in aggregates)
            latency = sum(a.average_latency_ms * a.calls for a in aggregates)
            prompt = sum(a.total_prompt_tokens for a in aggregates)
            completion = sum(a.total_completion_tokens for a in aggregates)
            cost = sum(a.estimated_cost for a in aggregates)
            hits, misses = self._cache_hits, self._cache_misses
        return LLMStatus(
            enabled=enabled,
            provider=provider,
            configured=configured,
            model=model,
            deterministic_fallback=deterministic_fallback,
            cache_backend=cache_backend,
            cache_hits=hits,
            cache_misses=misses,
            total_calls=calls,
            failed_calls=failed,
            retries=retries,
            average_latency_ms=int(latency / calls) if calls else 0,
            total_prompt_tokens=prompt,
            total_completion_tokens=completion,
            estimated_cost=round(cost, 6),
            by_provider=aggregates,
        )


class Metrics:
    """Optional Prometheus hook publishing current counters at scrape time.

    Only active when `AGENT_ENABLE_PROMETHEUS=true`; registration failures are
    swallowed so metrics can never break the agent.
    """

    def __init__(self, enabled: bool) -> None:
        self._enabled = enabled
        self._calls: Any = None
        self._failures: Any = None
        self._hits: Any = None
        self._misses: Any = None
        self._tokens: Any = None
        if enabled:
            self._setup()

    def _setup(self) -> None:  # pragma: no cover - prometheus registration
        try:
            from prometheus_client import Counter, Gauge

            self._calls = Counter("agent_llm_calls_total", "LLM provider calls", ["provider"])
            self._failures = Counter(
                "agent_llm_failures_total", "LLM provider failures", ["provider"]
            )
            self._hits = Counter("agent_llm_cache_hits_total", "LLM cache hits")
            self._misses = Counter("agent_llm_cache_misses_total", "LLM cache misses")
            self._tokens = Gauge("agent_llm_tokens_total", "LLM tokens used", ["kind"])
        except Exception:  # noqa: BLE001 - never crash on metrics
            self._enabled = False

    def record_call(self, provider: str, *, failure: bool, cache_hit: bool | None = None) -> None:
        if not self._enabled:
            return
        try:  # pragma: no cover - prometheus client calls
            if self._calls is not None:
                self._calls.labels(provider=provider).inc()
            if failure and self._failures is not None:
                self._failures.labels(provider=provider).inc()
            if cache_hit is True and self._hits is not None:
                self._hits.inc()
            elif cache_hit is False and self._misses is not None:
                self._misses.inc()
        except Exception:  # pragma: no cover - never crash on metrics
            return

    def publish(self, status: LLMStatus) -> None:
        if not self._enabled or self._tokens is None:
            return
        try:  # pragma: no cover - prometheus client calls
            self._tokens.labels(kind="prompt").set(status.total_prompt_tokens)
            self._tokens.labels(kind="completion").set(status.total_completion_tokens)
        except Exception:  # pragma: no cover - never crash on metrics
            return


class TraceContext:
    """Lightweight tracing context attached to structured logs."""

    def __init__(self, request_id: str | None = None, correlation_id: str | None = None) -> None:
        self.request_id = request_id
        self.correlation_id = correlation_id
