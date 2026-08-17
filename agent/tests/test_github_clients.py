import json

import httpx
import pytest
import respx

from app.clients.github_graphql import GitHubGraphQLClient
from app.clients.github_rest import GitHubAPIError, GitHubRESTClient

OWNER = "Subhajitdas99"
REPO = "waste-iq"
BASE = "https://api.github.com"
TOKEN = "test-installation-token"


async def _token() -> str:
    return TOKEN


def _rest_client() -> GitHubRESTClient:
    return GitHubRESTClient(OWNER, REPO, token_provider=_token)


@pytest.mark.anyio
async def test_get_repository_success():
    with respx.mock:
        respx.get(f"{BASE}/repos/{OWNER}/{REPO}").mock(
            return_value=httpx.Response(200, json={"full_name": f"{OWNER}/{REPO}"})
        )

        result = await _rest_client().get_repository()

    assert result["full_name"] == f"{OWNER}/{REPO}"


@pytest.mark.anyio
async def test_retries_then_succeeds_on_502():
    with respx.mock:
        route = respx.get(f"{BASE}/repos/{OWNER}/{REPO}").mock(
            side_effect=[
                httpx.Response(502),
                httpx.Response(200, json={"full_name": f"{OWNER}/{REPO}"}),
            ]
        )

        result = await _rest_client().get_repository()

    assert route.call_count == 2
    assert result["full_name"] == f"{OWNER}/{REPO}"


@pytest.mark.anyio
async def test_raises_api_error_on_404():
    with respx.mock:
        respx.get(f"{BASE}/repos/{OWNER}/{REPO}").mock(
            return_value=httpx.Response(404, json={"message": "Not Found"})
        )

        with pytest.raises(GitHubAPIError):
            await _rest_client().get_repository()


@pytest.mark.anyio
async def test_raises_after_repeated_failures():
    with respx.mock:
        respx.get(f"{BASE}/repos/{OWNER}/{REPO}").mock(return_value=httpx.Response(503))

        with pytest.raises(GitHubAPIError):
            await _rest_client().get_repository()


@pytest.mark.anyio
async def test_retries_on_network_error():
    with respx.mock:
        route = respx.get(f"{BASE}/repos/{OWNER}/{REPO}").mock(
            side_effect=[httpx.ConnectError("boom"), httpx.Response(200, json={"ok": True})]
        )

        result = await _rest_client().get_repository()

    assert route.call_count == 2
    assert result["ok"] is True


@pytest.mark.anyio
async def test_graphql_returns_data():
    with respx.mock:
        respx.post(f"{BASE}/graphql").mock(
            return_value=httpx.Response(
                200, json={"data": {"repository": {"nameWithOwner": f"{OWNER}/{REPO}"}}}
            )
        )

        data = await GitHubGraphQLClient(_token).run("{ __typename }")

    assert data["repository"]["nameWithOwner"] == f"{OWNER}/{REPO}"


@pytest.mark.anyio
async def test_graphql_raises_on_errors():
    with respx.mock:
        respx.post(f"{BASE}/graphql").mock(
            return_value=httpx.Response(200, json={"errors": [{"message": "field not found"}]})
        )

        with pytest.raises(GitHubAPIError):
            await GitHubGraphQLClient(_token).run("{ missing }")


@pytest.mark.anyio
async def test_list_labels():
    with respx.mock:
        route = respx.get(f"{BASE}/repos/{OWNER}/{REPO}/labels?per_page=100").mock(
            return_value=httpx.Response(200, json=[{"name": "bug"}, {"name": "backend"}])
        )
        result = await _rest_client().list_labels()
    assert route.call_count == 1
    assert [label["name"] for label in result] == ["bug", "backend"]


@pytest.mark.anyio
async def test_list_issue_comments():
    with respx.mock:
        route = respx.get(f"{BASE}/repos/{OWNER}/{REPO}/issues/7/comments?per_page=100").mock(
            return_value=httpx.Response(200, json=[{"id": 1, "body": "hello"}])
        )
        result = await _rest_client().list_issue_comments(7)
    assert route.call_count == 1
    assert result[0]["body"] == "hello"


