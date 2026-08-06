import asyncio
import base64
from typing import Any, Awaitable, Callable

import httpx

TokenProvider = Callable[[], Awaitable[str]]

RETRY_STATUSES = {429, 500, 502, 503, 504}
MAX_RETRIES = 4


def _b64encode(content: str) -> str:
    return base64.b64encode(content.encode("utf-8")).decode("ascii")


class GitHubAPIError(RuntimeError):
    pass


class _GitHubApiClient:
    """Shared HTTP plumbing for REST and GraphQL clients: auth, retries, errors."""

    def __init__(
        self,
        token_provider: TokenProvider,
        client: httpx.AsyncClient | None = None,
        base_url: str = "https://api.github.com",
    ) -> None:
        self._token_provider = token_provider
        self._client = client
        self.base_url = base_url

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0, base_url=self.base_url)
        return self._client

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def request(
        self, method: str, path: str, *, json: Any = None, retries: int = MAX_RETRIES
    ) -> Any:
        last_error: Exception | None = None
        for attempt in range(retries):
            token = await self._token_provider()
            headers = dict(self._headers())
            headers["Authorization"] = f"Bearer {token}"
            try:
                resp = await self.client.request(
                    method, f"{self.base_url}{path}", headers=headers, json=json
                )
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt < retries - 1:
                    await self._backoff(attempt)
                    continue
                break
            if resp.status_code in RETRY_STATUSES and attempt < retries - 1:
                await self._backoff(attempt)
                continue
            if resp.status_code >= 400:
                raise GitHubAPIError(f"{method} {path} -> {resp.status_code}: {resp.text[:500]}")
            if resp.status_code == 204:
                return None
            return resp.json()
        raise GitHubAPIError(f"{method} {path} failed: {last_error}")

    async def _backoff(self, attempt: int) -> None:
        await asyncio.sleep(0.5 * (2**attempt))


class GitHubRESTClient(_GitHubApiClient):
    """Typed GitHub REST client used by the agent.

    Reads cover repository/issue data (Phase 0+). Write methods are
    intentionally few and explicit: comments (Issue Assistant, propose-only),
    and — only via the Documentation Agent's approval-gated patch-PR flow —
    scoped contents writes (``agent/*`` branches only, see ``doc_*``).
    """

    def __init__(
        self,
        owner: str,
        repo: str,
        token_provider: TokenProvider,
        client: httpx.AsyncClient | None = None,
        base_url: str = "https://api.github.com",
    ) -> None:
        super().__init__(token_provider, client=client, base_url=base_url)
        self.owner = owner
        self.repo = repo

    async def get_repository(self) -> dict:
        return await self.request("GET", f"/repos/{self.owner}/{self.repo}")

    async def get_pull_request(self, pr_number: int) -> dict:
        return await self.request("GET", f"/repos/{self.owner}/{self.repo}/pulls/{pr_number}")

    async def list_pull_request_files(self, pr_number: int, per_page: int = 100) -> list[dict]:
        return await self.request(
            "GET",
            f"/repos/{self.owner}/{self.repo}/pulls/{pr_number}/files?per_page={per_page}",
        )

    async def get_issue(self, issue_number: int) -> dict:
        return await self.request("GET", f"/repos/{self.owner}/{self.repo}/issues/{issue_number}")

    async def list_open_issues(self, per_page: int = 30) -> list[dict]:
        return await self.request(
            "GET", f"/repos/{self.owner}/{self.repo}/issues?state=open&per_page={per_page}"
        )

    async def list_labels(self, per_page: int = 100) -> list[dict]:
        return await self.request(
            "GET", f"/repos/{self.owner}/{self.repo}/labels?per_page={per_page}"
        )

    async def list_issue_comments(self, issue_number: int, per_page: int = 100) -> list[dict]:
        return await self.request(
            "GET",
            f"/repos/{self.owner}/{self.repo}/issues/{issue_number}/comments?per_page={per_page}",
        )

    async def create_issue_comment(self, issue_number: int, body: str) -> dict:
        """Post a comment on an issue (propose-only assistant flow)."""
        return await self.request(
            "POST",
            f"/repos/{self.owner}/{self.repo}/issues/{issue_number}/comments",
            json={"body": body},
        )

    # ------------------------------------------------------------------
    # Documentation Agent write path (approval-gated, agent/* branches only)
    # ------------------------------------------------------------------

    async def get_file_contents(self, path: str, *, branch: str | None = None) -> dict:
        """Read a file's contents metadata via the contents API (base64 blob)."""
        query = f"?ref={branch}" if branch else ""
        return await self.request("GET", f"/repos/{self.owner}/{self.repo}/contents/{path}{query}")

    async def create_or_update_file(
        self,
        path: str,
        content: str,
        message: str,
        branch: str,
        *,
        sha: str | None = None,
    ) -> dict:
        """Create or update a file on ``branch`` (contents API; sha required to update)."""
        payload: dict[str, object] = {
            "message": message,
            "content": _b64encode(content),
            "branch": branch,
        }
        if sha:
            payload["sha"] = sha
        return await self.request(
            "PUT", f"/repos/{self.owner}/{self.repo}/contents/{path}", json=payload
        )

    async def create_git_ref(self, branch: str, sha: str) -> dict:
        """Create a branch pointing at ``sha`` (git refs API)."""
        return await self.request(
            "POST",
            f"/repos/{self.owner}/{self.repo}/git/refs",
            json={"ref": f"refs/heads/{branch}", "sha": sha},
        )

    async def create_pull_request(
        self, title: str, head: str, base: str, *, body: str = ""
    ) -> dict:
        """Open a pull request from ``head`` into ``base``."""
        return await self.request(
            "POST",
            f"/repos/{self.owner}/{self.repo}/pulls",
            json={"title": title, "head": head, "base": base, "body": body},
        )
