"""Provider abstraction for the LLM Intelligence Layer.

`build_provider` selects a provider from configuration
(AGENT_LLM_PROVIDER). When a non-mock provider is requested but no
credentials are configured, we fall back to the deterministic in-process
MockProvider so the system remains fully deterministic with no secrets set.
"""

from __future__ import annotations

import json
import re
from typing import Protocol

from app.llm.models import (
    DEFAULT_MODELS,
    LLMNotConfigured,
    LLMProviderName,
    PROVIDER_NAMES,
    PROVIDER_DESCRIPTIONS,
    ProviderInfo,
    ProviderRequest,
    ProviderResponse,
)

_OPENAI_BASE = "https://api.openai.com/v1"
_ANTHROPIC_BASE = "https://api.anthropic.com"
_GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"
_OLLAMA_BASE = "http://localhost:11434"
_OPENROUTER_BASE = "https://openrouter.ai/api/v1"

_EVIDENCE_LINE_RE = re.compile(
    r"\bevidence_id:\s*([^\s|]+).*?\bfile:\s*([^\s|]+).*?\blines:\s*(\d+)(?:-(\d+))?"
)


class LLMProvider(Protocol):
    name: str

    def complete(self, request: ProviderRequest) -> ProviderResponse: ...


def provider_default_model(name: str) -> str:
    return DEFAULT_MODELS.get(name, "mock-model")


class MockProvider:
    """Deterministic in-process provider used when nothing is configured.

    Never touches the network. It reads the EVIDENCE block embedded in the
    prompt and emits a valid, grounded JSON response that references the first
    evidence entries — so grounding validation deterministically passes.
    """

    name = "mock"

    def __init__(self, model: str = "mock-model", latency_ms: float = 1.0) -> None:
        self._model = model
        self._latency_ms = latency_ms

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        import time

        time.sleep(self._latency_ms / 1000.0)
        evidence = _EVIDENCE_LINE_RE.findall(request.user_prompt)
        references = [
            {
                "file_path": path,
                "start_line": int(start),
                "end_line": int(end if end else start),
                "evidence_id": eid,
                "chunk_id": f"chunk:{path}:{start}",
            }
            for eid, path, start, end in evidence[:3]
        ]
        role = "analyze"
        if "Role: explain" in request.user_prompt:
            role = "explain"
        elif "Role: summarize" in request.user_prompt:
            role = "summarize"
        if role == "analyze":
            payload = {
                "summary": "Deterministic mock analysis grounded in the supplied evidence.",
                "priorities": ["review the highest-severity findings first"],
                "recommendations": ["confirm each finding against the referenced lines"],
                "risks": ["unaddressed high-severity findings may ship to production"],
                "confidence": 0.5,
            }
        elif role == "explain":
            payload = {
                "explanation": "Deterministic mock explanation based on the referenced evidence.",
                "confidence": 0.5,
            }
        else:
            payload = {
                "overview": "Deterministic mock summary of the supplied evidence.",
                "key_points": ["key point grounded in the referenced evidence"],
                "confidence": 0.5,
            }
        payload["references"] = references
        content = json.dumps(payload)
        return ProviderResponse(
            content=content,
            model=self._model,
            prompt_tokens=len(request.system_prompt.split()) + len(request.user_prompt.split()),
            completion_tokens=len(content.split()),
            finish_reason="stop",
            raw={"provider": "mock"},
        )


def provider_base_url(name: str) -> str:
    return {
        "openai": _OPENAI_BASE,
        "anthropic": _ANTHROPIC_BASE,
        "google": _GEMINI_BASE,
        "ollama": _OLLAMA_BASE,
        "openrouter": _OPENROUTER_BASE,
    }.get(name, "")


def provider_requires_key(name: str) -> bool:
    return name in {"openai", "anthropic", "google", "openrouter"}


def is_configured(name: str, settings) -> bool:
    """Whether the named provider has usable credentials."""
    if name == "mock":
        return True
    if name == "ollama":
        return True
    if name == "openai":
        return bool(settings.agent_llm_api_key or settings.agent_openai_api_key)
    if name == "anthropic":
        return bool(settings.agent_llm_api_key or settings.agent_anthropic_api_key)
    if name == "google":
        return bool(settings.agent_llm_api_key or settings.agent_google_api_key)
    if name == "openrouter":
        return bool(settings.agent_openrouter_api_key)
    return False