@pytest.mark.anyio
async def test_create_issue_comment():
    with respx.mock:
        route = respx.post(f"{BASE}/repos/{OWNER}/{REPO}/issues/7/comments").mock(
            return_value=httpx.Response(201, json={"id": 99})
        )
        result = await _rest_client().create_issue_comment(7, "proposal body")
    assert route.call_count == 1
    assert result["id"] == 99
    assert json.loads(route.calls[0].request.content) == {"body": "proposal body"}


@pytest.mark.anyio
async def test_create_issue_comment_raises_on_422():
    with respx.mock:
        respx.post(f"{BASE}/repos/{OWNER}/{REPO}/issues/7/comments").mock(
            return_value=httpx.Response(422, json={"message": "Validation Failed"})
        )
        with pytest.raises(GitHubAPIError):
            await _rest_client().create_issue_comment(7, "bad")


# ----------------------------------------------------------------------
# Documentation Agent write path (Phase 4)
# ----------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_file_contents():
    with respx.mock:
        route = respx.get(
            f"{BASE}/repos/{OWNER}/{REPO}/contents/CHANGELOG.md?ref=agent/docs-1"
        ).mock(return_value=httpx.Response(200, json={"content": "aGVsbG8=", "sha": "abc"}))
        result = await _rest_client().get_file_contents("CHANGELOG.md", branch="agent/docs-1")
    assert route.call_count == 1
    assert result["sha"] == "abc"


@pytest.mark.anyio
async def test_create_or_update_file_base64_encodes_content():
    with respx.mock:
        route = respx.put(f"{BASE}/repos/{OWNER}/{REPO}/contents/CHANGELOG.md").mock(
            return_value=httpx.Response(200, json={"content": {"sha": "new"}})
        )
        await _rest_client().create_or_update_file(
            "CHANGELOG.md",
            "line one\n",
            "docs: update changelog",
            "agent/docs-1",
            sha="old-sha",
        )
    assert route.call_count == 1
    payload = json.loads(route.calls[0].request.content)
    assert payload["message"] == "docs: update changelog"
    assert payload["branch"] == "agent/docs-1"
    assert payload["sha"] == "old-sha"
    assert payload["content"] == "bGluZSBvbmUK"


@pytest.mark.anyio
async def test_create_git_ref():
    with respx.mock:
        route = respx.post(f"{BASE}/repos/{OWNER}/{REPO}/git/refs").mock(
            return_value=httpx.Response(201, json={"ref": "refs/heads/agent/docs-1"})
        )
        await _rest_client().create_git_ref("agent/docs-1", "deadbeef")
    assert route.call_count == 1
    payload = json.loads(route.calls[0].request.content)
    assert payload == {"ref": "refs/heads/agent/docs-1", "sha": "deadbeef"}


@pytest.mark.anyio
async def test_create_pull_request():
    with respx.mock:
        route = respx.post(f"{BASE}/repos/{OWNER}/{REPO}/pulls").mock(
            return_value=httpx.Response(201, json={"number": 101})
        )
        result = await _rest_client().create_pull_request(
            "docs: changelog entry for PR #10",
            "agent/docs-1",
            "develop",
            body="body text",
        )
    assert route.call_count == 1
    assert result["number"] == 101
    payload = json.loads(route.calls[0].request.content)
    assert payload["head"] == "agent/docs-1"
    assert payload["base"] == "develop"
    assert payload["body"] == "body text"


@pytest.mark.anyio
async def test_list_pull_request_files():
    with respx.mock:
        route = respx.get(f"{BASE}/repos/{OWNER}/{REPO}/pulls/10/files?per_page=100").mock(
            return_value=httpx.Response(200, json=[{"filename": "backend/app/api/routes/x.py"}])
        )
        result = await _rest_client().list_pull_request_files(10)
    assert route.call_count == 1
    assert result[0]["filename"] == "backend/app/api/routes/x.py"
