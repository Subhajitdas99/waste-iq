"""Tests for pull request providers (GitHub read-only + fixture)."""

import base64

import pytest
import respx
from httpx import Response

from app.review.pr_provider import FixturePullRequestProvider, GitHubPullRequestProvider
from app.review.review_models import ReviewUnavailable

_API = "https://api.github.test"


def _content_payload(text: str) -> dict:
    return {
        "type": "file",
        "encoding": "base64",
        "content": base64.b64encode(text.encode("utf-8")).decode("ascii"),
    }


@pytest.fixture
def provider():
    return GitHubPullRequestProvider("test-token", base_url=_API, timeout=5.0)


@pytest.fixture
def pr_metadata() -> dict:
    return {
        "number": 12,
        "title": "Add payments",
        "state": "open",
        "user": {"login": "alice"},
        "head": {"ref": "feature/payments", "sha": "sha-1"},
        "base": {"ref": "main"},
    }


@respx.mock
def test_get_pull_request_full_flow(provider, pr_metadata):
    diff = "diff --git a/x.py b/x.py\n@@ -0,0 +1,2 @@\n+a\n+b\n"
    respx.get(
        f"{_API}/repos/acme/app/pulls/12", headers={"Accept": "application/vnd.github+json"}
    ).mock(return_value=Response(200, json=pr_metadata))
    respx.get(
        f"{_API}/repos/acme/app/pulls/12", headers={"Accept": "application/vnd.github.v3.diff"}
    ).mock(return_value=Response(200, text=diff))
    respx.get(f"{_API}/repos/acme/app/pulls/12/files", params={"per_page": 100}).mock(
        return_value=Response(
            200,
            json=[
                {
                    "filename": "x.py",
                    "status": "added",
                    "patch": "@@ -0,0 +1,2 @@\n+a\n+b\n",
                }
            ],
        )
    )
    respx.get(f"{_API}/repos/acme/app/contents/x.py", params={"ref": "sha-1"}).mock(
        return_value=Response(200, json=_content_payload("a\nb\n"))
    )

    pr = provider.get_pull_request("acme/app", 12)
    assert pr.number == 12
    assert pr.title == "Add payments"
    assert pr.branch == "feature/payments"
    assert pr.commit_sha == "sha-1"
    assert pr.author == "alice"
    assert pr.diff == diff
    assert len(pr.files) == 1
    assert pr.files[0].status == "added"
    assert pr.files[0].content == "a\nb\n"
    assert pr.files[0].added_lines


@respx.mock
def test_get_pull_request_falls_back_to_diff_when_no_files(provider, pr_metadata):
    diff = (
        "diff --git a/a.py b/a.py\n"
        "index 1..2\n"
        "--- a/a.py\n"
        "+++ b/a.py\n"
        "@@ -1,1 +1,2 @@\n"
        " def f():\n"
        "+    return 1\n"
    )
    respx.get(
        f"{_API}/repos/acme/app/pulls/12", headers={"Accept": "application/vnd.github+json"}
    ).mock(return_value=Response(200, json=pr_metadata))
    respx.get(
        f"{_API}/repos/acme/app/pulls/12", headers={"Accept": "application/vnd.github.v3.diff"}
    ).mock(return_value=Response(200, text=diff))
    respx.get(f"{_API}/repos/acme/app/pulls/12/files", params={"per_page": 100}).mock(
        return_value=Response(200, json=[])
    )

    pr = provider.get_pull_request("acme/app", 12)
    assert pr.files and pr.files[0].path == "a.py"


@respx.mock
def test_get_pull_request_not_found(provider):
    respx.get(
        f"{_API}/repos/acme/app/pulls/12", headers={"Accept": "application/vnd.github+json"}
    ).mock(return_value=Response(404, json={}))
    respx.get(
        f"{_API}/repos/acme/app/pulls/12", headers={"Accept": "application/vnd.github.v3.diff"}
    ).mock(return_value=Response(404, json={}))

    with pytest.raises(ReviewUnavailable):
        provider.get_pull_request("acme/app", 12)


@respx.mock
def test_retry_on_503_then_success(provider):
    route = respx.get(f"{_API}/repos/acme/app/pulls/12")
    route.side_effect = [
        Response(503, json={}),
        Response(200, json={"number": 12, "head": {"sha": "s"}, "base": {"ref": "m"}}),
    ]
    data = provider._get_json("/repos/acme/app/pulls/12")
    assert data["number"] == 12
    assert route.call_count == 2


