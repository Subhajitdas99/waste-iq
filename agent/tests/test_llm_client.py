"""Tests for provider HTTP clients (OpenAI, Anthropic, Gemini, Ollama)."""

import httpx
import pytest
import respx

from app.llm.client import (
    AnthropicProvider,
    GeminiProvider,
    OllamaProvider,
    OpenAIProvider,
)
from app.llm.models import (
    LLMProviderError,
    LLMRetryableError,
    LLMTimeoutError,
    ProviderRequest,
)

OPENAI_URL = "https://api.openai.com/v1/chat/completions"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
)
OLLAMA_URL = "http://localhost:11434/api/chat"


def _request(**overrides):
    values = {
        "model": "m",
        "system_prompt": "system",
        "user_prompt": "user",
        "max_tokens": 500,
        "temperature": 0.0,
        "timeout": 5.0,
    }
    values.update(overrides)
    return ProviderRequest(**values)


def _openai_body():
    return {
        "choices": [{"message": {"content": '{"summary": "s"}'}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 12, "completion_tokens": 4},
        "model": "gpt-4o-mini",
    }


@respx.mock
def test_openai_success():
    respx.post(OPENAI_URL).mock(return_value=httpx.Response(200, json=_openai_body()))
    provider = OpenAIProvider(
        api_key="sk-test", base_url="https://api.openai.com/v1", model="gpt-4o-mini"
    )
    response = provider.complete(_request())
    assert '{"summary": "s"}' in response.content
    assert response.prompt_tokens == 12
    assert response.completion_tokens == 4
    request = respx.calls.last.request
    assert request.headers["authorization"] == "Bearer sk-test"


@respx.mock
def test_openai_retryable_on_429():
    respx.post(OPENAI_URL).mock(return_value=httpx.Response(429, json={}))
    provider = OpenAIProvider(
        api_key="sk-test", base_url="https://api.openai.com/v1", model="gpt-4o-mini"
    )
    with pytest.raises(LLMRetryableError):
        provider.complete(_request())


@respx.mock
def test_openai_retryable_on_5xx():
    respx.post(OPENAI_URL).mock(return_value=httpx.Response(500, json={}))
    provider = OpenAIProvider(
        api_key="sk-test", base_url="https://api.openai.com/v1", model="gpt-4o-mini"
    )
    with pytest.raises(LLMRetryableError):
        provider.complete(_request())


@respx.mock
def test_openai_non_retryable_on_400():
    respx.post(OPENAI_URL).mock(return_value=httpx.Response(400, json={}))
    provider = OpenAIProvider(
        api_key="sk-test", base_url="https://api.openai.com/v1", model="gpt-4o-mini"
    )
    with pytest.raises(LLMProviderError):
        provider.complete(_request())


@respx.mock
def test_openai_timeout_raises_timeout_error():
    def _slow(request):
        raise httpx.ReadTimeout("timeout")

    respx.post(OPENAI_URL).mock(side_effect=_slow)
    provider = OpenAIProvider(
        api_key="sk-test", base_url="https://api.openai.com/v1", model="gpt-4o-mini"
    )
    with pytest.raises(LLMTimeoutError):
        provider.complete(_request())


@respx.mock
def test_anthropic_success_headers():
    body = {
        "content": [{"type": "text", "text": '{"explanation": "e"}'}],
        "usage": {"input_tokens": 7, "output_tokens": 3},
        "model": "claude-3-5-haiku-latest",
        "stop_reason": "end_turn",
    }
    respx.post(ANTHROPIC_URL).mock(return_value=httpx.Response(200, json=body))
    provider = AnthropicProvider(
        api_key="sk-ant-test", base_url="https://api.anthropic.com", model="claude-3-5-haiku-latest"
    )
    response = provider.complete(_request())
    assert '{"explanation": "e"}' in response.content
    assert response.prompt_tokens == 7
    assert response.finish_reason == "end_turn"
    request = respx.calls.last.request
    assert request.headers["x-api-key"] == "sk-ant-test"
    assert request.headers["anthropic-version"] == "2023-06-01"


@respx.mock
def test_gemini_success_usage_metadata():
    body = {
        "candidates": [
            {
                "content": {"parts": [{"text": '{"overview": "o"}'}]},
                "finishReason": "STOP",
            }
        ],
        "usageMetadata": {"promptTokenCount": 9, "candidatesTokenCount": 5},
    }
    respx.post(GEMINI_URL).mock(return_value=httpx.Response(200, json=body))
    provider = GeminiProvider(
        api_key="AIza-test",
        base_url="https://generativelanguage.googleapis.com/v1beta",
        model="gemini-2.0-flash",
    )
    response = provider.complete(_request(model="gemini-2.0-flash"))
    assert '{"overview": "o"}' in response.content
    assert response.prompt_tokens == 9
    assert response.completion_tokens == 5
    request = respx.calls.last.request
    assert request.url.params["key"] == "AIza-test"


@respx.mock
def test_ollama_success_no_stream():
    body = {"message": {"content": '{"summary": "s"}'}, "done": True, "done_reason": "stop"}
    respx.post(OLLAMA_URL).mock(return_value=httpx.Response(200, json=body))
    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2")
    response = provider.complete(_request())
    assert '{"summary": "s"}' in response.content
    assert response.finish_reason == "stop"
    request = respx.calls.last.request
    payload = request.content.decode("utf-8")
    assert '"stream": false' in payload.replace('"stream":false', '"stream": false')
