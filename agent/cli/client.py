"""HTTP client for the Waste-IQ agent API.

Thin transport layer: builds requests against the existing agent endpoints and
maps every failure (connection, HTTP error, malformed body) to ``ClientError``.
"""

from __future__ import annotations

from typing import Any, Mapping

import httpx

from cli.models import ChatResponse, SearchResponse


class ClientError(Exception):
    """The agent could not be reached or returned an unexpected response."""


class AgentClient:
    """HTTP client for the existing agent endpoints."""

    def __init__(self, base_url: str, timeout: float = 60.0) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def chat(self, question: str) -> ChatResponse:
        data = self._post("/api/chat", {"question": question})
        try:
            return ChatResponse.model_validate(data)
        except Exception as exc:  # noqa: BLE001 - contract drift surfaces as ClientError
            raise ClientError("agent returned an unexpected chat response") from exc

    def search(self, query: str, limit: int = 10) -> SearchResponse:
        data = self._post("/api/context/search", {"query": query, "limit": limit, "hybrid": True})
        try:
            return SearchResponse.model_validate(data)
        except Exception as exc:  # noqa: BLE001 - contract drift surfaces as ClientError
            raise ClientError("agent returned an unexpected search response") from exc

    def health(self) -> dict[str, Any]:
        return self._get("/api/health")

    def llm_status(self) -> dict[str, Any]:
        return self._get("/api/llm/status")

    def context_status(self) -> dict[str, Any]:
        return self._get("/api/context/status")

    def evaluation_status(self) -> dict[str, Any]:
        return self._get("/api/evaluation/status")

    # -- internals ---------------------------------------------------------

    def _post(self, path: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        try:
            response = self._client.post(path, json=dict(payload))
        except httpx.HTTPError as exc:
            raise ClientError(f"cannot reach agent at {self.base_url}: {exc}") from exc
        return _decode(response, self.base_url)

    def _get(self, path: str) -> dict[str, Any]:
        try:
            response = self._client.get(path)
        except httpx.HTTPError as exc:
            raise ClientError(f"cannot reach agent at {self.base_url}: {exc}") from exc
        return _decode(response, self.base_url)


def _decode(response: httpx.Response, base_url: str) -> dict[str, Any]:
    if response.status_code >= 400:
        raise ClientError(f"agent returned HTTP {response.status_code}: {_detail(response)}")
    try:
        data = response.json()
    except ValueError as exc:
        raise ClientError("agent returned a non-JSON response") from exc
    if not isinstance(data, dict):
        raise ClientError("agent returned an unexpected response shape")
    return data


def _detail(response: httpx.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        return response.text or "unknown error"
    if isinstance(data, dict):
        detail = data.get("detail")
        if isinstance(detail, str):
            return detail
        return str(detail) if detail is not None else str(data)
    return str(data)
