import ast
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import JSON, select

from app.models.audit_log import AuditLog
from app.repositories.audit import AuditLogRepository
from app.services.audit import sanitize_snapshot

MIGRATION_FILE = (
    Path(__file__).resolve().parent.parent
    / "alembic"
    / "versions"
    / "20260819_0015_audit_logging.py"
)

_REGISTER_PAYLOAD = {
    "name": "Audit User",
    "email": "audituser@example.com",
    "password": "Test@1234",
    "phone": "9876543210",
    "role": "citizen",
}


def _register(
    client, email="audituser@example.com", role="citizen", password="Test@1234", phone=None
):
    payload = dict(_REGISTER_PAYLOAD, email=email, role=role, password=password)
    if phone is not None:
        payload["phone"] = phone
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _audit_rows(db_session, action=None):
    statement = select(AuditLog).order_by(AuditLog.id.asc())
    if action is not None:
        statement = statement.where(AuditLog.action == action)
    return list(db_session.execute(statement).scalars().all())


def _list_audit(client, admin_headers, **params):
    return client.get("/admin/audit-logs", params=params, headers=admin_headers)


# ─── Model ───────────────────────────────────────────────────────────────────


def test_audit_log_model_fields_and_constraints():
    table = AuditLog.__table__
    columns = {column.name: column for column in table.columns}
    expected = {
        "id",
        "actor_user_id",
        "action",
        "resource",
        "resource_id",
        "before",
        "after",
        "ip_address",
        "user_agent",
        "created_at",
    }
    assert expected == set(columns)
    assert columns["actor_user_id"].nullable is True
    assert columns["actor_user_id"].foreign_keys, "actor_user_id must reference users.id"
    assert columns["action"].nullable is False
    assert columns["resource"].nullable is False
    assert isinstance(columns["before"].type, JSON)
    assert isinstance(columns["after"].type, JSON)
    assert columns["created_at"].nullable is False
    assert columns["created_at"].server_default is not None

    index_names = {index.name for index in table.indexes}
    for expected_index in (
        "ix_audit_logs_actor_user_id",
        "ix_audit_logs_action",
        "ix_audit_logs_resource",
        "ix_audit_logs_resource_id",
        "ix_audit_logs_created_at",
    ):
        assert expected_index in index_names


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
    assert assignments["revision"] == "20260819_0015"
    assert assignments["down_revision"] == "20260804_0014"
    text = MIGRATION_FILE.read_text(encoding="utf-8")
    assert text.count("op.create_index(") == 5
    assert 'op.drop_table("audit_logs")' in text


def test_repository_is_append_only():
    repository = AuditLogRepository()
    assert hasattr(repository, "create")
    assert hasattr(repository, "list")
    assert not hasattr(repository, "update"), "Audit log repository must not expose update"
    assert not hasattr(repository, "delete"), "Audit log repository must not expose delete"


def test_sanitize_snapshot_removes_sensitive_keys():
    snapshot = {
        "status": "approved",
        "password": "secret",
        "password_hash": "bcrypthash",
        "access_token": "jwt",
        "token": "x",
        "notes": "keep me",
    }
    sanitized = sanitize_snapshot(snapshot)
    assert sanitized == {"status": "approved", "notes": "keep me"}
    assert sanitized is not snapshot
    assert sanitize_snapshot(None) is None


# ─── Registration ────────────────────────────────────────────────────────────


def test_register_records_user_registered(client, db_session):
    _register(client)
    rows = _audit_rows(db_session, action="user_registered")
    assert len(rows) == 1
    record = rows[0]
    assert record.resource == "user"
    assert record.resource_id == str(record.actor_user_id)
    assert record.actor is not None
    assert record.after == {"role": "citizen"}
    assert record.created_at is not None


def test_duplicate_registration_rolls_back_audit(client, db_session):
    _register(client)
    second = client.post("/auth/register", json=dict(_REGISTER_PAYLOAD))
    assert second.status_code == 400
    rows = _audit_rows(db_session, action="user_registered")
    assert len(rows) == 1, "Failed registration must not leave an audit record"


# ─── Login ───────────────────────────────────────────────────────────────────


def test_login_success_records_audit(client, db_session):
    _register(client)
    response = client.post(
        "/auth/login", json={"email": "audituser@example.com", "password": "Test@1234"}
    )
    assert response.status_code == 200
    rows = _audit_rows(db_session, action="login_success")
    assert len(rows) == 1
    assert rows[0].actor_user_id is not None
    assert rows[0].resource == "user"
    assert rows[0].resource_id == str(rows[0].actor_user_id)


