from datetime import datetime, timedelta, timezone

import httpx
import pytest
import respx
from jose import jwt

from app.clients.github_app import GitHubAppAuth

APP_ID = "12345"
INSTALLATION_ID = 999


def _make_rsa_key() -> str:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()


@pytest.fixture()
def rsa_private_key() -> str:
    return _make_rsa_key()


def test_build_app_jwt_has_expected_claims(rsa_private_key):
    auth = GitHubAppAuth(APP_ID, rsa_private_key, INSTALLATION_ID)
    token = auth.build_app_jwt()

    header = jwt.get_unverified_header(token)
    assert header["alg"] == "RS256"

    claims = jwt.decode(token, rsa_private_key, algorithms=["RS256"])
    assert claims["iss"] == int(APP_ID)
    now = datetime.now(timezone.utc)
    assert claims["iat"] <= int(now.timestamp())
    assert claims["exp"] > int(now.timestamp())


@pytest.mark.anyio
async def test_get_token_caches_and_forces_refresh(rsa_private_key):
    expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat().replace("+00:00", "Z")

    with respx.mock:
        route = respx.post(
            f"https://api.github.com/app/installations/{INSTALLATION_ID}/access_tokens"
        ).mock(
            return_value=httpx.Response(
                201,
                json={"token": "install-token-1", "expires_at": expires, "expires_in": 3600},
            )
        )

        auth = GitHubAppAuth(APP_ID, rsa_private_key, INSTALLATION_ID)
        first = await auth.get_token()
        cached = await auth.get_token()
        refreshed = await auth.get_token(force=True)
        await auth.aclose()

    assert first == "install-token-1"
    assert cached == "install-token-1"
    assert refreshed == "install-token-1"
    assert route.call_count == 2


@pytest.mark.anyio
async def test_get_token_raises_on_http_error(rsa_private_key):
    with respx.mock:
        respx.post(
            f"https://api.github.com/app/installations/{INSTALLATION_ID}/access_tokens"
        ).mock(return_value=httpx.Response(401, json={"message": "Bad credentials"}))

        auth = GitHubAppAuth(APP_ID, rsa_private_key, INSTALLATION_ID)
        with pytest.raises(httpx.HTTPStatusError):
            await auth.get_token()
        await auth.aclose()
