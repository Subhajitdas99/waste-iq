"""Unit and API tests for login history (WIQ-V1-019).

Repository/schema tests exercise ``AuditLogRepository.list_login_events`` and
the login-history response schemas directly. API tests cover
``GET /auth/login-history`` and ``GET /admin/login-history`` through the
TestClient.

Page-size bounds (1..100) are enforced at the API layer via FastAPI `Query`
constraints, mirroring `/admin/audit-logs`; the repository accepts any
positive page size it is given.

Note: login is rate limited (max 10/IP and max 5/account per 60s window) and
the conftest resets the limiter per test, so each test keeps its request
counts below those thresholds.
"""

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.repositories.audit import AuditLogRepository
from app.schemas.audit import AdminLoginHistoryEntryRead, LoginHistoryEntryRead

_repository = AuditLogRepository()

_REGISTER_PAYLOAD = {
    "name": "Login History User",
    "email": "loginhistory@example.com",
    "password": "Test@1234",
    "phone": "9876543210",
    "role": "citizen",
}


def _register(client, email="loginhistory@example.com", role="citizen", phone=None):
    payload = dict(_REGISTER_PAYLOAD, email=email, role=role)
    if phone is not None:
        payload["phone"] = phone
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _login(client, email="loginhistory@example.com", password="Test@1234"):
    return client.post("/auth/login", json={"email": email, "password": password})


def _create_login_event(
    db_session,
    *,
    actor_user_id: int | None = None,
    action: str = "login_success",
    minutes_ago: int = 0,
    ip_address: str = "203.0.113.9",
):
    record = _repository.create(
        db_session,
        actor_user_id=actor_user_id,
        action=action,
        resource="user",
        resource_id=str(actor_user_id) if actor_user_id is not None else None,
        ip_address=ip_address,
        user_agent="Mozilla/5.0 (Login History Test)",
    )
    # created_at has a server default with second-level resolution; set it
    # explicitly so ordering assertions are deterministic.
    record.created_at = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    db_session.commit()
    db_session.refresh(record)
    return record


def _list(db_session, **params):
    return _repository.list_login_events(db_session, **params)


# ─── Action scope ────────────────────────────────────────────────────────────


def test_login_success_and_failure_are_included(db_session, citizen_user):
    success = _create_login_event(
        db_session, actor_user_id=citizen_user.id, action="login_success", minutes_ago=10
    )
    failure = _create_login_event(
        db_session, actor_user_id=citizen_user.id, action="login_failure", minutes_ago=5
    )

    items, total_items, total_pages = _list(db_session)

    assert [item.id for item in items] == [failure.id, success.id]
    assert total_items == 2
    assert total_pages == 1


def test_non_login_actions_are_excluded(db_session, citizen_user):
    _create_login_event(db_session, actor_user_id=citizen_user.id, action="password_changed")
    _create_login_event(db_session, actor_user_id=citizen_user.id, action="user_registered")
    login = _create_login_event(db_session, actor_user_id=citizen_user.id, action="login_success")

    items, total_items, total_pages = _list(db_session)

    assert [item.id for item in items] == [login.id]
    assert total_items == 1
    assert total_pages == 1


# ─── Outcome filter ──────────────────────────────────────────────────────────


def test_outcome_success_filter(db_session, citizen_user):
    success = _create_login_event(
        db_session, actor_user_id=citizen_user.id, action="login_success"
    )
    _create_login_event(db_session, actor_user_id=citizen_user.id, action="login_failure")

    items, total_items, _ = _list(db_session, outcome="success")

    assert [item.id for item in items] == [success.id]
    assert total_items == 1


def test_outcome_failure_filter(db_session, citizen_user):
    _create_login_event(db_session, actor_user_id=citizen_user.id, action="login_success")
    failure = _create_login_event(
        db_session, actor_user_id=citizen_user.id, action="login_failure"
    )

    items, total_items, _ = _list(db_session, outcome="failure")

    assert [item.id for item in items] == [failure.id]
    assert total_items == 1


def test_unknown_outcome_raises_value_error(db_session):
    with pytest.raises(ValueError):
        _list(db_session, outcome="bogus")


# ─── Actor filter ────────────────────────────────────────────────────────────


def test_actor_user_id_filters_to_that_user_only(db_session, citizen_user, admin_user):
    mine = _create_login_event(db_session, actor_user_id=citizen_user.id)
    _create_login_event(db_session, actor_user_id=admin_user.id)

    items, total_items, _ = _list(db_session, actor_user_id=citizen_user.id)

    assert [item.id for item in items] == [mine.id]
    assert total_items == 1


