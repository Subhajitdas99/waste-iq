"""OpenRouter provider client (Phase 5.1).

OpenRouter exposes an OpenAI-compatible Chat Completions API
(``POST {base_url}/chat/completions``) that fronts hundreds of models.
Authentication is ``Authorization: Bearer <OPENROUTER_API_KEY>``; the optional
``HTTP-Referer`` and ``X-Title`` headers identify the app to the OpenRouter
community ranking.

A single attempt is made per call — retries, backoff, timeout and telemetry
are owned by the LLM service layer, exactly like the other providers.
"""

from __future__ import annotations

import httpx

from app.llm.client import _estimate_tokens, _send_single
from app.llm.models import ProviderRequest, ProviderResponse


class OpenRouterProvider:
    """OpenRouter Chat Completions client implementing the LLMProvider protocol."""

    name = "openrouter"

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        *,
        http_referer: str | None = None,
        app_name: str | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._http_referer = http_referer
        self._app_name = app_name

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        url = f"{self._base_url}/chat/completions"
        headers: dict[str, str] = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        if self._http_referer:
            headers["HTTP-Referer"] = self._http_referer
        if self._app_name:
            headers["X-Title"] = self._app_name
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