def test_login_failure_unknown_email_has_no_actor_or_email(client, db_session):
    response = client.post(
        "/auth/login", json={"email": "ghost@example.com", "password": "Test@1234"}
    )
    assert response.status_code == 401
    rows = _audit_rows(db_session, action="login_failure")
    assert len(rows) == 1
    record = rows[0]
    assert record.actor_user_id is None
    assert record.resource_id is None
    serialized = json.dumps(
        {
            "action": record.action,
            "resource": record.resource,
            "resource_id": record.resource_id,
            "before": record.before,
            "after": record.after,
            "ip_address": record.ip_address,
            "user_agent": record.user_agent,
        }
    )
    assert "ghost@example.com" not in serialized, "Failed logins must not leak the email"


def test_login_failure_known_email_sets_actor(client, db_session):
    _register(client)
    response = client.post(
        "/auth/login", json={"email": "audituser@example.com", "password": "WrongPassword"}
    )
    assert response.status_code == 401
    rows = _audit_rows(db_session, action="login_failure")
    assert len(rows) == 1
    assert rows[0].actor_user_id is not None
    assert rows[0].resource_id == str(rows[0].actor_user_id)


# ─── Password change ─────────────────────────────────────────────────────────


def test_password_change_records_audit_without_credentials(client, db_session):
    headers = _register(client)
    response = client.post(
        "/auth/change-password",
        json={"current_password": "Test@1234", "new_password": "NewPass@1234"},
        headers=headers,
    )
    assert response.status_code == 200
    rows = _audit_rows(db_session, action="password_changed")
    assert len(rows) == 1
    record = rows[0]
    assert record.actor_user_id is not None
    assert record.resource == "user"
    assert record.resource_id == str(record.actor_user_id)
    assert record.before is None
    assert record.after is None
    serialized = json.dumps({"before": record.before, "after": record.after})
    assert serialized == '{"before": null, "after": null}'


def test_password_change_failure_records_nothing(client, db_session):
    headers = _register(client)
    response = client.post(
        "/auth/change-password",
        json={"current_password": "WrongPassword", "new_password": "NewPass@1234"},
        headers=headers,
    )
    assert response.status_code == 400
    assert _audit_rows(db_session, action="password_changed") == []


# ─── Dealer approval ─────────────────────────────────────────────────────────


def test_dealer_approve_records_audit_snapshot(
    client, db_session, admin_headers, submitted_dealer_profile
):
    response = client.post(
        f"/admin/dealers/{submitted_dealer_profile.user_id}/approve", headers=admin_headers
    )
    assert response.status_code == 200
    rows = _audit_rows(db_session, action="dealer_approved")
    assert len(rows) == 1
    record = rows[0]
    assert record.resource == "dealer_profile"
    assert record.resource_id == str(submitted_dealer_profile.id)
    assert record.before == {"status": "submitted"}
    assert record.after == {"status": "approved"}


