"""Backend tests for WIQ-V1-015 forgot & reset password."""

import re
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

from jose import jwt as jose_jwt
from sqlalchemy import select

from app.core.config import settings
from app.core.security import (
    VERIFICATION_TOKEN_PURPOSE,
    create_access_token,
    create_password_reset_token,
    hash_password,
    hash_refresh_token,
    password_fingerprint,
    verify_password,
)
from app.models.audit_log import AuditLog
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole
from app.services.email import EmailDeliveryError, email_outbox

_PASSWORD = "Test@1234"
_NEW_PASSWORD = "Brand@New456"

GENERIC_FORGOT_MESSAGE = "If the email is registered, a password reset link has been sent."
GENERIC_BAD_RESET_TOKEN = {"detail": "Invalid or expired reset token"}
GENERIC_RESET_SUCCESS = {"message": "Password has been reset successfully"}


# ─── Helpers ────────────────────────────────────────────────────────────────


def _create_user(db_session, *, email, phone) -> User:
    user = User(
        name="Reset User",
        email=email,
        phone=phone,
        password_hash=hash_password(_PASSWORD),
        role=UserRole.citizen,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _forgot(client, email):
    return client.post("/auth/forgot-password", json={"email": email})


def _reset(client, token, new_password=_NEW_PASSWORD):
    return client.post("/auth/reset-password", json={"token": token, "new_password": new_password})


def _token_from_outbox() -> str:
    assert email_outbox, "expected a captured password reset email"
    html = email_outbox[-1].html_body
    match = re.search(r"https?://[^\"'\s]+/reset-password\?[^\"'\s]+", html)
    assert match, "reset link not found in captured email"
    tokens = parse_qs(urlparse(match.group(0)).query).get("token")
    assert tokens, "reset token not found in captured link"
    return tokens[0]


def _audit_actions(db_session, action):
    return list(
        db_session.execute(
            select(AuditLog).where(AuditLog.action == action).order_by(AuditLog.id.asc())
        ).scalars()
    )


def _get_user(db_session, email):
    return db_session.execute(select(User).where(User.email == email)).scalar_one()


def _craft_token(
    subject: str,
    *,
    purpose: str = "password_reset",
    pwd: str | None = None,
    expires_in: int = 30,
    secret: str | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "purpose": purpose,
        "pwd": pwd or "irrelevant-fingerprint",
        "exp": now + timedelta(minutes=expires_in),
    }
    return jose_jwt.encode(
        payload, secret or settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def _login(client, email, password):
    return client.post("/auth/login", json={"email": email, "password": password})


# ─── Forgot password ────────────────────────────────────────────────────────


def test_forgot_password_known_email_sends_reset_email(client, db_session):
    _create_user(db_session, email="forgot-known@example.com", phone="9876500001")

    response = _forgot(client, "forgot-known@example.com")

    assert response.status_code == 200
    assert response.json() == {"message": GENERIC_FORGOT_MESSAGE}
    assert len(email_outbox) == 1
    message = email_outbox[0]
    assert message.to_email == "forgot-known@example.com"
    assert "reset your waste-iq password" in message.subject.lower()
    assert "http://localhost:5173/reset-password?token=" in message.html_body


def test_forgot_password_unknown_email_is_generic_and_sends_nothing(client):
    response = _forgot(client, "nobody@example.com")

    assert response.status_code == 200
    assert response.json() == {"message": GENERIC_FORGOT_MESSAGE}
    assert email_outbox == []


def test_forgot_password_identical_response_for_known_and_unknown_emails(client, db_session):
    _create_user(db_session, email="identical@example.com", phone="9876500002")

    known = _forgot(client, "identical@example.com")
    unknown = _forgot(client, "ghost@example.com")

    assert known.status_code == unknown.status_code == 200
    assert known.json() == unknown.json()


def test_forgot_password_normalizes_email(client, db_session):
    _create_user(db_session, email="normalized@example.com", phone="9876500003")

    response = _forgot(client, "  Normalized@Example.COM  ")

    assert response.status_code == 200
    # Background delivery is keyed off the stored account; the outbox proves
    # the lookup matched despite casing/whitespace.
    assert len(email_outbox) == 1
    assert email_outbox[0].to_email == "normalized@example.com"


def test_forgot_password_requires_valid_body(client):
    assert client.post("/auth/forgot-password", json={}).status_code == 422
    assert client.post("/auth/forgot-password", json={"email": "not-an-email"}).status_code == 422


def test_forgot_password_records_audit_event_after_delivery(client, db_session):
    user = _create_user(db_session, email="forgot-audit@example.com", phone="9876500004")

    _forgot(client, "forgot-audit@example.com")

    events = _audit_actions(db_session, "password_reset_email_sent")
    assert len(events) == 1
    assert events[0].actor_user_id == user.id
    assert events[0].resource_id == str(user.id)


def test_forgot_password_delivery_failure_never_fails_request(client, db_session, monkeypatch):
    _create_user(db_session, email="forgot-fail@example.com", phone="9876500005")

    def _fail(_message):
        raise EmailDeliveryError("provider down")

    monkeypatch.setattr("app.services.email.send_email", _fail)

    response = _forgot(client, "forgot-fail@example.com")

    assert response.status_code == 200
    assert response.json() == {"message": GENERIC_FORGOT_MESSAGE}
    assert _audit_actions(db_session, "password_reset_email_sent") == []


def test_forgot_password_is_rate_limited(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "forgot_password_rate_limit_max", 2)
    _create_user(db_session, email="forgot-limit@example.com", phone="9876500006")

    assert _forgot(client, "forgot-limit@example.com").status_code == 200
    assert _forgot(client, "forgot-limit@example.com").status_code == 200
    limited = _forgot(client, "forgot-limit@example.com")
    assert limited.status_code == 429
    assert "retry-after" in {key.lower() for key in limited.headers}


def test_forgot_password_rate_limit_applies_to_unknown_emails_too(client, monkeypatch):
    monkeypatch.setattr(settings, "forgot_password_rate_limit_max", 1)

    assert _forgot(client, "nobody1@example.com").status_code == 200
    # Same IP budget regardless of whether the email exists, so a 429 cannot
    # be used to enumerate accounts.
    assert _forgot(client, "nobody2@example.com").status_code == 429


def test_background_delivery_task_skips_missing_user(db_session):
    from app.services.password_reset import complete_password_reset_email_delivery

    complete_password_reset_email_delivery(999999)

    assert email_outbox == []
    assert _audit_actions(db_session, "password_reset_email_sent") == []


# ─── Reset password: success path ───────────────────────────────────────────


def test_reset_password_success_changes_hash(client, db_session):
    user = _create_user(db_session, email="reset-ok@example.com", phone="9876500010")
    old_hash = user.password_hash
    _forgot(client, "reset-ok@example.com")
    token = _token_from_outbox()

    response = _reset(client, token)

    assert response.status_code == 200
    assert response.json() == GENERIC_RESET_SUCCESS

    db_session.refresh(user)
    assert user.password_hash != old_hash
    assert verify_password(_NEW_PASSWORD, user.password_hash)


def test_reset_password_old_password_rejected_new_accepted(client, db_session):
    _create_user(db_session, email="reset-login@example.com", phone="9876500011")
    _forgot(client, "reset-login@example.com")
    token = _token_from_outbox()
    assert _reset(client, token).status_code == 200

    assert _login(client, "reset-login@example.com", _PASSWORD).status_code == 401
    assert _login(client, "reset-login@example.com", _NEW_PASSWORD).status_code == 200


def test_reset_password_revokes_all_refresh_sessions(client, db_session):
    user = _create_user(db_session, email="reset-sessions@example.com", phone="9876500012")
    active = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token("session-token-raw"),
        family_id="family-1",
        user_agent="pytest",
        expires_at=datetime.now(timezone.utc) + timedelta(days=5),
    )
    db_session.add(active)
    db_session.commit()

    _forgot(client, "reset-sessions@example.com")
    assert _reset(client, _token_from_outbox()).status_code == 200

    db_session.refresh(active)
    assert active.revoked_at is not None
    remaining = (
        db_session.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)
            )
        )
        .scalars()
        .all()
    )
    assert remaining == []