def test_unattributed_failures_are_excluded_when_filtering_by_actor(
    db_session, citizen_user
):
    """Unknown-email failures have no actor and must not appear in a user's history."""
    _create_login_event(db_session, actor_user_id=None, action="login_failure")
    mine = _create_login_event(db_session, actor_user_id=citizen_user.id)

    items, total_items, _ = _list(db_session, actor_user_id=citizen_user.id)

    assert [item.id for item in items] == [mine.id]
    assert total_items == 1


def test_created_after_and_created_before_filters(db_session, citizen_user):
    old = _create_login_event(
        db_session, actor_user_id=citizen_user.id, minutes_ago=120
    )
    recent = _create_login_event(db_session, actor_user_id=citizen_user.id, minutes_ago=1)

    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
    items, total_items, _ = _list(db_session, created_after=cutoff)
    assert [item.id for item in items] == [recent.id]

    items, total_items, _ = _list(db_session, created_before=cutoff)
    assert [item.id for item in items] == [old.id]


# ─── Ordering & pagination ───────────────────────────────────────────────────


def test_newest_records_come_first(db_session, citizen_user):
    older = _create_login_event(
        db_session, actor_user_id=citizen_user.id, minutes_ago=30
    )
    newer = _create_login_event(db_session, actor_user_id=citizen_user.id, minutes_ago=1)

    items, _, _ = _list(db_session)

    assert [item.id for item in items] == [newer.id, older.id]


def test_pagination_shape_and_slices(db_session, citizen_user):
    # Later insertions are more recent, so newest-first equals reversed
    # insertion order.
    records = [
        _create_login_event(db_session, actor_user_id=citizen_user.id, minutes_ago=5 - index)
        for index in range(5)
    ]

    first_page, total_items, total_pages = _list(db_session, page=1, page_size=2)
    second_page, _, _ = _list(db_session, page=2, page_size=2)
    third_page, _, _ = _list(db_session, page=3, page_size=2)

    assert total_items == 5
    assert total_pages == 3
    assert len(first_page) == len(second_page) == 2
    assert len(third_page) == 1

    all_ids = [item.id for item in (*first_page, *second_page, *third_page)]
    assert len(set(all_ids)) == 5, "pages must not overlap"
    assert all_ids == [record.id for record in reversed(records)]


def test_empty_history_returns_zero_totals(db_session):
    items, total_items, total_pages = _list(db_session)

    assert items == []
    assert total_items == 0
    assert total_pages == 0


# ─── Schemas ─────────────────────────────────────────────────────────────────


def test_entry_schema_validates_from_orm_row_and_hides_internal_fields(
    db_session, citizen_user
):
    record = _create_login_event(db_session, actor_user_id=citizen_user.id)

    entry = LoginHistoryEntryRead.model_validate(record)

    assert entry.outcome == "success"
    assert entry.ip_address == "203.0.113.9"
    assert entry.user_agent == "Mozilla/5.0 (Login History Test)"
    assert entry.created_at is not None
    assert set(entry.model_dump()) == {"id", "outcome", "ip_address", "user_agent", "created_at"}


def test_entry_schema_accepts_outcome_kwarg_directly():
    entry = LoginHistoryEntryRead(
        id=1,
        outcome="failure",
        ip_address=None,
        user_agent=None,
        created_at=datetime.now(timezone.utc),
    )
    assert entry.outcome == "failure"


def test_entry_schema_rejects_non_login_actions(db_session, citizen_user):
    record = _create_login_event(
        db_session, actor_user_id=citizen_user.id, action="password_changed"
    )

    with pytest.raises(ValidationError):
        LoginHistoryEntryRead.model_validate(record)


def test_admin_entry_resolves_actor_fields(db_session, admin_user, citizen_user):
    record = _create_login_event(
        db_session, actor_user_id=citizen_user.id, action="login_failure"
    )

    entry = AdminLoginHistoryEntryRead.model_validate(record)

    assert entry.actor_user_id == citizen_user.id
    assert entry.actor_email == citizen_user.email
    assert entry.outcome == "failure"


def test_admin_entry_handles_unattributed_failure(db_session):
    record = _create_login_event(db_session, actor_user_id=None, action="login_failure")

    entry = AdminLoginHistoryEntryRead.model_validate(record)

    assert entry.actor_user_id is None
    assert entry.actor_email is None
    assert entry.outcome == "failure"


