import asyncio
from typing import Any, Awaitable, Callable

import httpx

TokenProvider = Callable[[], Awaitable[str]]

RETRY_STATUSES = {429, 500, 502, 503, 504}
MAX_RETRIES = 4


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
    """Typed REST reads used by the agent. Phase 0 covers repository/issue reads."""

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

    async def get_issue(self, issue_number: int) -> dict:
        return await self.request("GET", f"/repos/{self.owner}/{self.repo}/issues/{issue_number}")

    async def list_open_issues(self, per_page: int = 30) -> list[dict]:
        return await self.request(
            "GET", f"/repos/{self.owner}/{self.repo}/issues?state=open&per_page={per_page}"
        )
