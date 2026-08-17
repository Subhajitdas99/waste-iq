import logging
from datetime import datetime, timedelta, timezone

import httpx
from jose import jwt

logger = logging.getLogger(__name__)

API_BASE_URL = "https://api.github.com"
TOKEN_BUFFER_MINUTES = 5


class GitHubAppAuth:
    """Issues short-lived GitHub installation tokens from an app JWT.

    Tokens are cached in memory for ~1 hour and never persisted to disk.
    """

    def __init__(
        self,
        app_id: str,
        private_key: str,
        installation_id: int,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.app_id = app_id
        self.private_key = private_key
        self.installation_id = installation_id
        self._client = client
        self._token: str | None = None
        self._expires_at: datetime | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0, base_url=API_BASE_URL)
        return self._client

    def build_app_jwt(self) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "iat": int(now.timestamp()) - 60,
            "exp": int((now + timedelta(minutes=9)).timestamp()),
            "iss": int(self.app_id),
        }
        return jwt.encode(payload, self.private_key, algorithm="RS256")

    async def get_token(self, force: bool = False) -> str:
        """Return a cached installation token, refreshing if stale or forced."""
        if self._token and self._expires_at:
            if not force and self._expires_at > datetime.now(timezone.utc) + timedelta(
                minutes=TOKEN_BUFFER_MINUTES
            ):
                return self._token

        headers = {
            "Authorization": f"Bearer {self.build_app_jwt()}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        resp = await self.client.post(
            f"/app/installations/{self.installation_id}/access_tokens", headers=headers
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["token"]
        expires = data.get("expires_at")
        if expires:
            self._expires_at = datetime.fromisoformat(expires.replace("Z", "+00:00"))
        else:
            self._expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        logger.info(
            "issued installation token installation=%s expires_at=%s",
            self.installation_id,
            self._expires_at,
        )
        return self._token

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()


def request_installation_token_sync(
    app_id: str,
    private_key: str,
    installation_id: int,
    base_url: str = API_BASE_URL,
    timeout: float = 20.0,
) -> str:
    """Synchronous counterpart of GitHubAppAuth.get_token.

    Used by the (synchronous) PR Review Agent provider so review runs can
    issue a short-lived installation token without an event loop.
    """
    auth = GitHubAppAuth(app_id, private_key, installation_id)
    headers = {
        "Authorization": f"Bearer {auth.build_app_jwt()}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    import httpx

    with httpx.Client(timeout=timeout, base_url=base_url) as client:
        response = client.post(
            f"/app/installations/{installation_id}/access_tokens", headers=headers
        )
        response.raise_for_status()
        return response.json()["token"]
