"""Security and authorization boundary tests for Waste-IQ V1 (WIQ-V1-044)."""

from app.models.user import UserRole

# ─── 1. Email Verification Enforcement ────────────────────────────────────────


def test_unverified_citizen_cannot_create_pickup(
    client, make_user, auth_headers, valid_pickup_payload
):
    unverified_citizen = make_user(
        role=UserRole.citizen, email="unverified_c@test.com", email_verified=False
    )
    headers = auth_headers(unverified_citizen)

    response = client.post("/pickup-requests", data=valid_pickup_payload, headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Email verification required"


def test_unverified_citizen_cannot_patch_pickup(
    client, make_user, auth_headers, citizen_headers, valid_pickup_payload
):
    created = client.post(
        "/pickup-requests", data=valid_pickup_payload, headers=citizen_headers
    ).json()

    # User whose email became unverified or token used by unverified account
    unverified_owner = make_user(
        role=UserRole.citizen,
        email="unverified_owner@test.com",
        phone="9000000091",
        email_verified=False,
    )
    headers = auth_headers(unverified_owner)

    response = client.patch(
        f"/pickup-requests/{created['id']}", json={"waste_type": "New Type"}, headers=headers
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Email verification required"


def test_unverified_citizen_cannot_cancel_pickup(
    client, make_user, auth_headers, valid_pickup_payload
):
    unverified_citizen = make_user(
        role=UserRole.citizen,
        email="unverified_c2@test.com",
        phone="9000000092",
        email_verified=False,
    )
    headers = auth_headers(unverified_citizen)

    response = client.post("/pickup-requests/1/cancel", headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Email verification required"


def test_unverified_collector_cannot_accept_pickup(
    client, make_user, auth_headers, citizen_headers, valid_pickup_payload
):
    created = client.post(
        "/pickup-requests", data=valid_pickup_payload, headers=citizen_headers
    ).json()

    unverified_collector = make_user(
        role=UserRole.collector,
        email="unverified_col@test.com",
        phone="9000000093",
        email_verified=False,
    )
    headers = auth_headers(unverified_collector)

    response = client.post(f"/collector/pickups/{created['id']}/accept", headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Email verification required"

    # Legacy endpoint check
    legacy_resp = client.post(f"/collector/accept/{created['id']}", headers=headers)
    assert legacy_resp.status_code == 403
    assert legacy_resp.json()["detail"] == "Email verification required"


def test_unverified_collector_cannot_report_location(client, make_user, auth_headers):
    unverified_collector = make_user(
        role=UserRole.collector, email="unverified_loc@test.com", email_verified=False
    )
    headers = auth_headers(unverified_collector)

    response = client.post(
        "/collector/location",
        json={"latitude": 22.5726, "longitude": 88.3639, "accuracy": 10.0},
        headers=headers,
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Email verification required"


def test_unverified_dealer_cannot_submit_profile(client, make_user, auth_headers):
    unverified_dealer = make_user(
        role=UserRole.dealer, email="unverified_dlr@test.com", email_verified=False
    )
    headers = auth_headers(unverified_dealer)

    response = client.post(
        "/dealer/profile",
        json={
            "business_name": "Eco Traders",
            "owner_name": "Jane Dealer",
            "phone": "9876543210",
            "address": "12 Trade Road",
            "city": "Kolkata",
            "postal_code": "700001",
            "materials_accepted": ["plastic", "paper"],
        },
        headers=headers,
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Email verification required"


# ─── 2. PII / Phone Number Redaction ──────────────────────────────────────────


def test_available_pickup_queue_redacts_citizen_phone(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    created = client.post(
        "/pickup-requests", data=valid_pickup_payload, headers=citizen_headers
    ).json()
    assert created["citizen_phone"] is not None

    # Available queue
    available_resp = client.get("/collector/pickups/available", headers=collector_headers)
    assert available_resp.status_code == 200
    available_items = available_resp.json()
    match = next(item for item in available_items if item["id"] == created["id"])
    assert match["citizen_phone"] is None


def test_nearby_pickup_queue_redacts_citizen_phone(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    created = client.post(
        "/pickup-requests", data=valid_pickup_payload, headers=citizen_headers
    ).json()

    nearby_resp = client.get(
        "/collector/nearby",
        params={
            "latitude": valid_pickup_payload["latitude"],
            "longitude": valid_pickup_payload["longitude"],
            "radius_km": 5,
        },
        headers=collector_headers,
    )
    assert nearby_resp.status_code == 200
    items = nearby_resp.json()
    match = next(item for item in items if item["id"] == created["id"])
    assert match["citizen_phone"] is None


def test_unassigned_pickup_detail_redacts_citizen_phone_for_collector(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    created = client.post(
        "/pickup-requests", data=valid_pickup_payload, headers=citizen_headers
    ).json()

    detail_resp = client.get(f"/collector/pickups/{created['id']}", headers=collector_headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["citizen_phone"] is None


def test_assigned_pickup_exposes_citizen_phone_only_to_assigned_collector(
    client,
    citizen_headers,
    collector_headers,
    second_collector_headers,
    valid_pickup_payload,
):
    created = client.post(
        "/pickup-requests", data=valid_pickup_payload, headers=citizen_headers
    ).json()

    # Collector 1 accepts
    client.post(f"/collector/pickups/{created['id']}/accept", headers=collector_headers)

    # Collector 1 views assigned detail
    assigned_detail = client.get(
        f"/collector/pickups/{created['id']}", headers=collector_headers
    ).json()
    assert assigned_detail["citizen_phone"] is not None

    # Collector 2 cannot view assigned pickup (403 IDOR boundary)
    second_resp = client.get(
        f"/collector/pickups/{created['id']}", headers=second_collector_headers
    )
    assert second_resp.status_code == 403


# ─── 3. Object-Level Authorization (IDOR / BOLA) ──────────────────────────────


def test_collector_a_cannot_mutate_collector_b_assigned_pickup(
    client, citizen_headers, collector_headers, second_collector_headers, valid_pickup_payload
):
    created = client.post(
        "/pickup-requests", data=valid_pickup_payload, headers=citizen_headers
    ).json()
    client.post(f"/collector/pickups/{created['id']}/accept", headers=collector_headers)

    # Collector 2 attempts start
    start_resp = client.post(
        f"/collector/pickups/{created['id']}/start", headers=second_collector_headers
    )
    assert start_resp.status_code == 403

    # Collector 2 attempts collect
    collect_resp = client.post(
        f"/collector/pickups/{created['id']}/collect", headers=second_collector_headers
    )
    assert collect_resp.status_code == 403

    # Collector 2 attempts complete
    complete_resp = client.post(
        f"/collector/pickups/{created['id']}/complete",
        json={"weight_kg": 5.0},
        headers=second_collector_headers,
    )
    assert complete_resp.status_code == 403

    # Collector 2 attempts cancel assignment
    cancel_resp = client.post(
        f"/collector/pickups/{created['id']}/cancel", headers=second_collector_headers
    )
    assert cancel_resp.status_code == 403


def test_collector_cannot_navigate_to_another_collectors_assigned_pickup(
    client, citizen_headers, collector_headers, second_collector_headers, valid_pickup_payload
):
    created = client.post(
        "/pickup-requests", data=valid_pickup_payload, headers=citizen_headers
    ).json()
    client.post(f"/collector/pickups/{created['id']}/accept", headers=collector_headers)

    # Collector 2 attempts navigation
    nav_resp = client.get(
        f"/collector/navigation/{created['id']}",
        params={"latitude": 22.5726, "longitude": 88.3639},
        headers=second_collector_headers,
    )
    assert nav_resp.status_code == 404


def test_user_cannot_access_other_users_notification(
    client, citizen_headers, make_user, auth_headers
):
    other_citizen = make_user(
        role=UserRole.citizen, email="other_notif@test.com", phone="9000000094"
    )
    other_headers = auth_headers(other_citizen)

    # Trigger a notification for citizen 1
    # Check that other citizen gets 404 when querying an id that belongs to citizen 1
    get_resp = client.get("/notifications/999999", headers=other_headers)
    assert get_resp.status_code == 404

    read_resp = client.post("/notifications/999999/read", headers=other_headers)
    assert read_resp.status_code == 404

    delete_resp = client.delete("/notifications/999999", headers=other_headers)
    assert delete_resp.status_code == 404


def test_non_admin_cannot_access_admin_endpoints(
    client, citizen_headers, collector_headers, dealer_headers
):
    admin_endpoints = [
        ("GET", "/admin/users"),
        ("GET", "/admin/dealers"),
        ("GET", "/admin/dealers/pending"),
        ("GET", "/admin/audit-logs"),
        ("GET", "/admin/jobs/status"),
        ("GET", "/admin/analytics/overview"),
        ("GET", "/admin/analytics/materials"),
        ("GET", "/admin/analytics/collectors"),
    ]

    for role_headers in [citizen_headers, collector_headers, dealer_headers]:
        for method, path in admin_endpoints:
            if method == "GET":
                resp = client.get(path, headers=role_headers)
            else:
                resp = client.post(path, headers=role_headers)
            assert resp.status_code == 403, f"{method} {path} should return 403 for non-admin"