def test_refresh_endpoint_rejects_token_after_reset(client, db_session):
    """End to end: login, reset via token, then refresh must fail."""
    _create_user(db_session, email="refresh-e2e@example.com", phone="9876500013")
    login = _login(client, "refresh-e2e@example.com", _PASSWORD)
    refresh_token = login.json()["refresh_token"]

    _forgot(client, "refresh-e2e@example.com")
    assert _reset(client, _token_from_outbox()).status_code == 200

    refreshed = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert refreshed.status_code == 401


def test_reset_password_records_audit_event(client, db_session):
    _create_user(db_session, email="reset-audit@example.com", phone="9876500014")
    _forgot(client, "reset-audit@example.com")

    assert _reset(client, _token_from_outbox()).status_code == 200

    events = _audit_actions(db_session, "password_reset")
    assert len(events) == 1
    assert events[0].actor_user_id is not None
    assert events[0].resource == "user"


def test_audit_logs_and_logs_contain_no_token_or_password(client, db_session, caplog):
    _create_user(db_session, email="hygiene@example.com", phone="9876500015")
    with caplog.at_level("INFO"):
        _forgot(client, "hygiene@example.com")
        token = _token_from_outbox()
        assert _reset(client, token).status_code == 200

    serialized = "".join(
        str(row.after) + str(row.before)
        for row in (
            *_audit_actions(db_session, "password_reset"),
            *_audit_actions(db_session, "password_reset_email_sent"),
        )
    )
    assert token not in serialized
    assert token not in caplog.text
    assert _PASSWORD not in serialized
    assert _NEW_PASSWORD not in serialized


