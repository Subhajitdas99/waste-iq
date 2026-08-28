"""Tests for WIQ-V1-046 Citizen Weight Verification & Dispute Workflow.

Validates the complete weight verification lifecycle, including:
- Citizen confirmation of collector-recorded weight
- Citizen dispute with mandatory reason
- Admin review and resolution (uphold / corrected)
- Idempotency, authorization, audit trail, and notifications.
"""

from app.models.pickup_request import PickupStatus


def _build_weight_recorded(client, citizen_headers, collector_headers, valid_pickup_payload):
    """Helper: full lifecycle to weight_recorded, returns request dict."""
    req = client.post("/pickup-requests", data=valid_pickup_payload, headers=citizen_headers).json()
    client.post(f"/collector/pickups/{req['id']}/accept", headers=collector_headers)
    client.post(f"/collector/pickups/{req['id']}/start", headers=collector_headers)
    client.post(f"/collector/pickups/{req['id']}/collect", headers=collector_headers)
    resp = client.post(
        f"/collector/pickups/{req['id']}/record-weight",
        json={"weight_kg": 8.5},
        headers=collector_headers,
    )
    return resp.json()


# ─── Weight recording (setup) ──────────────────────────────────────────────────


def test_record_weight_transitions_to_weight_recorded_state(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    request = _build_weight_recorded(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )
    assert request["status"] == "weight_recorded"
    assert request["assignment"]["weight_kg"] == 8.5


def test_record_weight_creates_weight_recorded_audit_event(
    client,
    citizen_headers,
    collector_headers,
    admin_user,
    valid_pickup_payload,
):
    request = _build_weight_recorded(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )

    from app.core.security import create_access_token

    token = create_access_token(str(admin_user.id))
    resp = client.get(
        "/admin/audit-logs",
        params={"resource_id": str(request["id"]), "page": 1, "page_size": 50},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    actions = {item["action"] for item in resp.json()["items"]}
    assert "pickup_weight_recorded" in actions


# ─── Citizen weight confirmation ────────────────────────────────────────────────


def test_citizen_can_confirm_recorded_weight(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    request = _build_weight_recorded(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )
    resp = client.post(
        f"/pickup-requests/{request['id']}/weight/confirm",
        headers=citizen_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"
    assert resp.json()["assignment"]["weight_kg"] == 8.5


def test_citizen_confirm_creates_completed_event(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    request = _build_weight_recorded(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )
    client.post(f"/pickup-requests/{request['id']}/weight/confirm", headers=citizen_headers)
    detail = client.get(f"/pickup-requests/{request['id']}", headers=citizen_headers).json()
    statuses = [e["status"] for e in detail["timeline"]]
    assert "weight_recorded" in statuses
    assert "completed" in statuses


def test_citizen_confirm_idempotent(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    request = _build_weight_recorded(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )
    first = client.post(f"/pickup-requests/{request['id']}/weight/confirm", headers=citizen_headers)
    second = client.post(
        f"/pickup-requests/{request['id']}/weight/confirm", headers=citizen_headers
    )
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == "completed"
    assert second.json()["status"] == "completed"


def test_citizen_cannot_confirm_before_weight_recorded(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    req = client.post("/pickup-requests", data=valid_pickup_payload, headers=citizen_headers).json()
    client.post(f"/collector/pickups/{req['id']}/accept", headers=collector_headers)
    resp = client.post(f"/pickup-requests/{req['id']}/weight/confirm", headers=citizen_headers)
    assert resp.status_code == 400
    assert "weight" in resp.json()["detail"].lower()


def test_citizen_cannot_confirm_completed_pickup(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    request = _build_weight_recorded(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )
    client.post(f"/pickup-requests/{request['id']}/weight/confirm", headers=citizen_headers)
    resp = client.post(f"/pickup-requests/{request['id']}/weight/confirm", headers=citizen_headers)
    assert resp.status_code == 200


def test_non_owner_cannot_confirm(
    client, citizen_headers, collector_headers, valid_pickup_payload, make_user, auth_headers
):
    request = _build_weight_recorded(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )
    other = make_user(role="citizen", email="other_c@wasteiq.test", phone="9100099001")
    resp = client.post(
        f"/pickup-requests/{request['id']}/weight/confirm",
        headers=auth_headers(other),
    )
    assert resp.status_code == 403


# ─── Citizen weight dispute ────────────────────────────────────────────────────


def test_citizen_can_dispute_recorded_weight(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    request = _build_weight_recorded(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )
    resp = client.post(
        f"/pickup-requests/{request['id']}/weight/dispute",
        json={"reason": "The weight is much higher than expected."},
        headers=citizen_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "disputed"


def test_citizen_dispute_creates_dispute_record(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    request = _build_weight_recorded(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )
    client.post(
        f"/pickup-requests/{request['id']}/weight/dispute",
        json={"reason": "The weight seems incorrect."},
        headers=citizen_headers,
    )
    detail = client.get(f"/pickup-requests/{request['id']}", headers=citizen_headers).json()
    assert detail["dispute"] is not None
    assert detail["dispute"]["reason"] == "The weight seems incorrect."
    assert detail["dispute"]["resolution"] is None


def test_citizen_dispute_idempotent_same_reason(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    request = _build_weight_recorded(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )
    reason = "The weight is too high."
    first = client.post(
        f"/pickup-requests/{request['id']}/weight/dispute",
        json={"reason": reason},
        headers=citizen_headers,
    )
    second = client.post(
        f"/pickup-requests/{request['id']}/weight/dispute",
        json={"reason": reason},
        headers=citizen_headers,
    )
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == second.json()["status"] == "disputed"


def test_citizen_dispute_different_reason_returns_409(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    request = _build_weight_recorded(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )
    client.post(
        f"/pickup-requests/{request['id']}/weight/dispute",
        json={"reason": "First reason."},
        headers=citizen_headers,
    )
    resp = client.post(
        f"/pickup-requests/{request['id']}/weight/dispute",
        json={"reason": "Different reason."},
        headers=citizen_headers,
    )
    assert resp.status_code == 409


def test_citizen_cannot_dispute_before_weight_recorded(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    req = client.post("/pickup-requests", data=valid_pickup_payload, headers=citizen_headers).json()
    client.post(f"/collector/pickups/{req['id']}/accept", headers=collector_headers)
    resp = client.post(
        f"/pickup-requests/{req['id']}/weight/dispute",
        json={"reason": "Some reason."},
        headers=citizen_headers,
    )
    assert resp.status_code == 400


def test_citizen_cannot_dispute_completed_pickup(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    request = _build_weight_recorded(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )
    client.post(f"/pickup-requests/{request['id']}/weight/confirm", headers=citizen_headers)
    resp = client.post(
        f"/pickup-requests/{request['id']}/weight/dispute",
        json={"reason": "Too late to dispute."},
        headers=citizen_headers,
    )
    assert resp.status_code == 400


def test_citizen_dispute_requires_reason(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    request = _build_weight_recorded(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )
    resp = client.post(
        f"/pickup-requests/{request['id']}/weight/dispute",
        json={"reason": ""},
        headers=citizen_headers,
    )
    assert resp.status_code == 422


def test_citizen_dispute_reason_too_short(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    request = _build_weight_recorded(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )
    resp = client.post(
        f"/pickup-requests/{request['id']}/weight/dispute",
        json={"reason": "No"},
        headers=citizen_headers,
    )
    assert resp.status_code == 422


def test_non_owner_cannot_dispute(
    client, citizen_headers, collector_headers, valid_pickup_payload, make_user, auth_headers
):
    request = _build_weight_recorded(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )
    other = make_user(role="citizen", email="other_d@wasteiq.test", phone="9100099002")
    resp = client.post(
        f"/pickup-requests/{request['id']}/weight/dispute",
        json={"reason": "Unauthorized dispute attempt."},
        headers=auth_headers(other),
    )
    assert resp.status_code == 403


def test_dispute_creates_audit_event(
    client, citizen_headers, collector_headers, admin_user, valid_pickup_payload
):
    request = _build_weight_recorded(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )
    client.post(
        f"/pickup-requests/{request['id']}/weight/dispute",
        json={"reason": "Audit test dispute."},
        headers=citizen_headers,
    )
    from app.core.security import create_access_token

    token = create_access_token(str(admin_user.id))
    resp = client.get(
        "/admin/audit-logs",
        params={"resource_id": str(request["id"]), "page": 1, "page_size": 50},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    actions = {item["action"] for item in resp.json()["items"]}
    assert "pickup_weight_disputed" in actions


# ─── Admin dispute resolution ──────────────────────────────────────────────────


def test_admin_can_list_disputed_pickups(
    client, citizen_headers, collector_headers, admin_headers, valid_pickup_payload
):
    request = _build_weight_recorded(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )
    client.post(
        f"/pickup-requests/{request['id']}/weight/dispute",
        json={"reason": "Admin list test."},
        headers=citizen_headers,
    )
    resp = client.get("/admin/disputes/pickups", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"]
    ids = [item["id"] for item in body["items"]]
    assert request["id"] in ids


def test_admin_resolve_uphold(
    client, citizen_headers, collector_headers, admin_headers, valid_pickup_payload
):
    request = _build_weight_recorded(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )
    client.post(
        f"/pickup-requests/{request['id']}/weight/dispute",
        json={"reason": "Uphold test."},
        headers=citizen_headers,
    )
    resp = client.post(
        f"/admin/disputes/pickups/{request['id']}/resolve",
        json={"resolution": "upheld"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


def test_admin_resolve_corrected_requires_weight(
    client, citizen_headers, collector_headers, admin_headers, valid_pickup_payload
):
    request = _build_weight_recorded(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )
    client.post(
        f"/pickup-requests/{request['id']}/weight/dispute",
        json={"reason": "Corrected without weight."},
        headers=citizen_headers,
    )
    resp = client.post(
        f"/admin/disputes/pickups/{request['id']}/resolve",
        json={"resolution": "corrected"},
        headers=admin_headers,
    )
    assert resp.status_code == 400


def test_admin_resolve_corrected_with_weight(
    client, citizen_headers, collector_headers, admin_headers, valid_pickup_payload
):
    request = _build_weight_recorded(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )
    client.post(
        f"/pickup-requests/{request['id']}/weight/dispute",
        json={"reason": "Corrected with weight."},
        headers=citizen_headers,
    )
    resp = client.post(
        f"/admin/disputes/pickups/{request['id']}/resolve",
        json={"resolution": "corrected", "resolved_weight_kg": 10.0, "notes": "Adjusted."},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


def test_admin_resolve_idempotent(
    client, citizen_headers, collector_headers, admin_headers, valid_pickup_payload
):
    request = _build_weight_recorded(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )
    client.post(
        f"/pickup-requests/{request['id']}/weight/dispute",
        json={"reason": "Idempotent resolve."},
        headers=citizen_headers,
    )
    first = client.post(
        f"/admin/disputes/pickups/{request['id']}/resolve",
        json={"resolution": "upheld"},
        headers=admin_headers,
    )
    assert first.status_code == 200
    # Once resolved the pickup is no longer in disputed state; further
    # resolution attempts are rejected to keep the lifecycle explicit.
    second = client.post(
        f"/admin/disputes/pickups/{request['id']}/resolve",
        json={"resolution": "upheld"},
        headers=admin_headers,
    )
    assert second.status_code == 400


def test_admin_resolve_creates_audit_events(
    client, citizen_headers, collector_headers, admin_headers, admin_user, valid_pickup_payload
):
    request = _build_weight_recorded(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )
    client.post(
        f"/pickup-requests/{request['id']}/weight/dispute",
        json={"reason": "Audit resolve test."},
        headers=citizen_headers,
    )
    client.post(
        f"/admin/disputes/pickups/{request['id']}/resolve",
        json={"resolution": "upheld"},
        headers=admin_headers,
    )
    from app.core.security import create_access_token

    token = create_access_token(str(admin_user.id))
    resp = client.get(
        "/admin/audit-logs",
        params={"resource_id": str(request["id"]), "page": 1, "page_size": 50},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    actions = {item["action"] for item in resp.json()["items"]}
    assert "pickup_dispute_resolved" in actions


def test_non_admin_cannot_resolve(client, citizen_headers, collector_headers, valid_pickup_payload):
    request = _build_weight_recorded(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )
    client.post(
        f"/pickup-requests/{request['id']}/weight/dispute",
        json={"reason": "Unauthorized resolve."},
        headers=citizen_headers,
    )
    resp = client.post(
        f"/admin/disputes/pickups/{request['id']}/resolve",
        json={"resolution": "upheld"},
        headers=collector_headers,
    )
    assert resp.status_code == 403


def test_admin_cannot_resolve_non_disputed(
    client, citizen_headers, collector_headers, admin_headers, valid_pickup_payload
):
    request = _build_weight_recorded(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )
    resp = client.post(
        f"/admin/disputes/pickups/{request['id']}/resolve",
        json={"resolution": "upheld"},
        headers=admin_headers,
    )
    assert resp.status_code == 400


# ─── Original weight immutability ─────────────────────────────────────────────


def test_original_collector_weight_preserved_after_dispute(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    request = _build_weight_recorded(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )
    client.post(
        f"/pickup-requests/{request['id']}/weight/dispute",
        json={"reason": "Weight preserved test."},
        headers=citizen_headers,
    )
    detail = client.get(f"/pickup-requests/{request['id']}", headers=citizen_headers).json()
    assert detail["assignment"]["weight_kg"] == 8.5


def test_original_collector_weight_preserved_after_admin_uphold(
    client, citizen_headers, collector_headers, admin_headers, valid_pickup_payload
):
    request = _build_weight_recorded(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )
    client.post(
        f"/pickup-requests/{request['id']}/weight/dispute",
        json={"reason": "Uphold immutability."},
        headers=citizen_headers,
    )
    client.post(
        f"/admin/disputes/pickups/{request['id']}/resolve",
        json={"resolution": "upheld"},
        headers=admin_headers,
    )
    detail = client.get(f"/pickup-requests/{request['id']}", headers=citizen_headers).json()
    assert detail["assignment"]["weight_kg"] == 8.5


# ─── Collector bypass prevention ───────────────────────────────────────────────


def test_collector_cannot_complete_weight_recorded(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    request = _build_weight_recorded(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )
    resp = client.post(
        f"/collector/pickups/{request['id']}/complete",
        json={"weight_kg": 8.5},
        headers=collector_headers,
    )
    assert resp.status_code == 400


def test_collector_cannot_complete_disputed(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    request = _build_weight_recorded(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )
    client.post(
        f"/pickup-requests/{request['id']}/weight/dispute",
        json={"reason": "Cannot bypass dispute."},
        headers=citizen_headers,
    )
    resp = client.post(
        f"/collector/pickups/{request['id']}/complete",
        json={"weight_kg": 8.5},
        headers=collector_headers,
    )
    assert resp.status_code == 400


# ─── Audit PII / sensitive data ────────────────────────────────────────────────


def test_audit_does_not_contain_phone_in_dispute_events(
    client, db_session, citizen_headers, collector_headers, valid_pickup_payload
):
    request = _build_weight_recorded(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )
    client.post(
        f"/pickup-requests/{request['id']}/weight/dispute",
        json={"reason": "PII audit test."},
        headers=citizen_headers,
    )
    from app.services.audit import AuditService

    audit = AuditService()
    events, _, _ = audit.list(db_session, resource="pickup_request", page=1, page_size=100)
    for event in events:
        snapshot = {}
        if event.before:
            snapshot.update(event.before)
        if event.after:
            snapshot.update(event.after)
        for key in snapshot.keys():
            assert "phone" not in key.lower()


# ─── Status enum ───────────────────────────────────────────────────────────────


def test_pickup_status_enum_contains_disputed():
    values = {status.value for status in PickupStatus}
    assert "disputed" in values
