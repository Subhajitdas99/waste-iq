"""Tests for the LLM telemetry layer."""

from app.llm.models import LLMStatus
from app.llm.telemetry import Metrics, Telemetry


def test_telemetry_records_and_snapshots():
    telemetry = Telemetry(cost_input_per_1m=2.5, cost_output_per_1m=10.0)
    telemetry.record_call(
        "mock",
        latency_ms=100,
        prompt_tokens=100,
        completion_tokens=50,
        failure=False,
        retries=0,
    )
    status = telemetry.snapshot(
        enabled=True,
        provider="mock",
        configured=True,
        model="mock-model",
        deterministic_fallback=False,
        cache_backend="memory",
    )
    assert status.total_calls == 1
    assert status.average_latency_ms == 100
    assert status.total_prompt_tokens == 100
    assert status.total_completion_tokens == 50
    assert status.estimated_cost > 0
    assert status.cache_hits == 0
    aggregate = status.by_provider[0]
    assert aggregate.provider == "mock"
    assert aggregate.average_latency_ms == 100


def test_telemetry_records_failure_and_retries():
    telemetry = Telemetry()
    telemetry.record_call(
        "openai",
        latency_ms=0,
        prompt_tokens=0,
        completion_tokens=0,
        failure=True,
        retries=2,
    )
    status = telemetry.snapshot(
        enabled=True,
        provider="mock",
        configured=False,
        model="m",
        deterministic_fallback=True,
        cache_backend="sqlite",
    )
    assert status.failed_calls == 1
    assert status.retries == 2
    assert status.deterministic_fallback is True


def test_telemetry_cache_counts():
    telemetry = Telemetry()
    telemetry.record_cache(hit=True)
    telemetry.record_cache(hit=True)
    telemetry.record_cache(hit=False)
    status = telemetry.snapshot(
        enabled=True,
        provider="mock",
        configured=True,
        model="m",
        deterministic_fallback=False,
        cache_backend="memory",
    )
    assert status.cache_hits == 2
    assert status.cache_misses == 1


def test_telemetry_reset():
    telemetry = Telemetry()
    telemetry.record_call(
        "mock",
        latency_ms=10,
        prompt_tokens=5,
        completion_tokens=5,
        failure=False,
        retries=0,
    )
    telemetry.record_cache(hit=False)
    telemetry.reset()
    status = telemetry.snapshot(
        enabled=True,
        provider="mock",
        configured=True,
        model="m",
        deterministic_fallback=False,
        cache_backend="memory",
    )
    assert status.total_calls == 0
    assert status.cache_misses == 0
    assert status.by_provider == []


def test_metrics_disabled_noop():
    metrics = Metrics(enabled=False)
    metrics.record_call("mock", failure=True)
    metrics.publish(
        LLMStatus(
            enabled=True,
            provider="mock",
            configured=True,
            model="m",
            deterministic_fallback=False,
            cache_backend="memory",
        )
    )


def test_metrics_enabled_registers_collectors():
    metrics = Metrics(enabled=True)
    metrics.record_call("mock", failure=False)
    metrics.publish(
        LLMStatus(
            enabled=True,
            provider="mock",
            configured=True,
            model="m",
            deterministic_fallback=False,
            cache_backend="memory",
        )
    )
