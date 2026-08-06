"""HTTP clients for concrete LLM providers.

Each client speaks one provider's chat API and normalizes the result into a
`ProviderResponse`. A single attempt is made per call; retries and backoff are
owned by the service layer so telemetry can count them. Retryable conditions
(429/5xx/network) raise `LLMRetryableError`; other 4xx raise `LLMProviderError`.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.llm.models import (
    LLMProviderError,
    LLMRetryableError,
    LLMTimeoutError,
    ProviderRequest,
    ProviderResponse,
)

logger = logging.getLogger(__name__)

_RETRY_STATUSES = {429, 500, 502, 503, 504}


def _estimate_tokens(text: str) -> int:
    return max(1, round(len(text) / 4))


def _send_single(
    client: httpx.Client,
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    json_body: dict[str, Any] | None = None,
    params: dict[str, str] | None = None,
    timeout: float,
) -> httpx.Response:
    try:
        response = client.request(method, url, headers=headers, json=json_body, params=params)
    except httpx.TimeoutException as exc:
        raise LLMTimeoutError(f"provider call timed out after {timeout:.1f}s") from exc
    except httpx.HTTPError as exc:
        raise LLMRetryableError(f"provider network error: {exc}") from exc
    if response.status_code in _RETRY_STATUSES:
        raise LLMRetryableError(f"provider retryable error status={response.status_code}")
    if response.status_code >= 400:
        raise LLMProviderError(
            f"provider error status={response.status_code} body={response.text[:300]}"
        )
    return response


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": request.model or self._model,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt},
            ],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }
        with httpx.Client(timeout=request.timeout) as client:
            response = _send_single(
                client, "POST", url, headers=headers, json_body=body, timeout=request.timeout
            )
        data = response.json()
        choice = (data.get("choices") or [{}])[0]
        usage = data.get("usage") or {}
        message = choice.get("message") or {}
        return ProviderResponse(
            content=message.get("content") or "",
            model=data.get("model") or self._model,
            prompt_tokens=int(
                usage.get("prompt_tokens")
                or _estimate_tokens(request.system_prompt + request.user_prompt)
            ),
            completion_tokens=int(
                usage.get("completion_tokens") or _estimate_tokens(message.get("content") or "")
            ),
            finish_reason=choice.get("finish_reason") or "",
            raw=data,
        )


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        url = f"{self._base_url}/v1/messages"
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        body = {
            "model": request.model or self._model,
            "max_tokens": request.max_tokens,
            "system": request.system_prompt,
            "messages": [{"role": "user", "content": request.user_prompt}],
        }
        with httpx.Client(timeout=request.timeout) as client:
            response = _send_single(
                client, "POST", url, headers=headers, json_body=body, timeout=request.timeout
            )
        data = response.json()
        usage = data.get("usage") or {}
        return ProviderResponse(
            content="".join(
                block.get("text", "")
                for block in data.get("content") or []
                if block.get("type") == "text"
            ),
            model=data.get("model") or self._model,
            prompt_tokens=int(
                usage.get("input_tokens")
                or _estimate_tokens(request.system_prompt + request.user_prompt)
            ),
            completion_tokens=int(usage.get("output_tokens") or 0),
            finish_reason=data.get("stop_reason") or "",
            raw=data,
        )


class GeminiProvider:
    name = "google"

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        model = request.model or self._model
        url = f"{self._base_url}/models/{model}:generateContent"
        body = {
            "systemInstruction": {"parts": [{"text": request.system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": request.user_prompt}]}],
            "generationConfig": {
                "maxOutputTokens": request.max_tokens,
                "temperature": request.temperature,
            },
        }
        with httpx.Client(timeout=request.timeout) as client:
            response = _send_single(
                client,
                "POST",
                url,
                headers={"Content-Type": "application/json"},
                json_body=body,
                params={"key": self._api_key},
                timeout=request.timeout,
            )
        data = response.json()
        usage = data.get("usageMetadata") or {}
        candidate = (data.get("candidates") or [{}])[0]
        parts = (candidate.get("content") or {}).get("parts") or []
        return ProviderResponse(
            content="".join(part.get("text", "") for part in parts),
            model=model,
            prompt_tokens=int(
                usage.get("promptTokenCount")
                or _estimate_tokens(request.system_prompt + request.user_prompt)
            ),
            completion_tokens=int(usage.get("candidatesTokenCount") or 0),
            finish_reason=str(candidate.get("finishReason") or ""),
            raw=data,
        )


class OllamaProvider:
    name = "ollama"

    def __init__(self, base_url: str, model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        url = f"{self._base_url}/api/chat"
        body = {
            "model": request.model or self._model,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt},
            ],
            "stream": False,
            "options": {"temperature": request.temperature},
        }
        with httpx.Client(timeout=request.timeout) as client:
            response = _send_single(client, "POST", url, json_body=body, timeout=request.timeout)
        data = response.json()
        return ProviderResponse(
            content=(data.get("message") or {}).get("content") or "",
            model=data.get("model") or self._model,
            prompt_tokens=int(data.get("prompt_eval_count") or 0),
            completion_tokens=int(data.get("eval_count") or 0),
            finish_reason=data.get("done_reason") or "",
            raw=data,
        )
