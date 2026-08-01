from typing import Any

VALID_DEALER_PROFILE_PAYLOAD: dict[str, Any] = {
    "business_name": "Kolkata Recyclers Pvt Ltd",
    "owner_name": "Test Owner",
    "phone": "9876500001",
    "email": "owner@kolkata-recyclers.in",
    "address": "78 Industrial Estate, Kolkata",
    "city": "Kolkata",
    "state": "West Bengal",
    "postal_code": "700001",
    "materials_accepted": ["PET Plastic", "Cardboard"],
}


# ─── Profile creation ─────────────────────────────────────────────────────────


def test_create_dealer_profile_success(client, dealer_headers):
    response = client.post(
        "/dealer/profile", json=VALID_DEALER_PROFILE_PAYLOAD, headers=dealer_headers
    )
    assert response.status_code == 201
    body = response.json()
    assert body["approval_status"] == "draft"
    assert body["materials_accepted"] == ["PET Plastic", "Cardboard"]
    assert body["postal_code"] == "700001"
    assert body["profile_completion"] == 100


def test_create_dealer_profile_twice_fails(client, dealer_headers):
    client.post("/dealer/profile", json=VALID_DEALER_PROFILE_PAYLOAD, headers=dealer_headers)
    response = client.post(
        "/dealer/profile", json=VALID_DEALER_PROFILE_PAYLOAD, headers=dealer_headers
    )
    assert response.status_code == 400


def test_citizen_cannot_create_dealer_profile(client, citizen_headers):
    response = client.post(
        "/dealer/profile", json=VALID_DEALER_PROFILE_PAYLOAD, headers=citizen_headers
    )
    assert response.status_code == 403


def test_create_dealer_profile_empty_materials_fails(client, dealer_headers):
    payload = {**VALID_DEALER_PROFILE_PAYLOAD, "materials_accepted": []}
    response = client.post("/dealer/profile", json=payload, headers=dealer_headers)
    assert response.status_code == 422


def test_create_dealer_profile_empty_business_name_fails(client, dealer_headers):
    payload = {**VALID_DEALER_PROFILE_PAYLOAD, "business_name": ""}
    response = client.post("/dealer/profile", json=payload, headers=dealer_headers)
    assert response.status_code == 422


def test_create_dealer_profile_invalid_phone_fails(client, dealer_headers):
    payload = {**VALID_DEALER_PROFILE_PAYLOAD, "phone": "not-a-phone"}
    response = client.post("/dealer/profile", json=payload, headers=dealer_headers)
    assert response.status_code == 422


def test_create_dealer_profile_invalid_email_fails(client, dealer_headers):
    payload = {**VALID_DEALER_PROFILE_PAYLOAD, "email": "not-an-email"}
    response = client.post("/dealer/profile", json=payload, headers=dealer_headers)
    assert response.status_code == 422


def test_get_dealer_profile_not_found(client, dealer_headers):
    response = client.get("/dealer/profile", headers=dealer_headers)
    assert response.status_code == 404


def test_get_dealer_profile_success(client, dealer_headers):
    client.post("/dealer/profile", json=VALID_DEALER_PROFILE_PAYLOAD, headers=dealer_headers)
    response = client.get("/dealer/profile", headers=dealer_headers)
    assert response.status_code == 200
    assert response.json()["business_name"] == "Kolkata Recyclers Pvt Ltd"