# ─── API: GET /auth/login-history ────────────────────────────────────────────


def test_auth_login_history_requires_authentication(client):
    response = client.get("/auth/login-history")
    assert response.status_code == 401


def test_auth_login_history_shows_own_success_and_failure(client):
    headers = _register(client)
    assert _login(client).status_code == 200  # success
    assert _login(client, password="WrongPassword").status_code == 401  # failure

    response = client.get("/auth/login-history", headers=headers)
    assert response.status_code == 200

    body = response.json()
    assert body["total_items"] == 2
    # Newest first: the failed attempt is the most recent event.
    assert [item["outcome"] for item in body["items"]] == ["failure", "success"]
    for item in body["items"]:
        assert set(item) == {"id", "outcome", "ip_address", "user_agent", "created_at"}


def test_auth_login_history_excludes_non_login_actions(client):
    headers = _register(client)
    assert _login(client).status_code == 200
    changed = client.post(
        "/auth/change-password",
        json={"current_password": "Test@1234", "new_password": "NewPass@1234"},
        headers=headers,
    )
    assert changed.status_code == 200

    body = client.get("/auth/login-history", headers=headers).json()

    assert body["total_items"] == 1
    assert body["items"][0]["outcome"] == "success"


def test_auth_login_history_cannot_read_other_users_history(client):
    headers_a = _register(client, email="usera@example.com", phone="9111111111")
    _register(client, email="userb@example.com", phone="9222222222")
    assert _login(client, "usera@example.com").status_code == 200
    assert _login(client, "userb@example.com").status_code == 200

    own = client.get("/auth/login-history", headers=headers_a).json()
    assert own["total_items"] == 1

    # There is no identity override; extra query parameters are ignored.
    override = client.get(
        "/auth/login-history",
        params={"actor_user_id": 999999, "user_id": 999999},
        headers=headers_a,
    ).json()
    assert override == own


def test_auth_login_history_unknown_email_failure_is_not_attributed(client):
    headers = _register(client)
    before = client.get("/auth/login-history", headers=headers).json()
    assert before["total_items"] == 0

    assert _login(client, "ghost@example.com").status_code == 401

    after = client.get("/auth/login-history", headers=headers).json()
    message = "unattributable failures must not appear in any user's history"
    assert after["total_items"] == 0, message


def test_auth_login_history_outcome_filter(client):
    headers = _register(client)
    assert _login(client).status_code == 200
    assert _login(client, password="WrongPassword").status_code == 401

    successes = client.get(
        "/auth/login-history", params={"outcome": "success"}, headers=headers
    ).json()
    failures = client.get(
        "/auth/login-history", params={"outcome": "failure"}, headers=headers
    ).json()

    assert successes["total_items"] == 1
    assert successes["items"][0]["outcome"] == "success"
    assert failures["total_items"] == 1
    assert failures["items"][0]["outcome"] == "failure"
    assert client.get(
        "/auth/login-history", params={"outcome": "bogus"}, headers=headers
    ).status_code == 422


def test_auth_login_history_pagination_and_bounds(client):
    headers = _register(client)
    for _ in range(3):  # stays below the per-account login rate limit
        assert _login(client).status_code == 200

    first = client.get(
        "/auth/login-history", params={"page": 1, "page_size": 2}, headers=headers
    ).json()
    second = client.get(
        "/auth/login-history", params={"page": 2, "page_size": 2}, headers=headers
    ).json()

    assert first["total_items"] == 3
    assert first["total_pages"] == 2
    assert len(first["items"]) == 2
    assert len(second["items"]) == 1
    page_one_ids = {item["id"] for item in first["items"]}
    page_two_ids = {item["id"] for item in second["items"]}
    assert not page_one_ids & page_two_ids

    assert (
        client.get("/auth/login-history", params={"page": 0}, headers=headers).status_code == 422
    )
    assert (
        client.get("/auth/login-history", params={"page_size": 0}, headers=headers).status_code
        == 422
    )
    assert (
        client.get("/auth/login-history", params={"page_size": 101}, headers=headers).status_code
        == 422
    )


# ─── API: GET /admin/login-history ───────────────────────────────────────────


def test_admin_login_history_requires_authentication(client):
    assert client.get("/admin/login-history").status_code == 401