# ─── Reset password: rejected tokens (all identical generic responses) ──────


def test_reset_password_with_expired_token(client, db_session):
    user = _create_user(db_session, email="reset-expired@example.com", phone="9876500020")
    expired = _craft_token(
        str(user.id), pwd=password_fingerprint(user.password_hash), expires_in=-5
    )

    response = _reset(client, expired)

    assert response.status_code == 400
    assert response.json() == GENERIC_BAD_RESET_TOKEN
    db_session.refresh(user)
    assert verify_password(_PASSWORD, user.password_hash)


def test_reset_password_with_malformed_token(client):
    response = _reset(client, "not-a-jwt-at-all")
    assert response.status_code == 400
    assert response.json() == GENERIC_BAD_RESET_TOKEN


def test_reset_password_with_wrong_signature_token(client, db_session):
    user = _create_user(db_session, email="reset-signature@example.com", phone="9876500021")
    forged = _craft_token(
        str(user.id),
        pwd=password_fingerprint(user.password_hash),
        secret="attacker-controlled-secret",
    )

    response = _reset(client, forged)

    assert response.status_code == 400
    assert response.json() == GENERIC_BAD_RESET_TOKEN


def test_reset_password_with_verification_purpose_token(client, db_session):
    """An email-verification token must never work as a reset token."""
    user = _create_user(db_session, email="reset-purpose@example.com", phone="9876500022")
    fingerprint = password_fingerprint(user.password_hash)
    verification = _craft_token(str(user.id), purpose=VERIFICATION_TOKEN_PURPOSE, pwd=fingerprint)

    response = _reset(client, verification)

    assert response.status_code == 400
    assert response.json() == GENERIC_BAD_RESET_TOKEN


def test_reset_password_rejects_access_token(client, db_session):
    user = _create_user(db_session, email="reset-access@example.com", phone="9876500023")

    response = _reset(client, create_access_token(str(user.id)))

    assert response.status_code == 400
    assert response.json() == GENERIC_BAD_RESET_TOKEN


def test_reset_password_with_token_for_unknown_user(client):
    response = _reset(client, _craft_token("999999999"))

    assert response.status_code == 400
    assert response.json() == GENERIC_BAD_RESET_TOKEN