def test_dealer_reject_records_audit(db_session, client, admin_headers, submitted_dealer_profile):
    response = client.post(
        f"/admin/dealers/{submitted_dealer_profile.user_id}/reject",
        json={"reason": "Missing documents"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    rows = _audit_rows(db_session, action="dealer_rejected")
    assert len(rows) == 1
    record = rows[0]
    assert record.before == {"status": "submitted"}
    assert record.after == {"status": "rejected"}


def test_invalid_approval_transition_records_nothing(
    db_session, client, admin_headers, approved_dealer_profile
):
    response = client.post(
        f"/admin/dealers/{approved_dealer_profile.user_id}/approve", headers=admin_headers
    )
    assert response.status_code == 400
    assert _audit_rows(db_session, action="dealer_approved") == []


def test_reject_with_empty_reason_records_nothing(db_session, client, admin_headers, dealer_user):
    response = client.post(
        f"/admin/dealers/{dealer_user.id}/reject", json={}, headers=admin_headers
    )
    assert response.status_code == 422
    assert _audit_rows(db_session, action="dealer_rejected") == []


# ─── Inventory archive / restore ─────────────────────────────────────────────


def test_archive_records_audit(db_session, client, admin_headers, inventory_lot):
    response = client.post(
        f"/admin/inventory-lots/{inventory_lot.id}/archive",
        json={"archive_reason": "Quality issue found"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    rows = _audit_rows(db_session, action="inventory_lot_archived")
    assert len(rows) == 1
    record = rows[0]
    assert record.resource == "inventory_lot"
    assert record.resource_id == str(inventory_lot.id)
    assert record.before == {"visibility": "visible"}
    assert record.after == {"visibility": "hidden", "archive_reason": "Quality issue found"}


def test_restore_records_audit(db_session, client, admin_headers, inventory_lot):
    client.post(f"/admin/inventory-lots/{inventory_lot.id}/archive", json={}, headers=admin_headers)
    response = client.post(
        f"/admin/inventory-lots/{inventory_lot.id}/restore", headers=admin_headers
    )
    assert response.status_code == 200
    rows = _audit_rows(db_session, action="inventory_lot_restored")
    assert len(rows) == 1
    assert rows[0].before == {"visibility": "hidden"}
    assert rows[0].after == {"visibility": "visible"}


def test_repeated_archive_is_idempotent_for_audit(db_session, client, admin_headers, inventory_lot):
    first = client.post(
        f"/admin/inventory-lots/{inventory_lot.id}/archive", json={}, headers=admin_headers
    )
    assert first.status_code == 200
    second = client.post(
        f"/admin/inventory-lots/{inventory_lot.id}/archive", json={}, headers=admin_headers
    )
    assert second.status_code == 200
    assert len(_audit_rows(db_session, action="inventory_lot_archived")) == 1


# ─── Broadcast ───────────────────────────────────────────────────────────────


def test_broadcast_records_audit(db_session, client, admin_headers, citizen_user, dealer_user):
    response = client.post(
        "/admin/notifications/broadcast",
        json={
            "title": "Maintenance",
            "message": "Downtime tonight",
            "type": "system",
            "recipient_roles": ["citizen", "dealer"],
        },
        headers=admin_headers,
    )
    assert response.status_code == 200
    rows = _audit_rows(db_session, action="notification_broadcast")
    assert len(rows) == 1
    record = rows[0]
    assert record.resource == "notification"
    assert record.after == {
        "type": "system",
        "title": "Maintenance",
        "recipient_roles": ["citizen", "dealer"],
        "recipients_count": 2,
    }


def test_broadcast_invalid_role_records_nothing(db_session, client, admin_headers):
    response = client.post(
        "/admin/notifications/broadcast",
        json={
            "title": "Bad",
            "message": "Bad broadcast",
            "type": "system",
            "recipient_roles": ["hacker"],
        },
        headers=admin_headers,
    )
    assert response.status_code == 400
    assert _audit_rows(db_session, action="notification_broadcast") == []


# ─── Request metadata ────────────────────────────────────────────────────────


def test_audit_records_capture_ip_and_user_agent(db_session, client):
    _register(client)
    rows = _audit_rows(db_session, action="user_registered")
    assert len(rows) == 1
    assert rows[0].ip_address is not None
    assert rows[0].user_agent is not None


# ─── Admin API: authorization ────────────────────────────────────────────────


def test_audit_logs_require_authentication(client):
    response = client.get("/admin/audit-logs")
    assert response.status_code == 401


def test_audit_logs_admin_only(client, citizen_headers):
    response = client.get("/admin/audit-logs", headers=citizen_headers)
    assert response.status_code == 403


# ─── Admin API: listing ──────────────────────────────────────────────────────


def test_admin_lists_audit_logs(db_session, client, admin_headers):
    _register(client, email="alice@example.com", phone="9111111111")
    _register(client, email="bob@example.com", phone="9222222222")
    response = _list_audit(client, admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 1
    assert body["page_size"] == 50
    # Each registration emits user_registered + verification_email_sent.
    assert body["total_items"] == 4
    assert body["total_pages"] == 1
    actions = {item["action"] for item in body["items"]}
    assert actions == {"user_registered", "verification_email_sent"}
    assert all(item["actor_email"] is not None for item in body["items"])
    serialized = json.dumps(body)
    assert "password" not in serialized.lower()
    assert "password_hash" not in serialized.lower()


def test_audit_logs_empty(db_session, client, admin_headers):
    response = _list_audit(client, admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total_items"] == 0
    assert body["total_pages"] == 0


def test_audit_logs_pagination(db_session, client, admin_headers):
    for index in range(5):
        _register(client, email=f"user{index}@example.com", phone=f"98765432{index}")
    response = _list_audit(client, admin_headers, page=1, page_size=3)
    body = response.json()
    assert len(body["items"]) == 3
    # Each registration emits user_registered + verification_email_sent.
    assert body["total_items"] == 10
    assert body["total_pages"] == 4
    first_page_ids = {item["id"] for item in body["items"]}

    response = _list_audit(client, admin_headers, page=2, page_size=3)
    second_page_ids = {item["id"] for item in response.json()["items"]}
    assert not first_page_ids & second_page_ids

    response = _list_audit(client, admin_headers, page=4, page_size=3)
    assert len(response.json()["items"]) == 1


def test_audit_logs_page_size_bounds(client, admin_headers):
    assert _list_audit(client, admin_headers, page=0).status_code == 422
    assert _list_audit(client, admin_headers, page_size=0).status_code == 422
    assert _list_audit(client, admin_headers, page_size=101).status_code == 422


def test_audit_logs_ordering_newest_first(db_session, client, admin_headers):
    for index in range(3):
        _register(client, email=f"order{index}@example.com", phone=f"98765430{index}")
    response = _list_audit(client, admin_headers)
    items = response.json()["items"]
    assert [item["id"] for item in items] == sorted((item["id"] for item in items), reverse=True)


def test_audit_logs_filter_by_actor(db_session, client, admin_headers, make_user):
    _register(client, email="filter@example.com", phone="9111111111")
    make_user(role="citizen", email="other@example.com", phone="9111111112")
    registered_user_id = (
        db_session.execute(select(AuditLog).where(AuditLog.action == "user_registered"))
        .scalar_one()
        .actor_user_id
    )
    response = _list_audit(client, admin_headers, actor_user_id=registered_user_id)
    assert response.status_code == 200
    # Registration emits user_registered + verification_email_sent for the actor.
    assert response.json()["total_items"] == 2
    assert response.json()["items"][0]["actor_user_id"] == registered_user_id


def test_audit_logs_filter_by_action(db_session, client, admin_headers):
    _register(client)
    client.post("/auth/login", json={"email": "audituser@example.com", "password": "Test@1234"})
    response = _list_audit(client, admin_headers, action="login_success")
    assert response.status_code == 200
    body = response.json()
    assert body["total_items"] == 1
    assert body["items"][0]["action"] == "login_success"


def test_audit_logs_filter_by_resource(db_session, client, admin_headers):
    _register(client)
    response = _list_audit(client, admin_headers, resource="user")
    assert response.status_code == 200
    # Registration emits user_registered + verification_email_sent on "user".
    assert response.json()["total_items"] == 2
    response = _list_audit(client, admin_headers, resource="dealer_profile")
    assert response.json()["total_items"] == 0


def test_audit_logs_filter_by_created_after(db_session, client, admin_headers):
    _register(client)
    response = _list_audit(
        client,
        admin_headers,
        created_after=(datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
    )
    assert response.status_code == 200
    assert response.json()["total_items"] == 0
    response = _list_audit(
        client,
        admin_headers,
        created_after=(datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
    )
    # user_registered + verification_email_sent fall inside the window.
    assert response.json()["total_items"] == 2


def test_audit_logs_filter_by_created_before(db_session, client, admin_headers):
    _register(client)
    response = _list_audit(
        client,
        admin_headers,
        created_before=(datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
    )
    assert response.status_code == 200
    assert response.json()["total_items"] == 0
    response = _list_audit(
        client,
        admin_headers,
        created_before=(datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
    )
    # user_registered + verification_email_sent fall inside the window.
    assert response.json()["total_items"] == 2


# ─── Admin API: append-only enforcement ──────────────────────────────────────


def test_audit_logs_have_no_write_endpoints(client, admin_headers):
    assert client.post("/admin/audit-logs", headers=admin_headers).status_code == 405
    assert client.put("/admin/audit-logs", headers=admin_headers).status_code == 405
    assert client.patch("/admin/audit-logs", headers=admin_headers).status_code == 405
    assert client.delete("/admin/audit-logs", headers=admin_headers).status_code == 405
    assert client.put("/admin/audit-logs/1", headers=admin_headers).status_code == 404
    assert client.delete("/admin/audit-logs/1", headers=admin_headers).status_code == 404
