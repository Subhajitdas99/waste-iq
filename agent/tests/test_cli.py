"""Tests for the wiq CLI: argument parsing, API contract and error handling."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
import pytest
import respx

from cli.client import AgentClient, ClientError
from cli.main import _agent_url, build_parser, main
from cli.models import ChatResponse, SearchResponse

BASE = "http://127.0.0.1:8000"

CHAT_PAYLOAD: dict[str, Any] = {
    "intent": "explain_code",
    "answer": "The DealerApprovalGate guards the dealer approval workflow.",
    "confidence": 0.95,
    "references": [
        {
            "file_path": "backend/app/services/dealer_approval.py",
            "start_line": 12,
            "end_line": 40,
        }
    ],
    "provider": "openrouter",
    "model": "deepseek/deepseek-chat",
    "cached": False,
    "latency_ms": 1234,
    "grounded": True,
    "notes": [],
}

SEARCH_PAYLOAD: dict[str, Any] = {
    "results": [
        {
            "chunk_id": "c1",
            "path": "backend/app/services/dealer_approval.py",
            "start_line": 1,
            "end_line": 5,
            "score": 0.87,
            "source_type": "code",
        }
    ],
    "total": 1,
}


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def test_parser_ask() -> None:
    args = build_parser().parse_args(["ask", "Explain the dealer approval workflow"])
    assert args.command == "ask"
    assert args.question == "Explain the dealer approval workflow"


def test_parser_search() -> None:
    args = build_parser().parse_args(["search", "DealerApprovalGate", "--limit", "5"])
    assert args.command == "search"
    assert args.query == "DealerApprovalGate"
    assert args.limit == 5


def test_parser_status() -> None:
    args = build_parser().parse_args(["status"])
    assert args.command == "status"


def test_parser_benchmark_flags() -> None:
    args = build_parser().parse_args(["benchmark", "--skip-index", "--baseline", "base.json"])
    assert args.command == "benchmark"
    assert args.skip_index is True
    assert args.baseline == "base.json"


def test_parser_requires_subcommand() -> None:
    with pytest.raises(SystemExit) as exc_info:
        build_parser().parse_args([])
    assert exc_info.value.code == 2


def test_parser_global_url_flag() -> None:
    args = build_parser().parse_args(["--url", "http://localhost:9000", "status"])
    assert args.url == "http://localhost:9000"


def test_agent_url_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WIQ_AGENT_URL", "http://localhost:9999")
    assert _agent_url() == "http://localhost:9999"


def test_agent_url_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WIQ_AGENT_URL", raising=False)
    assert _agent_url() == "http://127.0.0.1:8000"


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------


def test_client_chat_success() -> None:
    with respx.mock:
        respx.post(f"{BASE}/api/chat").mock(return_value=httpx.Response(200, json=CHAT_PAYLOAD))
        client = AgentClient(BASE)
        try:
            response = client.chat("Explain dealer approval")
        finally:
            client.close()
    assert response.answer == CHAT_PAYLOAD["answer"]
    assert response.intent == "explain_code"
    assert response.confidence == pytest.approx(0.95)
    assert response.provider == "openrouter"
    assert response.latency_ms == 1234
    assert response.references[0].file_path == "backend/app/services/dealer_approval.py"
    assert response.references[0].start_line == 12
    assert response.references[0].end_line == 40


def test_client_search_success() -> None:
    with respx.mock:
        respx.post(f"{BASE}/api/context/search").mock(
            return_value=httpx.Response(200, json=SEARCH_PAYLOAD)
        )
        client = AgentClient(BASE)
        try:
            response = client.search("DealerApprovalGate")
        finally:
            client.close()
    assert response.total == 1
    assert response.results[0].path == "backend/app/services/dealer_approval.py"
    assert response.results[0].score == pytest.approx(0.87)
    assert response.results[0].start_line == 1
    assert response.results[0].end_line == 5


def test_client_http_error_surfaces_detail() -> None:
    with respx.mock:
        respx.post(f"{BASE}/api/chat").mock(
            return_value=httpx.Response(503, json={"detail": "LLM not configured"})
        )
        client = AgentClient(BASE)
        try:
            with pytest.raises(ClientError, match="HTTP 503"):
                client.chat("hello")
        finally:
            client.close()


def test_client_connection_error() -> None:
    with respx.mock:
        respx.post(f"{BASE}/api/chat").mock(side_effect=httpx.ConnectError("connection refused"))
        client = AgentClient(BASE)
        try:
            with pytest.raises(ClientError, match="cannot reach agent"):
                client.chat("hello")
        finally:
            client.close()


def test_client_non_json_response() -> None:
    with respx.mock:
        respx.post(f"{BASE}/api/chat").mock(return_value=httpx.Response(200, text="oops"))
        client = AgentClient(BASE)
        try:
            with pytest.raises(ClientError, match="non-JSON"):
                client.chat("hello")
        finally:
            client.close()


def test_client_contract_drift() -> None:
    with respx.mock:
        respx.post(f"{BASE}/api/chat").mock(return_value=httpx.Response(200, json={"nope": 1}))
        client = AgentClient(BASE)
        try:
            with pytest.raises(ClientError, match="unexpected chat response"):
                client.chat("hello")
        finally:
            client.close()


# ---------------------------------------------------------------------------
# main() dispatch, output and exit codes
# ---------------------------------------------------------------------------


class _FakeClient:
    """In-process stand-in for AgentClient (no network needed in main tests)."""

    def __init__(self) -> None:
        self.questions: list[str] = []
        self.queries: list[str] = []
        self.evaluation_calls = 0

    def close(self) -> None:
        pass

    def chat(self, question: str) -> ChatResponse:
        self.questions.append(question)
        return ChatResponse.model_validate(CHAT_PAYLOAD)

    def search(self, query: str, limit: int = 10) -> SearchResponse:
        self.queries.append(query)
        return SearchResponse.model_validate(SEARCH_PAYLOAD)

    def health(self) -> dict[str, Any]:
        return {"status": "ok", "app": "Waste-IQ AI Agent", "environment": "test"}

    def llm_status(self) -> dict[str, Any]:
        return {"enabled": True, "provider": "openrouter", "configured": True, "model": "m"}

    def context_status(self) -> dict[str, Any]:
        return {"indexed_files": 3, "chunk_count": 4, "vector_count": 4}

    def evaluation_status(self) -> dict[str, Any]:
        self.evaluation_calls += 1
        return {
            "benchmark_version": "v1",
            "run_id": "r1",
            "overall_score": 95.0,
            "failures": 0,
            "cases_executed": 10,
            "hallucinations": 0,
            "gates": {
                "repository_search_ge_90": True,
                "grounding_eq_100": True,
                "hallucinations_zero": True,
                "overall_ge_90": True,
                "passed": True,
            },
        }


def _patch_client(monkeypatch: pytest.MonkeyPatch) -> _FakeClient:
    fake = _FakeClient()
    monkeypatch.setattr("cli.main._make_client", lambda args: fake)
    return fake


def test_main_ask_success(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    fake = _patch_client(monkeypatch)
    assert main(["ask", "Explain dealer approval"]) == 0
    out = capsys.readouterr().out
    assert fake.questions == ["Explain dealer approval"]
    assert "guard" in out
    assert "Intent" in out
    assert "explain_code" in out
    assert "openrouter" in out
    assert "dealer_approval.py:12-40" in out


def test_main_search_success(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    fake = _patch_client(monkeypatch)
    assert main(["search", "DealerApprovalGate"]) == 0
    out = capsys.readouterr().out
    assert fake.queries == ["DealerApprovalGate"]
    assert "0.8700" in out
    assert "dealer_approval.py:1-5" in out


def test_main_status_success(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    _patch_client(monkeypatch)
    assert main(["status"]) == 0
    out = capsys.readouterr().out
    assert "Agent Health" in out
    assert "LLM" in out
    assert "Context / Index" in out


def test_main_server_unavailable(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    def _broken(_args: object) -> AgentClient:
        raise ClientError("cannot reach agent at http://127.0.0.1:8000")

    monkeypatch.setattr("cli.main._make_client", _broken)
    assert main(["status"]) == 1
    assert "cannot reach agent" in capsys.readouterr().err


def test_main_ask_api_error(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    class _BrokenClient:
        def close(self) -> None:
            pass

        def chat(self, question: str) -> ChatResponse:
            raise ClientError("agent returned HTTP 503: LLM not configured")

    monkeypatch.setattr("cli.main._make_client", lambda args: _BrokenClient())
    assert main(["ask", "hello"]) == 1
    assert "HTTP 503" in capsys.readouterr().err


def test_main_status_partial_failure(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    class _PartialClient(_FakeClient):
        def llm_status(self) -> dict[str, Any]:
            raise ClientError("agent returned HTTP 502: provider error")

    monkeypatch.setattr("cli.main._make_client", lambda args: _PartialClient())
    assert main(["status"]) == 1
    captured = capsys.readouterr()
    assert "LLM" in captured.out
    assert "provider error" in captured.err


def test_main_benchmark_exit_code_passthrough(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    class _Result:
        returncode = 3

    captured: dict[str, Any] = {}

    def fake_run(command: list[str], cwd: str) -> _Result:
        captured["command"] = command
        return _Result()

    fake = _patch_client(monkeypatch)
    monkeypatch.setattr("cli.main.subprocess.run", fake_run)
    assert main(["benchmark"]) == 3
    assert captured["command"][-1].endswith("run_evaluation.py")
    assert fake.evaluation_calls == 1
    out = capsys.readouterr().out
    assert "Overall score" in out
    assert "VERDICT" in out


def test_main_benchmark_missing_script(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    _patch_client(monkeypatch)
    monkeypatch.setattr(
        "cli.main.BENCHMARK_SCRIPT", Path("F:/definitely/missing/run_evaluation.py")
    )
    assert main(["benchmark"]) == 1
    assert "benchmark script not found" in capsys.readouterr().err