def test_admin_login_history_rejects_non_admin(client, citizen_headers):
    assert client.get("/admin/login-history", headers=citizen_headers).status_code == 403


def test_admin_login_history_lists_multiple_users(client, admin_headers):
    _register(client, email="multi-a@example.com", phone="9111111111")
    _register(client, email="multi-b@example.com", phone="9222222222")
    assert _login(client, "multi-a@example.com").status_code == 200
    assert _login(client, "multi-b@example.com").status_code == 200

    body = client.get("/admin/login-history", headers=admin_headers).json()

    assert body["total_items"] == 2
    actor_ids = {item["actor_user_id"] for item in body["items"]}
    assert len(actor_ids) == 2
    for item in body["items"]:
        assert set(item) == {
            "id",
            "outcome",
            "ip_address",
            "user_agent",
            "created_at",
            "actor_user_id",
            "actor_email",
        }
        assert item["actor_email"] is not None


def test_admin_login_history_actor_user_id_filter(client, admin_headers):
    _register(client, email="filter-a@example.com", phone="9111111111")
    dealer_headers = _register(
        client, email="filter-b@example.com", role="dealer", phone="9222222222"
    )
    assert _login(client, "filter-a@example.com").status_code == 200
    assert _login(client, "filter-b@example.com").status_code == 200

    target_id = client.get("/auth/me", headers=dealer_headers).json()["id"]
    body = client.get(
        "/admin/login-history", params={"actor_user_id": target_id}, headers=admin_headers
    ).json()

    assert body["total_items"] == 1
    assert body["items"][0]["actor_user_id"] == target_id


def test_admin_login_history_outcome_filter(client, admin_headers):
    _register(client)
    assert _login(client).status_code == 200
    assert _login(client, password="WrongPassword").status_code == 401

    successes = client.get(
        "/admin/login-history", params={"outcome": "success"}, headers=admin_headers
    ).json()
    failures = client.get(
        "/admin/login-history", params={"outcome": "failure"}, headers=admin_headers
    ).json()

    assert successes["total_items"] == 1
    assert failures["total_items"] == 1
    assert successes["items"][0]["outcome"] == "success"
    assert failures["items"][0]["outcome"] == "failure"


def test_admin_login_history_created_window_filters(client, db_session, admin_headers):
    old = _create_login_event(
        db_session, actor_user_id=None, action="login_failure", minutes_ago=120
    )
    recent = _create_login_event(
        db_session, actor_user_id=None, action="login_failure", minutes_ago=1
    )

    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)

    after = client.get(
        "/admin/login-history", params={"created_after": cutoff.isoformat()}, headers=admin_headers
    ).json()
    assert [item["id"] for item in after["items"]] == [recent.id]

    before = client.get(
        "/admin/login-history",
        params={"created_before": cutoff.isoformat()},
        headers=admin_headers,
    ).json()
    assert [item["id"] for item in before["items"]] == [old.id]


def test_admin_login_history_pagination_and_ordering(client, admin_headers):
    _register(client)
    for _ in range(3):  # stays below the per-account login rate limit
        assert _login(client).status_code == 200

    first = client.get(
        "/admin/login-history", params={"page": 1, "page_size": 2}, headers=admin_headers
    ).json()
    second = client.get(
        "/admin/login-history", params={"page": 2, "page_size": 2}, headers=admin_headers
    ).json()

    assert first["total_items"] == 3
    assert first["total_pages"] == 2
    all_ids = [item["id"] for item in (*first["items"], *second["items"])]
    assert len(set(all_ids)) == 3
    assert all_ids == sorted(all_ids, reverse=True), "must be newest (highest id tiebreak) first"


def test_admin_login_history_unattributed_failures_have_null_actor(client, admin_headers):
    assert _login(client, "nobody@example.com").status_code == 401

    body = client.get("/admin/login-history", headers=admin_headers).json()

    assert body["total_items"] == 1
    item = body["items"][0]
    assert item["outcome"] == "failure"
    assert item["actor_user_id"] is None
    assert item["actor_email"] is None


def test_admin_login_history_excludes_non_login_events(client, db_session, admin_headers):
    """Registration/verification audits exist but must never surface as login history."""
    _register(client)
    _repository.create(
        db_session,
        actor_user_id=None,
        action="password_changed",
        resource="user",
    )
    db_session.commit()

    body = client.get("/admin/login-history", headers=admin_headers).json()

    assert body["total_items"] == 0