def resolve_provider(settings) -> tuple[str, bool]:
    """Resolve (provider_name, configured) with deterministic mock fallback."""
    requested = settings.agent_llm_provider
    if requested not in PROVIDER_NAMES:
        raise LLMNotConfigured(
            f"unknown LLM provider '{requested}'; expected one of {PROVIDER_NAMES}"
        )
    if is_configured(requested, settings):
        return requested, True
    return "mock", False


def build_provider(settings) -> LLMProvider:
    """Return the provider instance for the active configuration."""
    from app.llm.client import (
        AnthropicProvider,
        GeminiProvider,
        OllamaProvider,
        OpenAIProvider,
    )
    from app.llm.providers.openrouter import OpenRouterProvider

    name, configured = resolve_provider(settings)
    model = settings.agent_llm_model or provider_default_model(name)
    if not configured:
        name = "mock"
        model = provider_default_model("mock")
    if name == "openai":
        return OpenAIProvider(
            api_key=settings.agent_llm_api_key or settings.agent_openai_api_key or "",
            base_url=settings.agent_llm_base_url or provider_base_url("openai"),
            model=model,
        )
    if name == "anthropic":
        return AnthropicProvider(
            api_key=settings.agent_llm_api_key or settings.agent_anthropic_api_key or "",
            base_url=settings.agent_llm_base_url or provider_base_url("anthropic"),
            model=model,
        )
    if name == "google":
        return GeminiProvider(
            api_key=settings.agent_llm_api_key or settings.agent_google_api_key or "",
            base_url=settings.agent_llm_base_url or provider_base_url("google"),
            model=model,
        )
    if name == "ollama":
        return OllamaProvider(
            base_url=settings.agent_llm_base_url or provider_base_url("ollama"),
            model=model,
        )
    if name == "openrouter":
        return OpenRouterProvider(
            api_key=settings.agent_openrouter_api_key or "",
            base_url=settings.agent_openrouter_base_url or provider_base_url("openrouter"),
            model=model,
            http_referer=settings.agent_openrouter_http_referer,
            app_name=settings.agent_openrouter_app_name,
        )
    return MockProvider(model=model)


def providers_info(settings) -> list[ProviderInfo]:
    """Descriptions for every known provider (used by /api/llm/providers)."""
    info: list[ProviderInfo] = []
    names: tuple[str, ...] = (
        "openai",
        "anthropic",
        "google",
        "ollama",
        "openrouter",
        "mock",
    )
    for name in names:
        info.append(
            ProviderInfo(
                name=name,
                configured=is_configured(name, settings),
                deterministic=name == "mock",
                description=PROVIDER_DESCRIPTIONS[name],
                default_model=provider_default_model(name),
                base_url=provider_base_url(name) or None,
            )
        )
    return info


def provider_for_name(name: LLMProviderName, settings, timeout: float) -> LLMProvider:
    """Explicit provider selection (used for per-request provider overrides)."""
    if name == "mock":
        return MockProvider(model=provider_default_model("mock"))
    if name not in PROVIDER_NAMES:
        raise LLMNotConfigured(f"unknown provider '{name}'; expected one of {PROVIDER_NAMES}")
    if not is_configured(name, settings):
        raise LLMNotConfigured(f"provider '{name}' is not configured")
    from app.llm.client import (
        AnthropicProvider,
        GeminiProvider,
        OllamaProvider,
        OpenAIProvider,
    )
    from app.llm.providers.openrouter import OpenRouterProvider

    model = settings.agent_llm_model or provider_default_model(name)
    if name == "openai":
        return OpenAIProvider(
            api_key=settings.agent_llm_api_key or settings.agent_openai_api_key or "",
            base_url=settings.agent_llm_base_url or provider_base_url("openai"),
            model=model,
        )
    if name == "anthropic":
        return AnthropicProvider(
            api_key=settings.agent_llm_api_key or settings.agent_anthropic_api_key or "",
            base_url=settings.agent_llm_base_url or provider_base_url("anthropic"),
            model=model,
        )
    if name == "google":
        return GeminiProvider(
            api_key=settings.agent_llm_api_key or settings.agent_google_api_key or "",
            base_url=settings.agent_llm_base_url or provider_base_url("google"),
            model=model,
        )
    if name == "ollama":
        return OllamaProvider(
            base_url=settings.agent_llm_base_url or provider_base_url("ollama"),
            model=model,
        )
    return OpenRouterProvider(
        api_key=settings.agent_openrouter_api_key or "",
        base_url=settings.agent_openrouter_base_url or provider_base_url("openrouter"),
        model=model,
        http_referer=settings.agent_openrouter_http_referer,
        app_name=settings.agent_openrouter_app_name,
    )
