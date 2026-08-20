"""Backend tests for WIQ-V1-014 email verification."""

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
from jose import jwt as jose_jwt
from sqlalchemy import select

from app.core.config import settings
from app.core.security import (
    VERIFICATION_TOKEN_PURPOSE,
    create_access_token,
    create_verification_token,
    hash_password,
)
from app.models.audit_log import AuditLog
from app.models.user import User, UserRole
from app.services.email import EmailDeliveryError, email_outbox

_PASSWORD = "Test@1234"

MIGRATION_FILE = (
    Path(__file__).resolve().parent.parent
    / "alembic"
    / "versions"
    / "20260821_0018_email_verification.py"
)

GENERIC_BAD_TOKEN = {"detail": "Invalid or expired verification token"}
GENERIC_RESEND_RESPONSE = (
    "If the email is registered and unverified, a verification email has been sent."
)


# ─── Helpers ────────────────────────────────────────────────────────────────


def _register(client, email, phone, role="citizen"):
    response = client.post(
        "/auth/register",
        json={
            "name": "Verify User",
            "email": email,
            "password": _PASSWORD,
            "phone": phone,
            "role": role,
        },
    )
    assert response.status_code == 201
    return response.json()


def _token_from_outbox() -> str:
    assert email_outbox, "expected a captured verification email"
    html = email_outbox[-1].html_body
    match = re.search(r"https?://[^\"'\s]+/verify-email\?[^\"'\s]+", html)
    assert match, "verification link not found in captured email"
    tokens = parse_qs(urlparse(match.group(0)).query).get("token")
    assert tokens, "verification token not found in captured link"
    return tokens[0]


def _verify(client, token):
    return client.post("/auth/verify-email", json={"token": token})


def _resend(client, email):
    return client.post("/auth/resend-verification", json={"email": email})


def _audit_actions(db_session, action):
    return list(
        db_session.execute(
            select(AuditLog).where(AuditLog.action == action).order_by(AuditLog.id.asc())
        ).scalars()
    )


def _get_user(db_session, email):
    return db_session.execute(select(User).where(User.email == email)).scalar_one()


