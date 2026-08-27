"""Tests for Masked Citizen–Collector Communication (WIQ-V1-047)."""

from app.core.config import Settings
from app.core.dependencies import get_settings
from app.models.user import UserRole


def _create_assigned_pickup(client, citizen_headers, collector_headers, payload):
    # Citizen creates request
    created = client.post("/pickup-requests", data=payload, headers=citizen_headers).json()
    # Collector accepts request
    client.post(f"/collector/pickups/{created['id']}/accept", headers=collector_headers)
    return created["id"]


# ─── 1. Authorization Boundaries ───────────────────────────────────────────────


def test_citizen_can_initiate_contact_on_assigned_pickup(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    pickup_id = _create_assigned_pickup(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )

    response = client.post(f"/pickup-requests/{pickup_id}/contact", headers=citizen_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["pickup_id"] == pickup_id
    assert data["status"] == "initiated"
    assert "masked_number" in data
    assert "instructions" in data
    assert "citizen_phone" not in data
    assert "collector_phone" not in data


def test_assigned_collector_can_initiate_contact(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    pickup_id = _create_assigned_pickup(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )

    response = client.post(f"/pickup-requests/{pickup_id}/contact", headers=collector_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["pickup_id"] == pickup_id
    assert data["status"] == "initiated"


def test_unassigned_collector_cannot_initiate_contact(
    client, citizen_headers, collector_headers, second_collector_headers, valid_pickup_payload
):
    pickup_id = _create_assigned_pickup(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )

    response = client.post(
        f"/pickup-requests/{pickup_id}/contact", headers=second_collector_headers
    )
    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "You are not authorized to contact participants for this pickup request"
    )


def test_other_citizen_cannot_initiate_contact(
    client, make_user, auth_headers, citizen_headers, collector_headers, valid_pickup_payload
):
    pickup_id = _create_assigned_pickup(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )

    second_citizen = make_user(
        role=UserRole.citizen,
        email="second_c_contact@test.com",
        phone="9000000077",
        email_verified=True,
    )
    headers = auth_headers(second_citizen)

    response = client.post(f"/pickup-requests/{pickup_id}/contact", headers=headers)
    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "You are not authorized to contact participants for this pickup request"
    )


def test_unauthenticated_user_cannot_initiate_contact(client):
    response = client.post("/pickup-requests/1/contact")
    assert response.status_code == 401


def test_unverified_email_user_cannot_initiate_contact(
    client, make_user, auth_headers, citizen_headers, collector_headers, valid_pickup_payload
):
    pickup_id = _create_assigned_pickup(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )

    unverified_user = make_user(
        role=UserRole.citizen,
        email="unverified_contact@test.com",
        phone="9000000078",
        email_verified=False,
    )
    headers = auth_headers(unverified_user)

    response = client.post(f"/pickup-requests/{pickup_id}/contact", headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Email verification required"


def test_admin_can_initiate_contact(
    client, citizen_headers, collector_headers, admin_headers, valid_pickup_payload
):
    pickup_id = _create_assigned_pickup(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )

    response = client.post(f"/pickup-requests/{pickup_id}/contact", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["pickup_id"] == pickup_id


# ─── 2. Lifecycle Scoping ──────────────────────────────────────────────────────


def test_pending_unassigned_pickup_cannot_be_contacted(
    client, citizen_headers, valid_pickup_payload
):
    created = client.post(
        "/pickup-requests", data=valid_pickup_payload, headers=citizen_headers
    ).json()

    response = client.post(f"/pickup-requests/{created['id']}/contact", headers=citizen_headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "No collector has been assigned to this pickup request yet"


def test_completed_pickup_cannot_be_contacted(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    pickup_id = _create_assigned_pickup(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )

    # Move to on_the_way -> collected -> completed
    client.post(f"/collector/pickups/{pickup_id}/start", headers=collector_headers)
    client.post(f"/collector/pickups/{pickup_id}/collect", headers=collector_headers)
    client.post(
        f"/collector/pickups/{pickup_id}/complete",
        json={"weight_kg": 15.5},
        headers=collector_headers,
    )

    response = client.post(f"/pickup-requests/{pickup_id}/contact", headers=citizen_headers)
    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Contact is no longer active for completed or cancelled pickup requests"
    )


# ─── 3. PII & Security Hygiene ─────────────────────────────────────────────────


def test_contact_response_never_exposes_real_phone_numbers(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    pickup_id = _create_assigned_pickup(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )

    res_citizen = client.post(f"/pickup-requests/{pickup_id}/contact", headers=citizen_headers)
    res_collector = client.post(f"/pickup-requests/{pickup_id}/contact", headers=collector_headers)

    for data in (res_citizen.json(), res_collector.json()):
        raw_text = str(data)
        assert "citizen_phone" not in raw_text
        assert "collector_phone" not in raw_text
        assert "9876543210" not in raw_text  # Default test citizen phone
        assert "1234567890" not in raw_text  # Default test collector phone


def test_assigned_pickup_detail_redacts_citizen_phone_for_collector(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    pickup_id = _create_assigned_pickup(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )

    assigned_detail = client.get(
        f"/collector/pickups/{pickup_id}", headers=collector_headers
    ).json()
    assert assigned_detail["citizen_phone"] is None


def test_disabled_provider_returns_503_status(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    pickup_id = _create_assigned_pickup(
        client, citizen_headers, collector_headers, valid_pickup_payload
    )

    def _disabled_settings():
        return Settings(COMMUNICATION_PROVIDER="disabled")

    client.app.dependency_overrides[get_settings] = _disabled_settings
    try:
        response = client.post(f"/pickup-requests/{pickup_id}/contact", headers=citizen_headers)
        assert response.status_code == 503
        assert response.json()["detail"] == "Masked communication service is currently unavailable"
    finally:
        client.app.dependency_overrides.pop(get_settings, None)
