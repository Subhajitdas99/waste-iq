"""Backend tests for WIQ-V1-013 refresh-token authentication."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from jose import jwt as jose_jwt
from sqlalchemy import select

from app.core.config import settings
from app.core.security import decode_access_token, hash_refresh_token
from app.models.audit_log import AuditLog
from app.models.refresh_token import RefreshToken
from app.models.user import User

_PASSWORD = "Test@1234"
_WRONG_PASSWORD = "WrongPass1"

MIGRATION_FILE = (
    Path(__file__).resolve().parent.parent
    / "alembic"
    / "versions"
    / "20260821_0017_refresh_tokens.py"
)


# ─── Helpers ────────────────────────────────────────────────────────────────


def _register(client, email, phone):
    response = client.post(
        "/auth/register",
        json={
            "name": "Refresh User",
            "email": email,
            "password": _PASSWORD,
            "phone": phone,
            "role": "citizen",
        },
    )
    assert response.status_code == 201
    return response.json()


def _login(client, email, password=_PASSWORD):
    return client.post("/auth/login", json={"email": email, "password": password})


def _refresh(client, refresh_token):
    return client.post("/auth/refresh", json={"refresh_token": refresh_token})


def _logout(client, access_token, refresh_token):
    return client.post(
        "/auth/logout",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"},
    )


def _logout_all(client, access_token):
    return client.post(
        "/auth/logout-all",
        headers={"Authorization": f"Bearer {access_token}"},
    )


def _token_rows(db_session, user_id):
    return list(
        db_session.execute(select(RefreshToken).where(RefreshToken.user_id == user_id)).scalars()
    )


def _active_tokens(db_session, user_id):
    return [row for row in _token_rows(db_session, user_id) if row.revoked_at is None]


def _get_user(db_session, email):
    return db_session.execute(select(User).where(User.email == email)).scalar_one()


def _set_token_expired(db_session, raw_token, user_id):
    row = db_session.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.token_hash == hash_refresh_token(raw_token),
        )
    ).scalar_one()
    row.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.commit()


def _assert_generic_401(response):
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid refresh token"}


# ─── Login / register return refresh capability ─────────────────────────────


def test_login_returns_refresh_token(client, db_session):
    _register(client, "rt-login@example.com", "9876543210")
    body = _login(client, "rt-login@example.com").json()
    assert "refresh_token" in body
    assert body["access_token"]
    assert body["refresh_token"] != body["access_token"]


def test_register_returns_refresh_token(client, db_session):
    body = _register(client, "rt-register@example.com", "9876543211")
    assert "refresh_token" in body


def test_refresh_token_stored_as_hash_not_plaintext(client, db_session):
    _register(client, "rt-hash@example.com", "9876543212")
    raw = _login(client, "rt-hash@example.com").json()["refresh_token"]
    user = _get_user(db_session, "rt-hash@example.com")
    rows = _token_rows(db_session, user.id)
    assert len(rows) == 2  # register + login each issue one session
    stored = next(row for row in rows if row.token_hash == hash_refresh_token(raw))
    assert stored.token_hash != raw
    assert stored.revoked_at is None
    assert stored.replaced_by is None


def test_refresh_token_has_configured_lifetime(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "refresh_token_expire_days", 14)
    _register(client, "rt-life@example.com", "9876543213")
    _login(client, "rt-life@example.com").json()["refresh_token"]
    user = _get_user(db_session, "rt-life@example.com")
    stored = _token_rows(db_session, user.id)[0]
    age = stored.expires_at.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)
    assert timedelta(days=13) < age <= timedelta(days=14)


# ─── Refresh success and rotation ───────────────────────────────────────────


def test_refresh_succeeds_and_rotates(client, db_session):
    _register(client, "rt-ok@example.com", "9876543214")
    first = _login(client, "rt-ok@example.com").json()
    user = _get_user(db_session, "rt-ok@example.com")

    response = _refresh(client, first["refresh_token"])
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"] != first["refresh_token"]
    assert body["user"]["id"] == user.id
    assert decode_access_token(body["access_token"]) == str(user.id)

    rows = _token_rows(db_session, user.id)
    assert len(rows) == 3  # register + login + rotated session
    old = next(row for row in rows if row.token_hash == hash_refresh_token(first["refresh_token"]))
    new = next(row for row in rows if row.token_hash == hash_refresh_token(body["refresh_token"]))
    assert old.revoked_at is not None
    assert old.replaced_by == new.id
    assert old.family_id == new.family_id


def test_new_refresh_token_works_after_rotation(client):
    _register(client, "rt-chain@example.com", "9876543215")
    first = _login(client, "rt-chain@example.com").json()
    second = _refresh(client, first["refresh_token"]).json()
    third = _refresh(client, second["refresh_token"]).json()
    assert third["access_token"]
    assert third["refresh_token"] != second["refresh_token"]


def test_access_token_remains_valid_independently(client):
    _register(client, "rt-access@example.com", "9876543216")
    body = _login(client, "rt-access@example.com").json()
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert response.status_code == 200
    # Refreshing must not invalidate the current access token.
    _refresh(client, body["refresh_token"])
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert response.status_code == 200


# ─── Rejected tokens ────────────────────────────────────────────────────────


def test_malformed_refresh_token_rejected(client):
    _assert_generic_401(client.post("/auth/refresh", json={"refresh_token": "not-a-jwt"}))


def test_unknown_refresh_token_rejected_generically(client, db_session):
    _register(client, "rt-unknown@example.com", "9876543217")
    _login(client, "rt-unknown@example.com")
    _assert_generic_401(_refresh(client, "definitely-not-a-real-token"))


def test_expired_refresh_token_rejected(client, db_session):
    _register(client, "rt-expired@example.com", "9876543218")
    raw = _login(client, "rt-expired@example.com").json()["refresh_token"]
    user = _get_user(db_session, "rt-expired@example.com")
    _set_token_expired(db_session, raw, user.id)
    _assert_generic_401(_refresh(client, raw))


def test_access_token_cannot_be_used_as_refresh_token(client):
    _register(client, "rt-cross@example.com", "9876543221")
    body = _login(client, "rt-cross@example.com").json()
    _assert_generic_401(_refresh(client, body["access_token"]))


def test_refresh_token_cannot_be_used_as_access_token(client):
    _register(client, "rt-cross2@example.com", "9876543222")
    body = _login(client, "rt-cross2@example.com").json()
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {body['refresh_token']}"})
    assert response.status_code == 401


def test_decoder_rejects_access_jwt_without_access_type(client):
    _register(client, "rt-typeless@example.com", "9876543223")
    token = jose_jwt.encode({"sub": "1"}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    with pytest.raises(ValueError):
        decode_access_token(token)


# ─── Reuse detection ────────────────────────────────────────────────────────


def test_reused_rotated_token_revokes_family(client, db_session):
    _register(client, "rt-reuse@example.com", "9876543224")
    first = _login(client, "rt-reuse@example.com").json()
    user = _get_user(db_session, "rt-reuse@example.com")
    second = _refresh(client, first["refresh_token"]).json()

    _assert_generic_401(_refresh(client, first["refresh_token"]))

    rows = _token_rows(db_session, user.id)
    login_family = {
        row.family_id
        for row in rows
        if row.token_hash
        in (hash_refresh_token(first["refresh_token"]), hash_refresh_token(second["refresh_token"]))
    }
    assert len(login_family) == 1
    family_rows = [row for row in rows if row.family_id in login_family]
    assert len(family_rows) == 2
    assert all(row.revoked_at is not None for row in family_rows)
    # The rotated (newest) token is dead too.
    _assert_generic_401(_refresh(client, second["refresh_token"]))
    # The register-issued session belongs to a different family and survives.
    assert len(_active_tokens(db_session, user.id)) == 1


def test_family_revocation_does_not_affect_other_sessions(client, db_session):
    _register(client, "rt-sessions@example.com", "9876543225")
    session_a = _login(client, "rt-sessions@example.com").json()
    session_b = _login(client, "rt-sessions@example.com").json()
    user = _get_user(db_session, "rt-sessions@example.com")

    rotated = _refresh(client, session_a["refresh_token"]).json()
    _assert_generic_401(_refresh(client, session_a["refresh_token"]))

    # Register session + session B survive (each is its own family).
    assert len(_active_tokens(db_session, user.id)) == 2
    # Session B's family is untouched.
    fresh_b = _refresh(client, session_b["refresh_token"])
    assert fresh_b.status_code == 200
    assert fresh_b.json()["refresh_token"] != rotated["refresh_token"]


def test_rotation_is_atomic_no_orphan_on_failure(client, db_session):
    _register(client, "rt-atomic@example.com", "9876543226")
    raw = _login(client, "rt-atomic@example.com").json()["refresh_token"]
    user = _get_user(db_session, "rt-atomic@example.com")
    # Rotate once, then replay: the family dies and no new token survives.
    _refresh(client, raw)
    _assert_generic_401(_refresh(client, raw))
    assert len(_active_tokens(db_session, user.id)) == 1  # only the register session


# ─── Logout / logout-all ────────────────────────────────────────────────────


def test_logout_revokes_current_session_only(client, db_session):
    _register(client, "rt-logout@example.com", "9876543227")
    session_a = _login(client, "rt-logout@example.com").json()
    session_b = _login(client, "rt-logout@example.com").json()
    user = _get_user(db_session, "rt-logout@example.com")

    response = _logout(client, session_a["access_token"], session_a["refresh_token"])
    assert response.status_code == 204

    _assert_generic_401(_refresh(client, session_a["refresh_token"]))
    # The other session still works (register session + session B remain).
    fresh_b = _refresh(client, session_b["refresh_token"])
    assert fresh_b.status_code == 200
    assert len(_active_tokens(db_session, user.id)) == 2


def test_logout_is_idempotent_and_ignores_unknown_tokens(client, db_session):
    _register(client, "rt-idem@example.com", "9876543228")
    body = _login(client, "rt-idem@example.com").json()
    user = _get_user(db_session, "rt-idem@example.com")

    assert _logout(client, body["access_token"], "not-a-real-token").status_code == 204
    assert len(_active_tokens(db_session, user.id)) == 2  # register + login
    assert _logout(client, body["access_token"], body["refresh_token"]).status_code == 204
    assert _logout(client, body["access_token"], body["refresh_token"]).status_code == 204
    assert len(_active_tokens(db_session, user.id)) == 1  # register session


def test_logout_cannot_revoke_another_users_session(client, db_session):
    _register(client, "rt-victim@example.com", "9876543229")
    _register(client, "rt-attacker@example.com", "9876543230")
    victim = _login(client, "rt-victim@example.com").json()
    attacker = _login(client, "rt-attacker@example.com").json()
    victim_user = _get_user(db_session, "rt-victim@example.com")

    response = _logout(client, attacker["access_token"], victim["refresh_token"])
    assert response.status_code == 204
    # Victim's sessions (register + login) are untouched.
    assert len(_active_tokens(db_session, victim_user.id)) == 2
    assert _refresh(client, victim["refresh_token"]).status_code == 200


def test_logout_all_revokes_every_session(client, db_session):
    _register(client, "rt-all@example.com", "9876543231")
    session_a = _login(client, "rt-all@example.com").json()
    session_b = _login(client, "rt-all@example.com").json()
    user = _get_user(db_session, "rt-all@example.com")

    assert _logout_all(client, session_a["access_token"]).status_code == 204

    _assert_generic_401(_refresh(client, session_a["refresh_token"]))
    _assert_generic_401(_refresh(client, session_b["refresh_token"]))
    assert len(_active_tokens(db_session, user.id)) == 0


def test_logout_all_requires_authentication(client):
    response = client.post("/auth/logout-all")
    assert response.status_code == 401


def test_logout_requires_authentication(client):
    response = client.post("/auth/logout", json={"refresh_token": "x"})
    assert response.status_code == 401


# ─── Password change ────────────────────────────────────────────────────────


def test_password_change_revokes_other_sessions_keeps_current(client, db_session):
    _register(client, "rt-pwd@example.com", "9876543232")
    current = _login(client, "rt-pwd@example.com").json()
    other = _login(client, "rt-pwd@example.com").json()
    user = _get_user(db_session, "rt-pwd@example.com")

    response = client.post(
        "/auth/change-password",
        json={
            "current_password": _PASSWORD,
            "new_password": "NewPass123!",
            "refresh_token": current["refresh_token"],
        },
        headers={"Authorization": f"Bearer {current['access_token']}"},
    )
    assert response.status_code == 200

    # Current session survives.
    assert _refresh(client, current["refresh_token"]).status_code == 200
    # The other session is gone.
    _assert_generic_401(_refresh(client, other["refresh_token"]))
    # Old password no longer works; the new one does, with a fresh session.
    assert _login(client, "rt-pwd@example.com", _PASSWORD).status_code == 401
    relogin = _login(client, "rt-pwd@example.com", "NewPass123!")
    assert relogin.status_code == 200
    assert len(_active_tokens(db_session, user.id)) == 2


def test_password_change_without_refresh_token_revokes_all(client, db_session):
    _register(client, "rt-pwd2@example.com", "9876543233")
    session = _login(client, "rt-pwd2@example.com").json()
    user = _get_user(db_session, "rt-pwd2@example.com")

    response = client.post(
        "/auth/change-password",
        json={"current_password": _PASSWORD, "new_password": "NewPass123!"},
        headers={"Authorization": f"Bearer {session['access_token']}"},
    )
    assert response.status_code == 200
    _assert_generic_401(_refresh(client, session["refresh_token"]))
    assert len(_active_tokens(db_session, user.id)) == 0


# ─── Lockout interaction ────────────────────────────────────────────────────


def test_refresh_rejected_while_account_is_locked(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "login_rate_limit_max", 100)
    monkeypatch.setattr(settings, "login_account_rate_limit_max", 100)
    _register(client, "rt-locked@example.com", "9876543234")
    body = _login(client, "rt-locked@example.com").json()

    for _ in range(5):
        assert _login(client, "rt-locked@example.com", _WRONG_PASSWORD).status_code == 401
    assert _get_user(db_session, "rt-locked@example.com").is_locked()

    _assert_generic_401(_refresh(client, body["refresh_token"]))


# ─── Rate limiting not bypassed ─────────────────────────────────────────────


def test_login_rate_limiting_still_enforced(client, monkeypatch):
    monkeypatch.setattr(settings, "login_rate_limit_max", 2)
    monkeypatch.setattr(settings, "login_account_rate_limit_max", 100)
    _register(client, "rt-ratelimit@example.com", "9876543235")

    assert _login(client, "rt-ratelimit@example.com").status_code == 200
    assert _login(client, "rt-ratelimit@example.com").status_code == 200
    assert _login(client, "rt-ratelimit@example.com").status_code == 429


# ─── Audit logging ──────────────────────────────────────────────────────────


def test_audit_logs_contain_no_token_material(client, db_session):
    _register(client, "rt-audit@example.com", "9876543236")
    body = _login(client, "rt-audit@example.com").json()
    _refresh(client, body["refresh_token"])
    _logout(client, body["access_token"], body["refresh_token"])

    rows = list(db_session.execute(select(AuditLog)).scalars())
    assert rows  # login_success + user_registered at minimum
    serialized = [str(row.after) + str(row.before) for row in rows]
    for material in (
        body["refresh_token"],
        body["access_token"],
        "password",
        "Test@1234",
    ):
        assert all(material not in snapshots for snapshots in serialized)


# ─── Migration / model metadata ─────────────────────────────────────────────


def test_migration_chain_extends_latest_head():
    with open(MIGRATION_FILE, encoding="utf-8") as fh:
        content = fh.read()
    assert 'down_revision = "20260820_0016"' in content
    assert 'revision = "20260821_0017"' in content


def test_model_metadata_indexes_match_migration():
    from sqlalchemy import inspect

    from app.models.refresh_token import RefreshToken

    indexes = {
        index.name: sorted(index.columns.keys())
        for index in inspect(RefreshToken.__table__).indexes
    }
    assert indexes["ix_refresh_tokens_token_hash"] == ["token_hash"]
    assert indexes["ix_refresh_tokens_user_id"] == ["user_id"]
    assert indexes["ix_refresh_tokens_family_id"] == ["family_id"]