def _craft_token(
    subject: str, *, purpose: str = VERIFICATION_TOKEN_PURPOSE, expires_in: int = 60
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "purpose": purpose,
        "exp": now + timedelta(minutes=expires_in),
    }
    return jose_jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def _create_user(db_session, *, email, phone, verified=False) -> User:
    user = User(
        name="Direct User",
        email=email,
        phone=phone,
        password_hash=hash_password(_PASSWORD),
        role=UserRole.citizen,
        email_verified_at=datetime.now(timezone.utc) if verified else None,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ─── Registration integration ───────────────────────────────────────────────


def test_register_sends_verification_email_and_returns_unverified_user(client):
    body = _register(client, "reg-email@example.com", "9876543210")
    assert body["user"]["email_verified"] is False
    assert body["user"]["email_verified_at"] is None

    assert len(email_outbox) == 1
    message = email_outbox[0]
    assert message.to_email == "reg-email@example.com"
    assert "verify your waste-iq email" in message.subject.lower()
    assert "http://localhost:5173/verify-email?token=" in message.html_body
    _token_from_outbox()


def test_registration_succeeds_when_email_delivery_fails(client, monkeypatch):
    def _fail(_message):
        raise EmailDeliveryError("provider down")

    monkeypatch.setattr("app.services.email.send_email", _fail)
    body = _register(client, "fail-email@example.com", "9876543211")
    assert body["user"]["email_verified"] is False
    assert email_outbox == []


def test_verification_email_audit_recorded_on_registration(client, db_session):
    _register(client, "audit-send@example.com", "9876543212")
    events = _audit_actions(db_session, "verification_email_sent")
    assert len(events) == 1
    user = _get_user(db_session, "audit-send@example.com")
    assert events[0].actor_user_id == user.id
    assert events[0].resource_id == str(user.id)


# ─── Verification success and state transition ──────────────────────────────


def test_verify_email_success(client, db_session):
    _register(client, "verify-ok@example.com", "9876543213")
    token = _token_from_outbox()

    response = _verify(client, token)
    assert response.status_code == 200
    assert response.json() == {"message": "Email verified successfully"}

    user = _get_user(db_session, "verify-ok@example.com")
    assert user.email_verified is True
    assert user.email_verified_at is not None

    events = _audit_actions(db_session, "email_verified")
    assert len(events) == 1
    assert events[0].actor_user_id == user.id
    assert events[0].after == {"email_verified": True}


def test_verify_email_persists_across_transactions(client, db_session):
    _register(client, "verify-persist@example.com", "9876543214")
    token = _token_from_outbox()
    assert _verify(client, token).status_code == 200

    user = _get_user(db_session, "verify-persist@example.com")
    assert user.email_verified_at is not None


def test_reused_token_is_idempotent_and_single_use(client, db_session):
    _register(client, "verify-reuse@example.com", "9876543215")
    token = _token_from_outbox()

    assert _verify(client, token).json() == {"message": "Email verified successfully"}
    user = _get_user(db_session, "verify-reuse@example.com")
    verified_at = user.email_verified_at

    second = _verify(client, token)
    assert second.status_code == 200
    assert second.json() == {"message": "Email already verified"}

    user = _get_user(db_session, "verify-reuse@example.com")
    assert user.email_verified_at == verified_at
    assert len(_audit_actions(db_session, "email_verified")) == 1


def test_already_verified_account_is_idempotent(client, db_session):
    user = _create_user(
        db_session, email="pre-verified@example.com", phone="9876543216", verified=True
    )
    token = create_verification_token(str(user.id))

    response = _verify(client, token)
    assert response.status_code == 200
    assert response.json() == {"message": "Email already verified"}
    assert _audit_actions(db_session, "email_verified") == []


# ─── Rejected tokens (all identical generic responses) ──────────────────────


def test_verify_email_with_invalid_token(client, db_session):
    _register(client, "verify-invalid@example.com", "9876543217")
    response = _verify(client, "definitely-not-a-real-token")
    assert response.status_code == 400
    assert response.json() == GENERIC_BAD_TOKEN
    assert _get_user(db_session, "verify-invalid@example.com").email_verified is False


def test_verify_email_with_expired_token(client, db_session):
    _register(client, "verify-expired@example.com", "9876543218")
    user = _get_user(db_session, "verify-expired@example.com")
    expired = _craft_token(str(user.id), expires_in=-60)

    response = _verify(client, expired)
    assert response.status_code == 400
    assert response.json() == GENERIC_BAD_TOKEN
    assert _get_user(db_session, "verify-expired@example.com").email_verified is False


def test_verify_email_with_malformed_token(client):
    response = _verify(client, "not-a-jwt-at-all")
    assert response.status_code == 400
    assert response.json() == GENERIC_BAD_TOKEN


def test_verify_email_with_wrong_purpose_token(client, db_session):
    _register(client, "verify-purpose@example.com", "9876543219")
    user = _get_user(db_session, "verify-purpose@example.com")
    wrong_purpose = _craft_token(str(user.id), purpose="password_reset")

    response = _verify(client, wrong_purpose)
    assert response.status_code == 400
    assert response.json() == GENERIC_BAD_TOKEN


def test_verify_email_rejects_access_token(client, db_session):
    _register(client, "verify-access@example.com", "9876543220")
    user = _get_user(db_session, "verify-access@example.com")

    response = _verify(client, create_access_token(str(user.id)))
    assert response.status_code == 400
    assert response.json() == GENERIC_BAD_TOKEN


def test_verify_email_with_token_for_unknown_user(client):
    response = _verify(client, _craft_token("999999999"))
    assert response.status_code == 400
    assert response.json() == GENERIC_BAD_TOKEN


def test_verify_email_with_non_numeric_subject(client):
    response = _verify(client, _craft_token("not-a-number"))
    assert response.status_code == 400
    assert response.json() == GENERIC_BAD_TOKEN


def test_verify_email_requires_token_field(client):
    response = client.post("/auth/verify-email", json={})
    assert response.status_code == 422


# ─── Login / session interaction ────────────────────────────────────────────


def test_unverified_user_can_login(client):
    _register(client, "verify-login@example.com", "9876543221")
    response = client.post(
        "/auth/login", json={"email": "verify-login@example.com", "password": _PASSWORD}
    )
    assert response.status_code == 200
    assert response.json()["user"]["email_verified"] is False


def test_auth_me_exposes_email_verified_state(client):
    _register(client, "verify-me@example.com", "9876543222")
    body = client.post(
        "/auth/login", json={"email": "verify-me@example.com", "password": _PASSWORD}
    ).json()
    headers = {"Authorization": f"Bearer {body['access_token']}"}

    me_before = client.get("/auth/me", headers=headers).json()
    assert me_before["email_verified"] is False
    assert me_before["email_verified_at"] is None

    _verify(client, _token_from_outbox())
    me_after = client.get("/auth/me", headers=headers).json()
    assert me_after["email_verified"] is True
    assert me_after["email_verified_at"] is not None


def test_refresh_sessions_survive_verification(client):
    body = _register(client, "verify-refresh@example.com", "9876543223")
    refreshed = client.post("/auth/refresh", json={"refresh_token": body["refresh_token"]})
    assert refreshed.status_code == 200

    _verify(client, _token_from_outbox())

    again = client.post("/auth/refresh", json={"refresh_token": refreshed.json()["refresh_token"]})
    assert again.status_code == 200


# ─── Resend verification ────────────────────────────────────────────────────


def test_resend_verification_sends_email(client, db_session):
    _register(client, "verify-resend@example.com", "9876543224")
    assert len(email_outbox) == 1

    response = _resend(client, "verify-resend@example.com")
    assert response.status_code == 200
    assert response.json() == {"message": GENERIC_RESEND_RESPONSE}

    assert len(email_outbox) == 2
    assert email_outbox[1].to_email == "verify-resend@example.com"
    assert len(_audit_actions(db_session, "verification_email_sent")) == 2


def test_resend_verification_sends_a_fresh_usable_token(client):
    _register(client, "verify-fresh@example.com", "9876543225")
    first_token = _token_from_outbox()
    _resend(client, "verify-fresh@example.com")
    second_token = _token_from_outbox()

    assert second_token != first_token
    assert _verify(client, second_token).status_code == 200


def test_resend_verification_unknown_email_is_generic(client):
    response = _resend(client, "nobody@example.com")
    assert response.status_code == 200
    assert response.json() == {"message": GENERIC_RESEND_RESPONSE}
    assert email_outbox == []


def test_resend_verification_verified_account_is_generic_and_sends_nothing(client, db_session):
    _register(client, "verify-done@example.com", "9876543226")
    _verify(client, _token_from_outbox())
    assert len(email_outbox) == 1

    response = _resend(client, "verify-done@example.com")
    assert response.status_code == 200
    assert response.json() == {"message": GENERIC_RESEND_RESPONSE}
    assert len(email_outbox) == 1
    assert len(_audit_actions(db_session, "verification_email_sent")) == 1


def test_resend_verification_is_rate_limited(client, monkeypatch):
    monkeypatch.setattr(settings, "resend_verification_rate_limit_max", 2)
    _register(client, "verify-ratelimit@example.com", "9876543227")

    assert _resend(client, "verify-ratelimit@example.com").status_code == 200
    assert _resend(client, "verify-ratelimit@example.com").status_code == 200
    assert _resend(client, "verify-ratelimit@example.com").status_code == 429


def test_resend_verification_rate_limit_applies_to_unknown_emails_too(client, monkeypatch):
    monkeypatch.setattr(settings, "resend_verification_rate_limit_max", 1)

    assert _resend(client, "nobody@example.com").status_code == 200
    # Same IP budget is consumed regardless of whether the email exists, so
    # the 429 cannot be used to enumerate accounts.
    assert _resend(client, "someoneelse@example.com").status_code == 429


# ─── Audit hygiene ──────────────────────────────────────────────────────────


def test_audit_logs_and_logs_contain_no_verification_token(client, db_session, caplog):
    with caplog.at_level("INFO"):
        _register(client, "verify-audit@example.com", "9876543228")
        token = _token_from_outbox()
        _verify(client, token)
        _resend(client, "verify-audit@example.com")

    assert "email_verified" in [row.action for row in _audit_actions(db_session, "email_verified")]
    serialized = [
        str(row.after) + str(row.before) for row in _audit_actions(db_session, "email_verified")
    ]
    assert token not in "".join(serialized)
    assert token not in caplog.text
    assert "verify-audit@example.com/verify-email" not in caplog.text


def test_console_provider_logs_redacted_summary_only(caplog):
    from app.services.email import OutgoingEmail, send_email

    with caplog.at_level("INFO"):
        send_email(
            OutgoingEmail(
                to_email="target@example.com",
                subject="Secret subject",
                html_body="<a href='http://x/verify-email?token=SUPERSECRET'>link</a>",
                text_body="body SUPERSECRET",
            )
        )
    assert "SUPERSECRET" not in caplog.text
    assert "target@example.com" in caplog.text


# ─── Transaction / rollback behaviour ───────────────────────────────────────


def test_verify_email_rolls_back_when_audit_fails(db_session, monkeypatch):
    user = _create_user(db_session, email="verify-rollback@example.com", phone="9876543229")
    token = create_verification_token(str(user.id))

    def _boom(*_args, **_kwargs):
        raise RuntimeError("audit backend unavailable")

    monkeypatch.setattr("app.services.email_verification._audit_service.record", _boom)

    with pytest.raises(RuntimeError):
        from app.services.email_verification import verify_email

        verify_email(db_session, token)

    db_session.rollback()
    user = db_session.get(User, user.id)
    assert user.email_verified_at is None
    assert user.email_verified is False
    assert _audit_actions(db_session, "email_verified") == []


# ─── Migration / model metadata ─────────────────────────────────────────────


def test_migration_chain_extends_latest_head():
    with open(MIGRATION_FILE, encoding="utf-8") as fh:
        content = fh.read()
    assert 'down_revision = "20260821_0017"' in content
    assert 'revision = "20260821_0018"' in content


def test_model_metadata_includes_email_verified_at():
    column = User.__table__.columns["email_verified_at"]
    assert column.nullable is True
    assert isinstance(User.email_verified, property)