def test_update_dealer_profile_resets_to_draft(client, dealer_headers, db_session, dealer_user):
    """Editing a submitted/approved profile should reset approval_status to draft."""
    from app.services.dealer_profiles import DealerProfileService
    from app.services.dealer_approval import AdminDealerApprovalService

    profile_service = DealerProfileService()
    approval_service = AdminDealerApprovalService()

    client.post("/dealer/profile", json=VALID_DEALER_PROFILE_PAYLOAD, headers=dealer_headers)
    profile_service.submit_profile(db_session, dealer_user)
    approval_service.approve_dealer(db_session, dealer_user, dealer_user.id)

    response = client.put(
        "/dealer/profile", json={"business_name": "Updated Name Ltd"}, headers=dealer_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["business_name"] == "Updated Name Ltd"
    assert body["approval_status"] == "draft"
    assert body["is_verified"] is False


# ─── Submission ───────────────────────────────────────────────────────────────


def test_submit_profile_moves_draft_to_submitted(client, dealer_headers):
    client.post("/dealer/profile", json=VALID_DEALER_PROFILE_PAYLOAD, headers=dealer_headers)
    response = client.post("/dealer/profile/submit", headers=dealer_headers)
    assert response.status_code == 200
    assert response.json()["approval_status"] == "submitted"


def test_submit_profile_without_profile_raises_404(client, dealer_headers):
    response = client.post("/dealer/profile/submit", headers=dealer_headers)
    assert response.status_code == 404


def test_profile_timeline_returns_events_newest_first(client, dealer_headers, dealer_user):
    client.post("/dealer/profile", json=VALID_DEALER_PROFILE_PAYLOAD, headers=dealer_headers)
    client.post("/dealer/profile/submit", headers=dealer_headers)

    response = client.get("/dealer/profile/timeline", headers=dealer_headers)
    assert response.status_code == 200

    events = response.json()
    assert [event["status"] for event in events] == ["submitted", "draft"]
    assert events[0]["note"] == "Profile submitted for review."
    assert events[0]["actor_name"] == dealer_user.name


def test_profile_timeline_without_profile_raises_404(client, dealer_headers):
    response = client.get("/dealer/profile/timeline", headers=dealer_headers)
    assert response.status_code == 404


def test_approve_profile_then_submit_is_invalid(client, dealer_headers, db_session, dealer_user):
    """Approved profiles cannot be submitted again until they are edited."""
    from app.services.dealer_profiles import DealerProfileService
    from app.services.dealer_approval import AdminDealerApprovalService

    client.post("/dealer/profile", json=VALID_DEALER_PROFILE_PAYLOAD, headers=dealer_headers)
    DealerProfileService().submit_profile(db_session, dealer_user)
    AdminDealerApprovalService().approve_dealer(db_session, dealer_user, dealer_user.id)

    response = client.post("/dealer/profile/submit", headers=dealer_headers)
    assert response.status_code == 400


# ─── Approval workflow (service layer) ────────────────────────────────────────


def test_approve_dealer_profile_sets_status_and_timestamp(db_session, dealer_user):
    from app.services.dealer_profiles import DealerProfileService
    from app.services.dealer_approval import AdminDealerApprovalService
    from app.schemas.dealer import DealerProfileCreate

    DealerProfileService().create_profile(
        db_session, dealer_user, DealerProfileCreate(**VALID_DEALER_PROFILE_PAYLOAD)
    )
    DealerProfileService().submit_profile(db_session, dealer_user)
    result = AdminDealerApprovalService().approve_dealer(db_session, dealer_user, dealer_user.id)

    assert result.approval_status == "approved"
    assert result.approved_at is not None
    assert result.is_verified is True


def test_reject_dealer_profile_records_reason_and_clears_approval(db_session, dealer_user):
    from app.services.dealer_profiles import DealerProfileService
    from app.services.dealer_approval import AdminDealerApprovalService
    from app.schemas.dealer import DealerProfileCreate

    service = DealerProfileService()
    approval_service = AdminDealerApprovalService()

    service.create_profile(
        db_session, dealer_user, DealerProfileCreate(**VALID_DEALER_PROFILE_PAYLOAD)
    )
    service.submit_profile(db_session, dealer_user)
    result = approval_service.reject_dealer(
        db_session, dealer_user, dealer_user.id, "Incorrect GST"
    )

    assert result.approval_status == "rejected"
    assert result.rejection_reason == "Incorrect GST"
    assert result.approved_at is None
    assert result.is_verified is False


def test_approve_nonexistent_dealer_profile_raises_404(db_session, admin_user):
    from app.services.dealer_approval import AdminDealerApprovalService
    from fastapi import HTTPException
    import pytest

    with pytest.raises(HTTPException) as exc_info:
        AdminDealerApprovalService().approve_dealer(db_session, admin_user, 999999)
    assert exc_info.value.status_code == 404


# ─── Marketplace listing ──────────────────────────────────────────────────────


def test_approved_dealer_can_list_inventory(
    client, dealer_headers, approved_dealer_profile, inventory_lot
):
    response = client.get("/dealer/inventory-lots", headers=dealer_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total_items"] == 1
    assert body["items"][0]["id"] == inventory_lot.id


def test_pending_dealer_cannot_list_inventory(client, dealer_headers, submitted_dealer_profile):
    response = client.get("/dealer/inventory-lots", headers=dealer_headers)
    assert response.status_code == 403


def test_dealer_without_profile_cannot_list_inventory(client, dealer_headers):
    response = client.get("/dealer/inventory-lots", headers=dealer_headers)
    assert response.status_code == 403


def test_citizen_cannot_access_dealer_inventory_listing(client, citizen_headers):
    response = client.get("/dealer/inventory-lots", headers=citizen_headers)
    assert response.status_code == 403


def test_dealer_listing_excludes_archived_lots(
    client, dealer_headers, approved_dealer_profile, inventory_lot, db_session
):
    from datetime import datetime, timezone
    from app.models.inventory_lot import InventoryLotVisibility

    inventory_lot.archived_at = datetime.now(timezone.utc)
    inventory_lot.visibility = InventoryLotVisibility.hidden
    db_session.commit()

    response = client.get("/dealer/inventory-lots", headers=dealer_headers)
    assert response.status_code == 200
    assert response.json()["total_items"] == 0


# ─── Marketplace detail ───────────────────────────────────────────────────────


def test_approved_dealer_can_view_lot_detail(
    client, dealer_headers, approved_dealer_profile, inventory_lot
):
    response = client.get(f"/dealer/inventory-lots/{inventory_lot.id}", headers=dealer_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["lot_number"] == "LOT-2026-000001"
    assert body["status"] == "available"


def test_dealer_cannot_view_hidden_lot_detail(
    client, dealer_headers, approved_dealer_profile, inventory_lot, db_session
):
    from app.models.inventory_lot import InventoryLotVisibility

    inventory_lot.visibility = InventoryLotVisibility.hidden
    db_session.commit()

    response = client.get(f"/dealer/inventory-lots/{inventory_lot.id}", headers=dealer_headers)
    assert response.status_code == 404


def test_dealer_cannot_view_nonexistent_lot(client, dealer_headers, approved_dealer_profile):
    response = client.get("/dealer/inventory-lots/999999", headers=dealer_headers)
    assert response.status_code == 404


# ─── Reservation ───────────────────────────────────────────────────────────────


def test_approved_dealer_can_reserve_available_lot(
    client, dealer_headers, approved_dealer_profile, inventory_lot
):
    response = client.post(
        f"/dealer/inventory-lots/{inventory_lot.id}/reserve", headers=dealer_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "reserved"
    assert body["reservation_expires_at"] is not None


def test_reserve_already_reserved_lot_returns_409(
    client,
    dealer_headers,
    approved_dealer_profile,
    second_dealer_headers,
    second_dealer_user,
    db_session,
    inventory_lot,
):
    from app.models.dealer_profile import DealerProfile, DealerApprovalStatus
    from datetime import datetime, timezone

    second_profile = DealerProfile(
        user_id=second_dealer_user.id,
        business_name="Second Dealer Co",
        owner_name="Second Owner",
        phone="9876500002",
        address="99 Second Lane, Kolkata",
        city="Kolkata",
        postal_code="700003",
        materials_accepted=["PET Plastic"],
        approval_status=DealerApprovalStatus.approved,
        is_verified=True,
        approved_at=datetime.now(timezone.utc),
    )
    db_session.add(second_profile)
    db_session.commit()

    first = client.post(
        f"/dealer/inventory-lots/{inventory_lot.id}/reserve", headers=dealer_headers
    )
    assert first.status_code == 200

    second = client.post(
        f"/dealer/inventory-lots/{inventory_lot.id}/reserve", headers=second_dealer_headers
    )
    assert second.status_code == 409


def test_reserve_archived_lot_returns_404(
    client, dealer_headers, approved_dealer_profile, inventory_lot, db_session
):
    from datetime import datetime, timezone
    from app.models.inventory_lot import InventoryLotVisibility

    inventory_lot.archived_at = datetime.now(timezone.utc)
    inventory_lot.visibility = InventoryLotVisibility.hidden
    db_session.commit()

    response = client.post(
        f"/dealer/inventory-lots/{inventory_lot.id}/reserve", headers=dealer_headers
    )
    assert response.status_code == 404


def test_reserve_sold_lot_returns_409(
    client, dealer_headers, approved_dealer_profile, inventory_lot, db_session
):
    from app.models.inventory_lot import InventoryLotStatus

    inventory_lot.status = InventoryLotStatus.sold
    db_session.commit()

    response = client.post(
        f"/dealer/inventory-lots/{inventory_lot.id}/reserve", headers=dealer_headers
    )
    assert response.status_code == 409


def test_pending_dealer_cannot_reserve(
    client, dealer_headers, submitted_dealer_profile, inventory_lot
):
    response = client.post(
        f"/dealer/inventory-lots/{inventory_lot.id}/reserve", headers=dealer_headers
    )
    assert response.status_code == 403


def test_reserve_sets_audit_event(
    client, dealer_headers, approved_dealer_profile, inventory_lot, db_session, admin_headers
):
    client.post(f"/dealer/inventory-lots/{inventory_lot.id}/reserve", headers=dealer_headers)

    response = client.get(f"/admin/inventory-lots/{inventory_lot.id}/events", headers=admin_headers)
    assert response.status_code == 200
    events = response.json()
    event_types = [e["event_type"] for e in events]
    assert "reserved" in event_types