def test_reset_password_with_non_numeric_subject(client):
    response = _reset(client, _craft_token("not-a-number"))
    assert response.status_code == 400
    assert response.json() == GENERIC_BAD_RESET_TOKEN


def test_reset_password_missing_fields_fails(client):
    assert client.post("/auth/reset-password", json={}).status_code == 422
    assert client.post("/auth/reset-password", json={"token": "x"}).status_code == 422


# ─── Password policy on reset ───────────────────────────────────────────────


def test_reset_password_rejects_short_password(client, db_session):
    user = _create_user(db_session, email="reset-short@example.com", phone="9876500030")
    _forgot(client, "reset-short@example.com")
    token = _token_from_outbox()

    response = _reset(client, token, "short")

    assert response.status_code == 422
    db_session.refresh(user)
    assert verify_password(_PASSWORD, user.password_hash)


def test_reset_password_rejects_current_password(client, db_session):
    user = _create_user(db_session, email="reset-same@example.com", phone="9876500031")
    _forgot(client, "reset-same@example.com")
    token = _token_from_outbox()

    response = _reset(client, token, _PASSWORD)

    assert response.status_code == 400
    db_session.refresh(user)
    assert verify_password(_PASSWORD, user.password_hash)


# ─── Single-use semantics (fingerprint claim) ───────────────────────────────


def test_reset_token_cannot_be_reused_after_successful_reset(client, db_session):
    _create_user(db_session, email="reset-reuse@example.com", phone="9876500040")
    _forgot(client, "reset-reuse@example.com")
    token = _token_from_outbox()

    assert _reset(client, token).status_code == 200
    replayed = _reset(client, token)

    assert replayed.status_code == 400
    assert replayed.json() == GENERIC_BAD_RESET_TOKEN
    # The replay must not have changed anything.
    user = _get_user(db_session, "reset-reuse@example.com")
    assert verify_password(_NEW_PASSWORD, user.password_hash)


def test_older_reset_tokens_die_after_a_completed_reset(client, db_session):
    """Two outstanding tokens: completing one invalidates the other."""
    user = _create_user(db_session, email="reset-stale@example.com", phone="9876500041")
    stale_token = create_password_reset_token(
        str(user.id), password_fingerprint(user.password_hash)
    )

    _forgot(client, "reset-stale@example.com")
    fresh_token = _token_from_outbox()
    assert _reset(client, fresh_token).status_code == 200

    response = _reset(client, stale_token)
    assert response.status_code == 400
    assert response.json() == GENERIC_BAD_RESET_TOKEN


def test_reset_tokens_die_after_change_password(client, db_session):
    """A regular change-password also invalidates outstanding reset tokens."""
    user = _create_user(db_session, email="reset-change@example.com", phone="9876500042")
    outstanding = create_password_reset_token(
        str(user.id), password_fingerprint(user.password_hash)
    )

    headers = {"Authorization": f"Bearer {create_access_token(str(user.id))}"}
    changed = client.post(
        "/auth/change-password",
        json={"current_password": _PASSWORD, "new_password": _NEW_PASSWORD},
        headers=headers,
    )
    assert changed.status_code == 200

    response = _reset(client, outstanding)
    assert response.status_code == 400
    assert response.json() == GENERIC_BAD_RESET_TOKEN


# ─── Lockout interaction ────────────────────────────────────────────────────


def test_locked_account_can_still_request_and_complete_reset(client, db_session):
    """Lockout is temporary; resetting the password must stay possible."""
    user = _create_user(db_session, email="reset-locked@example.com", phone="9876500050")
    for _ in range(settings.lockout_failed_attempt_threshold):
        _login(client, "reset-locked@example.com", "WrongPassword1")
    db_session.refresh(user)
    assert user.is_locked()

    assert _forgot(client, "reset-locked@example.com").status_code == 200
    response = _reset(client, _token_from_outbox())
    assert response.status_code == 200

    db_session.refresh(user)
    assert verify_password(_NEW_PASSWORD, user.password_hash)
