from datetime import datetime, timedelta, timezone

from app.models.notification import NotificationType

# ─── Helpers ──────────────────────────────────────────────────────────────────


def _create_notification(db_session, user, *, type=NotificationType.system, title="Hello"):
    from app.models.notification import Notification

    notification = Notification(
        user_id=user.id,
        type=type,
        title=title,
        message=f"Message for {title}",
        link="/dashboard/overview",
        metadata_json={"request_id": 1},
    )
    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)
    return notification


def _all_for_user(client, headers, **params):
    response = client.get("/notifications", headers=headers, params={"page_size": 50, **params})
    assert response.status_code == 200
    return response.json()["items"]


# ─── Core CRUD & ownership ────────────────────────────────────────────────────


def test_list_notifications_requires_auth(client):
    assert client.get("/notifications").status_code == 401


def test_list_notifications_empty(client, citizen_headers):
    response = client.get("/notifications", headers=citizen_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total_items"] == 0


def test_list_notifications_returns_owned_only(
    client, citizen_headers, dealer_headers, citizen_user, dealer_user, db_session
):
    mine = _create_notification(db_session, citizen_user, title="Mine")
    _create_notification(db_session, dealer_user, title="Theirs")

    items = _all_for_user(client, citizen_headers)
    assert [item["id"] for item in items] == [mine.id]

    dealer_items = _all_for_user(client, dealer_headers)
    assert [item["title"] for item in dealer_items] == ["Theirs"]


def test_list_notification_fields(client, citizen_headers, citizen_user, db_session):
    created = _create_notification(db_session, citizen_user, title="Latest")

    items = _all_for_user(client, citizen_headers)
    assert len(items) == 1
    item = items[0]
    assert item["id"] == created.id
    assert item["type"] == "system"
    assert item["status"] == "unread"
    assert item["message"] == "Message for Latest"
    assert item["link"] == "/dashboard/overview"
    assert item["metadata_json"] == {"request_id": 1}
    assert item["user_id"] == citizen_user.id
    assert item["read_at"] is None


def test_list_unread_and_count(client, citizen_headers, citizen_user, db_session):
    _create_notification(db_session, citizen_user, type=NotificationType.system)
    _create_notification(db_session, citizen_user, type=NotificationType.pickup_accepted)

    count = client.get("/notifications/unread/count", headers=citizen_headers).json()
    assert count["unread_count"] == 2

    unread = client.get("/notifications/unread", headers=citizen_headers).json()
    assert len(unread) == 2
    assert all(item["status"] == "unread" for item in unread)


def test_list_notifications_filter_status(client, citizen_headers, citizen_user, db_session):
    notification = _create_notification(db_session, citizen_user)
    client.post(f"/notifications/{notification.id}/read", headers=citizen_headers)

    read_items = _all_for_user(client, citizen_headers, status="read")
    assert len(read_items) == 1
    assert read_items[0]["status"] == "read"

    unread_items = _all_for_user(client, citizen_headers, status="unread")
    assert unread_items == []


def test_list_notifications_invalid_status_400(client, citizen_headers):
    response = client.get("/notifications", params={"status": "nope"}, headers=citizen_headers)
    assert response.status_code == 400


def test_list_notifications_pagination(client, citizen_headers, citizen_user, db_session):
    for index in range(5):
        _create_notification(db_session, citizen_user, title=f"N{index}")

    response = client.get(
        "/notifications", params={"page": 2, "page_size": 2}, headers=citizen_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["total_items"] == 5
    assert body["total_pages"] == 3


def test_get_foreign_notification_404(client, citizen_headers, dealer_user, db_session):
    other = _create_notification(db_session, dealer_user)
    assert client.get(f"/notifications/{other.id}", headers=citizen_headers).status_code == 404


def test_get_missing_notification_404(client, citizen_headers):
    assert client.get("/notifications/999999", headers=citizen_headers).status_code == 404


def test_mark_read(client, citizen_headers, citizen_user, db_session):
    notification = _create_notification(db_session, citizen_user)

    response = client.post(f"/notifications/{notification.id}/read", headers=citizen_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "read"
    assert body["read_at"] is not None

    count = client.get("/notifications/unread/count", headers=citizen_headers).json()
    assert count["unread_count"] == 0


def test_mark_read_is_idempotent(client, citizen_headers, citizen_user, db_session):
    notification = _create_notification(db_session, citizen_user)
    client.post(f"/notifications/{notification.id}/read", headers=citizen_headers)
    response = client.post(f"/notifications/{notification.id}/read", headers=citizen_headers)
    assert response.status_code == 200


def test_mark_all_read(client, citizen_headers, citizen_user, db_session):
    for index in range(3):
        _create_notification(db_session, citizen_user, title=f"N{index}")

    response = client.post("/notifications/read-all", headers=citizen_headers)
    assert response.json()["affected"] == 3

    assert client.get("/notifications/unread", headers=citizen_headers).json() == []


def test_delete_notification(client, citizen_headers, citizen_user, db_session):
    notification = _create_notification(db_session, citizen_user)

    response = client.delete(f"/notifications/{notification.id}", headers=citizen_headers)
    assert response.status_code == 204
    assert (
        client.get(f"/notifications/{notification.id}", headers=citizen_headers).status_code == 404
    )


def test_delete_read_notifications(client, citizen_headers, citizen_user, db_session):
    first = _create_notification(db_session, citizen_user)
    second = _create_notification(db_session, citizen_user)
    client.post(f"/notifications/{first.id}/read", headers=citizen_headers)

    response = client.delete("/notifications/read", headers=citizen_headers)
    assert response.json()["affected"] == 1

    remaining = _all_for_user(client, citizen_headers)
    assert [item["id"] for item in remaining] == [second.id]


def test_other_roles_can_access_notifications(
    client, collector_headers, dealer_headers, admin_headers
):
    for headers in (collector_headers, dealer_headers, admin_headers):
        response = client.get("/notifications", headers=headers)
        assert response.status_code == 200


# ─── Pickup lifecycle hooks ───────────────────────────────────────────────────


def test_create_pickup_notifies_citizen(client, citizen_headers, valid_pickup_payload):
    response = client.post("/pickup-requests", data=valid_pickup_payload, headers=citizen_headers)
    assert response.status_code == 201

    kinds = [item["type"] for item in _all_for_user(client, citizen_headers)]
    assert "pickup_created" in kinds


def test_pickup_lifecycle_notifies_citizen(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    created = client.post(
        "/pickup-requests", data=valid_pickup_payload, headers=citizen_headers
    ).json()
    pickup_id = created["id"]

    assert (
        client.post(f"/collector/pickups/{pickup_id}/accept", headers=collector_headers).status_code
        == 200
    )
    assert (
        client.post(f"/collector/pickups/{pickup_id}/start", headers=collector_headers).status_code
        == 200
    )
    assert (
        client.post(
            f"/collector/pickups/{pickup_id}/collect", headers=collector_headers
        ).status_code
        == 200
    )
    complete = client.post(
        f"/collector/pickups/{pickup_id}/complete",
        json={"weight_kg": 4.5},
        headers=collector_headers,
    )
    assert complete.status_code == 200

    kinds = [item["type"] for item in _all_for_user(client, citizen_headers)]
    for expected in (
        "pickup_created",
        "pickup_accepted",
        "pickup_started",
        "pickup_collected",
        "pickup_completed",
    ):
        assert expected in kinds, f"missing {expected} in {kinds}"


# ─── Dealer approval hooks ────────────────────────────────────────────────────


def test_dealer_submission_notifies_admins(
    client, dealer_headers, admin_headers, draft_dealer_profile
):
    response = client.post("/dealer/profile/submit", headers=dealer_headers)
    assert response.status_code == 200

    kinds = [item["type"] for item in _all_for_user(client, admin_headers)]
    assert "dealer_profile_submitted" in kinds


def test_admin_approve_notifies_dealer(
    client, admin_headers, dealer_headers, submitted_dealer_profile
):
    response = client.post(
        f"/admin/dealers/{submitted_dealer_profile.user_id}/approve", headers=admin_headers
    )
    assert response.status_code == 200

    kinds = [item["type"] for item in _all_for_user(client, dealer_headers)]
    assert "dealer_profile_approved" in kinds


def test_admin_reject_notifies_dealer(
    client, admin_headers, dealer_headers, submitted_dealer_profile
):
    response = client.post(
        f"/admin/dealers/{submitted_dealer_profile.user_id}/reject",
        json={"reason": "Missing GST"},
        headers=admin_headers,
    )
    assert response.status_code == 200

    kinds = [item["type"] for item in _all_for_user(client, dealer_headers)]
    assert "dealer_profile_rejected" in kinds


# ─── Inventory marketplace hooks ──────────────────────────────────────────────


def test_inventory_created_notifies_citizen(
    client,
    admin_headers,
    citizen_headers,
    completed_pickup_with_assignment,
    material_category,
    active_pricing_rule,
):
    response = client.post(
        "/admin/inventory-lots",
        json={
            "pickup_request_id": completed_pickup_with_assignment.id,
            "material_category_id": material_category.id,
        },
        headers=admin_headers,
    )
    assert response.status_code == 201

    kinds = [item["type"] for item in _all_for_user(client, citizen_headers)]
    assert "inventory_created" in kinds


def test_reserve_notifies_citizen_and_dealer(
    client,
    citizen_headers,
    dealer_headers,
    approved_dealer_profile,
    inventory_lot,
):
    response = client.post(
        f"/dealer/inventory-lots/{inventory_lot.id}/reserve", headers=dealer_headers
    )
    assert response.status_code == 200

    citizen_kinds = [item["type"] for item in _all_for_user(client, citizen_headers)]
    assert "inventory_reserved" in citizen_kinds

    dealer_kinds = [item["type"] for item in _all_for_user(client, dealer_headers)]
    assert "inventory_reserved" in dealer_kinds


def test_cancel_reservation_notifies_citizen(
    client,
    citizen_headers,
    dealer_headers,
    approved_dealer_profile,
    inventory_lot,
):
    client.post(f"/dealer/inventory-lots/{inventory_lot.id}/reserve", headers=dealer_headers)
    response = client.post(
        f"/marketplace/inventory/{inventory_lot.id}/cancel-reservation", headers=dealer_headers
    )
    assert response.status_code == 200

    kinds = [item["type"] for item in _all_for_user(client, citizen_headers)]
    assert "reservation_cancelled" in kinds


def test_purchase_notifies_citizen(
    client,
    citizen_headers,
    dealer_headers,
    approved_dealer_profile,
    inventory_lot,
):
    client.post(f"/dealer/inventory-lots/{inventory_lot.id}/reserve", headers=dealer_headers)
    response = client.post(
        f"/marketplace/inventory/{inventory_lot.id}/purchase", headers=dealer_headers
    )
    assert response.status_code == 201

    kinds = [item["type"] for item in _all_for_user(client, citizen_headers)]
    assert "inventory_purchased" in kinds


def test_expired_reservation_notifies_previous_dealer(
    client,
    dealer_headers,
    approved_dealer_profile,
    inventory_lot,
    db_session,
):
    from app.models.inventory_lot import InventoryLotStatus

    client.post(f"/dealer/inventory-lots/{inventory_lot.id}/reserve", headers=dealer_headers)

    inventory_lot.status = InventoryLotStatus.reserved
    inventory_lot.reserved_at = datetime.now(timezone.utc) - timedelta(hours=25)
    inventory_lot.reservation_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db_session.commit()

    # Trigger the sweep through a dealer listing.
    response = client.get("/dealer/inventory-lots", headers=dealer_headers)
    assert response.status_code == 200

    kinds = [item["type"] for item in _all_for_user(client, dealer_headers)]
    assert "reservation_expired" in kinds


# ─── Admin broadcast ──────────────────────────────────────────────────────────


def test_admin_broadcast_reaches_all_users(
    client, admin_headers, citizen_headers, collector_headers, dealer_headers
):
    response = client.post(
        "/admin/notifications/broadcast",
        json={"title": "System downtime", "message": "Site under maintenance tonight."},
        headers=admin_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "admin_announcement"
    assert body["recipients_count"] == 4  # admin + citizen + collector + dealer

    for headers in (citizen_headers, collector_headers, dealer_headers):
        kinds = [item["type"] for item in _all_for_user(client, headers)]
        assert "admin_announcement" in kinds


def test_admin_broadcast_by_role(client, admin_headers, citizen_headers, dealer_headers):
    response = client.post(
        "/admin/notifications/broadcast",
        json={
            "title": "Dealer only",
            "message": "Marketplace update.",
            "recipient_roles": ["dealer"],
        },
        headers=admin_headers,
    )
    assert response.json()["recipients_count"] == 1

    citizen_kinds = [item["type"] for item in _all_for_user(client, citizen_headers)]
    dealer_kinds = [item["type"] for item in _all_for_user(client, dealer_headers)]
    assert "admin_announcement" not in citizen_kinds
    assert "admin_announcement" in dealer_kinds


def test_admin_broadcast_invalid_role_400(client, admin_headers):
    response = client.post(
        "/admin/notifications/broadcast",
        json={
            "title": "Bad",
            "message": "Nope",
            "recipient_roles": ["super-admin"],
        },
        headers=admin_headers,
    )
    assert response.status_code == 400


def test_non_admin_cannot_broadcast(client, citizen_headers):
    response = client.post(
        "/admin/notifications/broadcast",
        json={"title": "Nope", "message": "Nope"},
        headers=citizen_headers,
    )
    assert response.status_code == 403
