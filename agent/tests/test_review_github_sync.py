"""Tests for the synchronous GitHub app installation-token issuance."""

import httpx
import respx

from app.clients.github_app import GitHubAppAuth, request_installation_token_sync

_BASE = "https://api.github.test"


@respx.mock
def test_request_installation_token_sync(monkeypatch):
    monkeypatch.setattr(GitHubAppAuth, "build_app_jwt", lambda self: "fake-jwt")
    respx.post(f"{_BASE}/app/installations/999/access_tokens").mock(
        return_value=httpx.Response(
            200, json={"token": "inst-token-1", "expires_at": "2030-01-01T00:00:00Z"}
        )
    )

    token = request_installation_token_sync("12345", "fake-key", 999, base_url=_BASE)

    assert token == "inst-token-1"
    request = respx.calls.last.request
    assert request.headers["Authorization"] == "Bearer fake-jwt"
    assert request.headers["Accept"] == "application/vnd.github+json"


@respx.mock
def test_request_installation_token_sync_failure_raises(monkeypatch):
    monkeypatch.setattr(GitHubAppAuth, "build_app_jwt", lambda self: "fake-jwt")
    respx.post(f"{_BASE}/app/installations/999/access_tokens").mock(
        return_value=httpx.Response(401, json={"message": "Bad credentials"})
    )

    try:
        request_installation_token_sync("12345", "fake-key", 999, base_url=_BASE)
    except httpx.HTTPStatusError:
        pass
    else:
        raise AssertionError("expected an HTTP error to be raised")