@respx.mock
def test_retry_exhausted_raises(provider):
    route = respx.get(f"{_API}/repos/acme/app/pulls/12")
    route.side_effect = [Response(503, json={})] * 4
    with pytest.raises(Exception, match="github api error"):
        provider._get_json("/repos/acme/app/pulls/12")
    assert route.call_count == 3


@respx.mock
def test_other_error_status_raises(provider):
    respx.get(f"{_API}/repos/acme/app/pulls/12").mock(return_value=Response(403, json={}))
    with pytest.raises(ReviewUnavailable):
        provider._get_json("/repos/acme/app/pulls/12")


@respx.mock
def test_find_pull_request_for_head(provider, pr_metadata):
    respx.get(f"{_API}/repos/acme/app/pulls", params={"state": "open", "per_page": 100}).mock(
        return_value=Response(200, json=[pr_metadata])
    )
    respx.get(
        f"{_API}/repos/acme/app/pulls/12", headers={"Accept": "application/vnd.github+json"}
    ).mock(return_value=Response(200, json=pr_metadata))
    respx.get(
        f"{_API}/repos/acme/app/pulls/12", headers={"Accept": "application/vnd.github.v3.diff"}
    ).mock(return_value=Response(200, text=""))
    respx.get(f"{_API}/repos/acme/app/pulls/12/files", params={"per_page": 100}).mock(
        return_value=Response(200, json=[])
    )

    pr = provider.find_pull_request_for_head("acme/app", "feature/payments")
    assert pr is not None
    assert pr.number == 12


@respx.mock
def test_find_pull_request_for_head_no_match(provider, pr_metadata):
    respx.get(f"{_API}/repos/acme/app/pulls", params={"state": "open", "per_page": 100}).mock(
        return_value=Response(200, json=[pr_metadata])
    )
    assert provider.find_pull_request_for_head("acme/app", "other-branch") is None


@respx.mock
def test_content_fetch_failure_returns_none(provider, pr_metadata):
    diff = "diff --git a/x.py b/x.py\n@@ -0,0 +1,1 @@\n+a\n"
    respx.get(
        f"{_API}/repos/acme/app/pulls/12", headers={"Accept": "application/vnd.github+json"}
    ).mock(return_value=Response(200, json=pr_metadata))
    respx.get(
        f"{_API}/repos/acme/app/pulls/12", headers={"Accept": "application/vnd.github.v3.diff"}
    ).mock(return_value=Response(200, text=diff))
    respx.get(f"{_API}/repos/acme/app/pulls/12/files", params={"per_page": 100}).mock(
        return_value=Response(
            200,
            json=[{"filename": "x.py", "status": "modified", "patch": "@@ -0,0 +1,1 @@\n+a\n"}],
        )
    )
    respx.get(f"{_API}/repos/acme/app/contents/x.py", params={"ref": "sha-1"}).mock(
        return_value=Response(404, json={})
    )

    pr = provider.get_pull_request("acme/app", 12)
    assert pr.files[0].content is None


@respx.mock
def test_network_error_retries_then_raises(provider):
    route = respx.get(f"{_API}/repos/acme/app/pulls/12")
    route.side_effect = [httpx_connect_error()] * 3
    with pytest.raises(Exception, match="github api unreachable"):
        provider._get_json("/repos/acme/app/pulls/12")
    assert route.call_count == 3


def httpx_connect_error():
    from httpx import ConnectError

    return ConnectError("boom")


# ------------------------------------------------------------------
# Fixture provider


def test_fixture_provider_serves_demo_pr():
    provider = FixturePullRequestProvider()
    pr = provider.get_pull_request("waste-iq/demo", 1)
    assert pr.files
    assert provider.get_patch("waste-iq/demo", 1)
    assert pr.title


def test_fixture_provider_unknown_pr_raises():
    provider = FixturePullRequestProvider()
    with pytest.raises(ReviewUnavailable):
        provider.get_pull_request("waste-iq/demo", 2)


def test_fixture_provider_head_lookup():
    provider = FixturePullRequestProvider()
    assert provider.find_pull_request_for_head("waste-iq/demo", "feature/demo-payments") is not None
    assert provider.find_pull_request_for_head("waste-iq/demo", "other") is None
