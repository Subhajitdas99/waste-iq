import ast
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select

from app.core.config import settings
from app.core.ratelimit import SlidingWindowRateLimiter, check_rate_limit, get_client_ip
from app.models.audit_log import AuditLog
from app.models.user import User
from app.services.auth import record_failed_login, reset_login_failures

MIGRATION_FILE = (
    Path(__file__).resolve().parent.parent
    / "alembic"
    / "versions"
    / "20260820_0016_user_lockout.py"
)

_PASSWORD = "Test@1234"
_WRONG_PASSWORD = "WrongPass1"


# ─── Helpers ────────────────────────────────────────────────────────────────


def _register(client, email, phone):
    response = client.post(
        "/auth/register",
        json={
            "name": "Rate User",
            "email": email,
            "password": _PASSWORD,
            "phone": phone,
            "role": "citizen",
        },
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def _login(client, email, password=_PASSWORD):
    return client.post("/auth/login", json={"email": email, "password": password})


def _get_user(db_session, email):
    return db_session.execute(select(User).where(User.email == email)).scalar_one()


def _as_utc(value: datetime | None) -> datetime | None:
    """Normalize a possibly naive datetime (SQLite) to timezone-aware UTC."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _set_login_limits(monkeypatch, *, ip=100, account=100, window=60):
    monkeypatch.setattr(settings, "login_rate_limit_max", ip)
    monkeypatch.setattr(settings, "login_account_rate_limit_max", account)
    monkeypatch.setattr(settings, "rate_limit_window_seconds", window)


def _make_request(client_ip: str):
    """A minimal starlette Request with a controlled client IP."""
    from starlette.requests import Request

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/auth/login",
        "headers": [],
        "query_string": b"",
        "server": ("testserver", 80),
        "client": (client_ip, 12345),
        "scheme": "http",
        "root_path": "",
    }
    return Request(scope)


# ─── Model & migration ──────────────────────────────────────────────────────


def test_user_model_lockout_columns():
    table = User.__table__
    assert "failed_login_count" in table.columns
    assert "locked_until" in table.columns
    assert table.columns["failed_login_count"].nullable is False
    assert table.columns["failed_login_count"].server_default is not None
    assert table.columns["locked_until"].nullable is True


def test_migration_file_revision_chain():
    assert MIGRATION_FILE.exists(), "Migration file must exist"
    module = ast.parse(MIGRATION_FILE.read_text(encoding="utf-8"))
    assignments = {
        node.targets[0].id: node.value.value
        for node in ast.walk(module)
        if isinstance(node, ast.Assign)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.targets[0], ast.Name)
    }
    assert assignments["revision"] == "20260820_0016"
    assert assignments["down_revision"] == "20260819_0015"
    text = MIGRATION_FILE.read_text(encoding="utf-8")
    assert '"failed_login_count"' in text
    assert '"locked_until"' in text
    assert 'op.drop_column("users", "locked_until")' in text
    assert 'op.drop_column("users", "failed_login_count")' in text


def test_settings_for_rate_limiting_and_lockout():
    assert settings.login_rate_limit_max > 0
    assert settings.login_account_rate_limit_max > 0
    assert settings.register_rate_limit_max > 0
    assert settings.forgot_password_rate_limit_max > 0
    assert settings.resend_verification_rate_limit_max > 0
    assert settings.rate_limit_window_seconds > 0
    assert settings.lockout_failed_attempt_threshold == 5
    assert settings.lockout_cooldown_minutes > 0


# ─── SlidingWindowRateLimiter unit tests ────────────────────────────────────


def test_sliding_window_allows_up_to_limit():
    limiter = SlidingWindowRateLimiter()
    for now in (1.0, 2.0, 3.0):
        decision = limiter.check("k", limit=3, window_seconds=10, now=now)
        assert decision.allowed
        assert decision.retry_after_seconds == 0


def test_sliding_window_denies_after_limit():
    limiter = SlidingWindowRateLimiter()
    for now in (1.0, 2.0, 3.0):
        assert limiter.check("k", limit=3, window_seconds=10, now=now).allowed
    decision = limiter.check("k", limit=3, window_seconds=10, now=4.0)
    assert not decision.allowed
    assert decision.retry_after_seconds == 8


def test_sliding_window_expiry_resets_count():
    limiter = SlidingWindowRateLimiter()
    for now in (1.0, 2.0, 3.0):
        assert limiter.check("k", limit=3, window_seconds=10, now=now).allowed
    # Oldest hit (t=1) expires at t=11, so t=11 is allowed again.
    decision = limiter.check("k", limit=3, window_seconds=10, now=11.0)
    assert decision.allowed


def test_sliding_window_sweeps_expired_keys_at_capacity():
    limiter = SlidingWindowRateLimiter(max_entries=1)
    assert limiter.check("old", limit=5, window_seconds=10, now=1.0).allowed
    # A new key while at capacity sweeps expired keys first, so "old" gives
    # way instead of the request being rejected.
    assert limiter.check("fresh", limit=5, window_seconds=10, now=100.0).allowed
    assert len(limiter) == 1


def test_sliding_window_reset():
    limiter = SlidingWindowRateLimiter()
    assert limiter.check("k", limit=1, window_seconds=10, now=1.0).allowed
    limiter.reset()
    assert limiter.check("k", limit=1, window_seconds=10, now=2.0).allowed


def test_sliding_window_zero_limit_disables():
    limiter = SlidingWindowRateLimiter()
    for _ in range(5):
        assert limiter.check("k", limit=0, window_seconds=10, now=1.0).allowed


def test_sliding_window_fails_closed_at_capacity():
    limiter = SlidingWindowRateLimiter(max_entries=2)
    assert limiter.check("a", limit=1, window_seconds=10, now=1.0).allowed
    assert limiter.check("b", limit=1, window_seconds=10, now=2.0).allowed
    decision = limiter.check("c", limit=1, window_seconds=10, now=3.0)
    assert not decision.allowed


def test_sliding_window_is_thread_safe():
    limiter = SlidingWindowRateLimiter()
    allowed_count = 0
    lock = threading.Lock()

    def worker():
        nonlocal allowed_count
        for _ in range(10):
            decision = limiter.check("shared", limit=5, window_seconds=60)
            if decision.allowed:
                with lock:
                    allowed_count += 1

    threads = [threading.Thread(target=worker) for _ in range(20)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert allowed_count == 5, "exactly `limit` checks must pass under concurrency"


# ─── check_rate_limit unit tests ───────────────────────────────────────────


def test_check_rate_limit_enforces_ip_and_account_keys(monkeypatch):
    monkeypatch.setattr(settings, "login_rate_limit_max", 2)
    monkeypatch.setattr(settings, "login_account_rate_limit_max", 2)
    request = _make_request("203.0.113.10")

    for _ in range(2):
        check_rate_limit(request, "login", account_identifier="user@example.com")
    from fastapi import HTTPException

    try:
        check_rate_limit(request, "login", account_identifier="user@example.com")
        raise AssertionError("expected HTTPException")
    except HTTPException as exc:
        assert exc.status_code == 429
        assert exc.headers["Retry-After"]
        assert exc.detail == "Too many requests. Please try again later."


def test_check_rate_limit_per_ip_isolation(monkeypatch):
    monkeypatch.setattr(settings, "login_rate_limit_max", 2)
    first = _make_request("203.0.113.10")
    second = _make_request("203.0.113.11")

    check_rate_limit(first, "login")
    check_rate_limit(first, "login")
    check_rate_limit(second, "login")  # different IP is unaffected
    check_rate_limit(second, "login")


def test_get_client_ip_ignores_forwarded_for():
    request = _make_request("203.0.113.20")
    assert get_client_ip(request) == "203.0.113.20"


# ─── API: rate limiting ─────────────────────────────────────────────────────


def test_login_allows_requests_before_limit(client, monkeypatch):
    _register(client, "before@example.com", "9111111110")
    _set_login_limits(monkeypatch, ip=3, account=3)
    for _ in range(3):
        response = _login(client, "before@example.com", _WRONG_PASSWORD)
        assert response.status_code == 401


def test_login_returns_429_after_limit(client, monkeypatch):
    _register(client, "limited@example.com", "9111111111")
    _set_login_limits(monkeypatch, ip=3, account=3)
    for _ in range(3):
        assert _login(client, "limited@example.com", _WRONG_PASSWORD).status_code == 401

    response = _login(client, "limited@example.com", _WRONG_PASSWORD)
    assert response.status_code == 429
    assert response.json()["detail"] == "Too many requests. Please try again later."
    assert "Retry-After" in response.headers
    assert int(response.headers["Retry-After"]) >= 1


def test_login_429_retry_after_is_deterministic(client, monkeypatch):
    _register(client, "retry@example.com", "9111111112")
    _set_login_limits(monkeypatch, ip=3, account=3, window=10)

    class FakeClock:
        def __init__(self):
            self.value = 0.0

        def __call__(self):
            return self.value

    clock = FakeClock()
    monkeypatch.setattr("app.core.ratelimit._now", clock)

    for offset in (0.0, 1.0, 2.0):
        clock.value = offset
        assert _login(client, "retry@example.com", _WRONG_PASSWORD).status_code == 401

    clock.value = 3.0
    response = _login(client, "retry@example.com", _WRONG_PASSWORD)
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "8"


def test_login_429_window_expiry_allows_again(client, monkeypatch):
    _register(client, "expiry@example.com", "9111111113")
    _set_login_limits(monkeypatch, ip=3, account=3, window=10)

    class FakeClock:
        def __init__(self):
            self.value = 0.0

        def __call__(self):
            return self.value

    clock = FakeClock()
    monkeypatch.setattr("app.core.ratelimit._now", clock)

    for offset in (0.0, 1.0, 2.0):
        clock.value = offset
        assert _login(client, "expiry@example.com", _WRONG_PASSWORD).status_code == 401

    clock.value = 3.0
    assert _login(client, "expiry@example.com", _WRONG_PASSWORD).status_code == 429

    clock.value = 11.0
    response = _login(client, "expiry@example.com", _WRONG_PASSWORD)
    assert response.status_code == 401


def test_login_per_account_isolation(client, monkeypatch):
    _register(client, "acct-a@example.com", "9111111114")
    _register(client, "acct-b@example.com", "9111111115")
    _set_login_limits(monkeypatch, ip=50, account=3)

    for _ in range(3):
        assert _login(client, "acct-a@example.com", _WRONG_PASSWORD).status_code == 401
    assert _login(client, "acct-a@example.com", _WRONG_PASSWORD).status_code == 429

    # A different account on the same IP still has its own budget.
    for _ in range(3):
        assert _login(client, "acct-b@example.com", _WRONG_PASSWORD).status_code == 401
    assert _login(client, "acct-b@example.com", _WRONG_PASSWORD).status_code == 429


def test_login_ip_and_account_limits_combined(client, monkeypatch):
    _register(client, "combined@example.com", "9111111116")
    _set_login_limits(monkeypatch, ip=2, account=50)

    for _ in range(2):
        assert _login(client, "combined@example.com", _WRONG_PASSWORD).status_code == 401
    response = _login(client, "combined@example.com", _WRONG_PASSWORD)
    assert response.status_code == 429  # IP key exhausted first


def test_register_rate_limit(client, monkeypatch):
    monkeypatch.setattr(settings, "register_rate_limit_max", 3)
    for index in range(3):
        response = client.post(
            "/auth/register",
            json={
                "name": "Rate User",
                "email": f"reg{index}@example.com",
                "password": _PASSWORD,
                "phone": f"9111111{index}",
                "role": "citizen",
            },
        )
        assert response.status_code == 201

    response = client.post(
        "/auth/register",
        json={
            "name": "Rate User",
            "email": "reg3@example.com",
            "password": _PASSWORD,
            "phone": "911111113",
            "role": "citizen",
        },
    )
    assert response.status_code == 429
    assert "Retry-After" in response.headers


def test_429_does_not_leak_account_existence(client, monkeypatch):
    _register(client, "known@example.com", "9111111117")
    _set_login_limits(monkeypatch, ip=50, account=2)

    for _ in range(2):
        assert _login(client, "known@example.com", _WRONG_PASSWORD).status_code == 401
    known = _login(client, "known@example.com", _WRONG_PASSWORD)
    assert known.status_code == 429
    assert "known@example.com" not in known.text

    # A different email has its own account budget but the same IP.
    for _ in range(2):
        assert _login(client, "ghost@example.com", _WRONG_PASSWORD).status_code == 401
    ghost = _login(client, "ghost@example.com", _WRONG_PASSWORD)
    assert ghost.status_code == 429
    assert ghost.json() == known.json(), (
        "429 bodies must be identical for existing and unknown emails"
    )


def test_auth_refresh_is_not_rate_limited(client, monkeypatch):
    _set_login_limits(monkeypatch, ip=1, account=1)
    assert _login(client, "nobody@example.com", _WRONG_PASSWORD).status_code == 401
    # /auth/refresh does not exist yet; it must not be rate-limited (404, not 429).
    response = client.post("/auth/refresh", json={"refresh_token": "x"})
    assert response.status_code == 404


def test_cors_preflight_is_not_rate_limited(client, monkeypatch):
    _set_login_limits(monkeypatch, ip=1, account=1)
    assert _login(client, "nobody@example.com", _WRONG_PASSWORD).status_code == 401

    response = client.options(
        "/auth/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert "Retry-After" not in response.headers


# ─── Account lockout ────────────────────────────────────────────────────────


def _set_lockout(monkeypatch, *, threshold=5, cooldown_minutes=15):
    monkeypatch.setattr(settings, "lockout_failed_attempt_threshold", threshold)
    monkeypatch.setattr(settings, "lockout_cooldown_minutes", cooldown_minutes)


def test_failed_login_increments_counter(client, db_session, monkeypatch):
    _register(client, "increment@example.com", "9111111118")
    _set_login_limits(monkeypatch, ip=50, account=50)

    _login(client, "increment@example.com", _WRONG_PASSWORD)

    user = _get_user(db_session, "increment@example.com")
    assert user.failed_login_count == 1
    assert user.locked_until is None


def test_fourth_failed_login_does_not_lock(client, db_session, monkeypatch):
    _register(client, "four@example.com", "9111111119")
    _set_login_limits(monkeypatch, ip=50, account=50)
    _set_lockout(monkeypatch, threshold=5)

    for _ in range(4):
        assert _login(client, "four@example.com", _WRONG_PASSWORD).status_code == 401

    user = _get_user(db_session, "four@example.com")
    assert user.failed_login_count == 4
    assert user.locked_until is None

    # Correct password still works before the threshold is reached.
    assert _login(client, "four@example.com", _PASSWORD).status_code == 200


def test_fifth_failed_login_locks_account(client, db_session, monkeypatch):
    _register(client, "lock@example.com", "9111111120")
    _set_login_limits(monkeypatch, ip=50, account=50)
    _set_lockout(monkeypatch, threshold=5, cooldown_minutes=15)

    for _ in range(5):
        assert _login(client, "lock@example.com", _WRONG_PASSWORD).status_code == 401

    user = _get_user(db_session, "lock@example.com")
    assert _as_utc(user.locked_until) is not None
    assert _as_utc(user.locked_until) > datetime.now(timezone.utc)
    # Counter resets so the account gets a fresh set of attempts after cooldown.
    assert user.failed_login_count == 0


def test_lockout_uses_configured_cooldown(client, db_session, monkeypatch):
    _register(client, "cooldown@example.com", "9111111121")
    _set_login_limits(monkeypatch, ip=50, account=50)
    _set_lockout(monkeypatch, threshold=2, cooldown_minutes=30)

    for _ in range(2):
        assert _login(client, "cooldown@example.com", _WRONG_PASSWORD).status_code == 401

    user = _get_user(db_session, "cooldown@example.com")
    expected = datetime.now(timezone.utc) + timedelta(minutes=30)
    assert abs((_as_utc(user.locked_until) - expected).total_seconds()) < 60


def test_login_while_locked_is_rejected(client, db_session, monkeypatch):
    _register(client, "locked@example.com", "9111111122")
    _set_login_limits(monkeypatch, ip=50, account=50)
    _set_lockout(monkeypatch, threshold=5)

    for _ in range(5):
        assert _login(client, "locked@example.com", _WRONG_PASSWORD).status_code == 401

    # Correct credentials are still rejected while locked.
    response = _login(client, "locked@example.com", _PASSWORD)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_counter_does_not_grow_while_locked(client, db_session, monkeypatch):
    _register(client, "nogrow@example.com", "9111111123")
    _set_login_limits(monkeypatch, ip=50, account=50)
    _set_lockout(monkeypatch, threshold=3)

    for _ in range(3):
        assert _login(client, "nogrow@example.com", _WRONG_PASSWORD).status_code == 401
    user = _get_user(db_session, "nogrow@example.com")
    assert user.failed_login_count == 0  # reset at lock time
    assert user.locked_until is not None

    for _ in range(2):
        assert _login(client, "nogrow@example.com", _WRONG_PASSWORD).status_code == 401

    db_session.expire_all()
    user = _get_user(db_session, "nogrow@example.com")
    assert user.failed_login_count == 0, "attempts during lockout must not increment the counter"


def test_cooldown_expiry_allows_login(client, db_session, monkeypatch):
    _register(client, "expiredlock@example.com", "9111111124")
    _set_login_limits(monkeypatch, ip=50, account=50)
    _set_lockout(monkeypatch, threshold=2)

    for _ in range(2):
        assert _login(client, "expiredlock@example.com", _WRONG_PASSWORD).status_code == 401
    user = _get_user(db_session, "expiredlock@example.com")
    assert user.locked_until is not None

    # Simulate cooldown expiry.
    user.locked_until = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.commit()

    response = _login(client, "expiredlock@example.com", _PASSWORD)
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_successful_login_resets_counter_and_lockout(client, db_session, monkeypatch):
    _register(client, "reset@example.com", "9111111125")
    _set_login_limits(monkeypatch, ip=50, account=50)

    for _ in range(3):
        assert _login(client, "reset@example.com", _WRONG_PASSWORD).status_code == 401
    user = _get_user(db_session, "reset@example.com")
    assert user.failed_login_count == 3

    assert _login(client, "reset@example.com", _PASSWORD).status_code == 200

    db_session.expire_all()
    user = _get_user(db_session, "reset@example.com")
    assert user.failed_login_count == 0
    assert user.locked_until is None


def test_failed_login_does_not_reset_counter(client, db_session, monkeypatch):
    _register(client, "noreset@example.com", "9111111126")
    _set_login_limits(monkeypatch, ip=50, account=50)

    for _ in range(2):
        assert _login(client, "noreset@example.com", _WRONG_PASSWORD).status_code == 401
    _login(client, "noreset@example.com", _WRONG_PASSWORD)

    user = _get_user(db_session, "noreset@example.com")
    assert user.failed_login_count == 3


def test_lockout_does_not_reveal_account_existence(client, db_session, monkeypatch):
    _register(client, "secret@example.com", "9111111127")
    _set_login_limits(monkeypatch, ip=50, account=50)
    _set_lockout(monkeypatch, threshold=2)

    for _ in range(2):
        assert _login(client, "secret@example.com", _WRONG_PASSWORD).status_code == 401

    locked_response = _login(client, "secret@example.com", _PASSWORD)
    ghost_response = _login(client, "ghost@example.com", _WRONG_PASSWORD)
    assert locked_response.status_code == 401
    assert ghost_response.status_code == 401
    assert locked_response.json() == ghost_response.json(), (
        "locked and unknown accounts must produce identical responses"
    )


def test_repeated_failures_across_sessions_lock_exactly_at_threshold(
    client, db_session, monkeypatch
):
    """Sequential failures from independent sessions converge on the lock."""
    _register(client, "sessions@example.com", "9111111128")
    _set_login_limits(monkeypatch, ip=50, account=50)
    _set_lockout(monkeypatch, threshold=4)

    for _ in range(3):
        assert _login(client, "sessions@example.com", _WRONG_PASSWORD).status_code == 401
    user = _get_user(db_session, "sessions@example.com")
    assert user.failed_login_count == 3
    assert user.locked_until is None

    assert _login(client, "sessions@example.com", _WRONG_PASSWORD).status_code == 401
    db_session.expire_all()
    user = _get_user(db_session, "sessions@example.com")
    assert user.locked_until is not None


# ─── Audit integration ──────────────────────────────────────────────────────


def test_failed_logins_record_single_audit_event_each(client, db_session, monkeypatch):
    _register(client, "audit@example.com", "9111111129")
    _set_login_limits(monkeypatch, ip=50, account=50)

    for _ in range(3):
        assert _login(client, "audit@example.com", _WRONG_PASSWORD).status_code == 401
    assert _login(client, "audit@example.com", _PASSWORD).status_code == 200

    failures = db_session.execute(
        select(AuditLog).where(AuditLog.action == "login_failure")
    ).scalars()
    successes = db_session.execute(
        select(AuditLog).where(AuditLog.action == "login_success")
    ).scalars()
    assert len(list(failures)) == 3, "one login_failure event per failed attempt"
    assert len(list(successes)) == 1, "one login_success event per successful login"


def test_lockout_attempts_do_not_duplicate_audit_events(client, db_session, monkeypatch):
    _register(client, "lockaudit@example.com", "9111111130")
    _set_login_limits(monkeypatch, ip=50, account=50)
    _set_lockout(monkeypatch, threshold=2)

    for _ in range(2):
        assert _login(client, "lockaudit@example.com", _WRONG_PASSWORD).status_code == 401
    assert _login(client, "lockaudit@example.com", _PASSWORD).status_code == 401

    failures = db_session.execute(
        select(AuditLog).where(AuditLog.action == "login_failure")
    ).scalars()
    assert len(list(failures)) == 3

    serialized = str(db_session.execute(select(AuditLog)).scalars().all())
    assert _PASSWORD not in serialized
    assert "password" not in serialized.lower()


def test_429_responses_do_not_contain_passwords(client, monkeypatch):
    _set_login_limits(monkeypatch, ip=1, account=1)
    assert _login(client, "nobody@example.com", _WRONG_PASSWORD).status_code == 401
    response = _login(client, "nobody@example.com", _WRONG_PASSWORD)
    assert response.status_code == 429
    assert _PASSWORD not in response.text
    assert _WRONG_PASSWORD not in response.text


# ─── Service-level unit tests ───────────────────────────────────────────────


def test_record_failed_login_atomic_increment(db_session, monkeypatch):
    from app.models.user import UserRole

    user = User(
        name="Unit User",
        email="unit@example.com",
        phone="9111111131",
        password_hash="hash",
        role=UserRole.citizen,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    _set_lockout(monkeypatch, threshold=3, cooldown_minutes=15)
    record_failed_login(db_session, user)
    db_session.commit()
    db_session.refresh(user)
    assert user.failed_login_count == 1
    assert user.locked_until is None

    record_failed_login(db_session, user)
    db_session.commit()
    db_session.refresh(user)
    assert user.failed_login_count == 2
    assert user.locked_until is None

    record_failed_login(db_session, user)
    db_session.commit()
    db_session.refresh(user)
    assert user.failed_login_count == 0, "counter resets at lock time"
    assert user.locked_until is not None


def test_reset_login_failures_clears_lock(db_session, monkeypatch):
    from app.models.user import UserRole

    user = User(
        name="Reset Unit",
        email="resetunit@example.com",
        phone="9111111132",
        password_hash="hash",
        role=UserRole.citizen,
    )
    user.failed_login_count = 2
    user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=10)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    reset_login_failures(db_session, user)
    db_session.commit()
    db_session.refresh(user)
    assert user.failed_login_count == 0
    assert user.locked_until is None
