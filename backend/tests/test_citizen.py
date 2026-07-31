VALID_PICKUP_PAYLOAD = {
    "waste_type": "Plastic bottles",
    "address": "12 Lake Road, Kolkata, 700029",
    "latitude": 22.5726,
    "longitude": 88.3639,
}


def test_create_pickup_request_success(client, citizen_headers):
    response = client.post("/pickup-requests", data=VALID_PICKUP_PAYLOAD, headers=citizen_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["waste_type"] == "Plastic bottles"
    assert body["status"] == "pending"
    assert body["can_cancel"] is True


def test_create_pickup_request_without_photo_succeeds(client, citizen_headers):
    response = client.post("/pickup-requests", data=VALID_PICKUP_PAYLOAD, headers=citizen_headers)
    assert response.status_code == 201
    assert response.json()["image_url"] is None


def test_collector_cannot_create_pickup_request(client, collector_headers):
    response = client.post("/pickup-requests", data=VALID_PICKUP_PAYLOAD, headers=collector_headers)
    assert response.status_code == 403


def test_create_pickup_request_requires_auth(client):
    response = client.post("/pickup-requests", data=VALID_PICKUP_PAYLOAD)
    assert response.status_code == 401


def test_list_pickup_requests_returns_own_requests_only(
    client, citizen_headers, citizen_user, db_session
):
    client.post("/pickup-requests", data=VALID_PICKUP_PAYLOAD, headers=citizen_headers)

    response = client.get("/pickup-requests", headers=citizen_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["user_id"] == citizen_user.id


def test_get_pickup_request_detail_includes_timeline(client, citizen_headers):
    created = client.post(
        "/pickup-requests", data=VALID_PICKUP_PAYLOAD, headers=citizen_headers
    ).json()
    response = client.get(f"/pickup-requests/{created['id']}", headers=citizen_headers)
    assert response.status_code == 200
    body = response.json()
    assert "timeline" in body
    assert len(body["timeline"]) >= 1
    assert body["timeline"][0]["status"] == "pending"


def test_get_pickup_request_not_found(client, citizen_headers):
    response = client.get("/pickup-requests/999999", headers=citizen_headers)
    assert response.status_code == 404


def test_citizen_cannot_view_other_citizens_request(client, citizen_headers, db_session):
    from app.models.user import User, UserRole
    from app.core.security import hash_password

    other_citizen = User(
        name="Other Citizen",
        email="other@wasteiq.test",
        phone="9000099999",
        password_hash=hash_password("Test@1234"),
        role=UserRole.citizen,
    )
    db_session.add(other_citizen)
    db_session.commit()

    from app.core.security import create_access_token

    other_headers = {"Authorization": f"Bearer {create_access_token(str(other_citizen.id))}"}
    created = client.post(
        "/pickup-requests", data=VALID_PICKUP_PAYLOAD, headers=other_headers
    ).json()

    response = client.get(f"/pickup-requests/{created['id']}", headers=citizen_headers)
    assert response.status_code == 403


def test_update_pending_pickup_request_success(client, citizen_headers):
    created = client.post(
        "/pickup-requests", data=VALID_PICKUP_PAYLOAD, headers=citizen_headers
    ).json()
    response = client.patch(
        f"/pickup-requests/{created['id']}",
        json={"waste_type": "Cardboard"},
        headers=citizen_headers,
    )
    assert response.status_code == 200
    assert response.json()["waste_type"] == "Cardboard"


def test_update_pickup_request_cannot_set_status_directly(client, citizen_headers):
    """
    Citizens patching status should not bypass the cancel endpoint's business rules
    silently succeeding to an arbitrary status.
    """
    created = client.post(
        "/pickup-requests", data=VALID_PICKUP_PAYLOAD, headers=citizen_headers
    ).json()
    response = client.patch(
        f"/pickup-requests/{created['id']}",
        json={"status": "completed"},
        headers=citizen_headers,
    )
    # Service strips "status" from citizen updates entirely (update_data.pop("status", None)),
    # so the request must succeed but the status must remain unchanged.
    assert response.status_code == 200
    assert response.json()["status"] == "pending"


def test_cancel_pending_pickup_request_success(client, citizen_headers):
    created = client.post(
        "/pickup-requests", data=VALID_PICKUP_PAYLOAD, headers=citizen_headers
    ).json()
    response = client.post(f"/pickup-requests/{created['id']}/cancel", headers=citizen_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert response.json()["can_cancel"] is False


def test_cancel_already_accepted_pickup_fails(client, citizen_headers, collector_headers):
    created = client.post(
        "/pickup-requests", data=VALID_PICKUP_PAYLOAD, headers=citizen_headers
    ).json()
    client.post(f"/collector/accept/{created['id']}", headers=collector_headers)

    response = client.post(f"/pickup-requests/{created['id']}/cancel", headers=citizen_headers)
    assert response.status_code == 400


def test_cancel_other_citizens_pickup_fails(client, citizen_headers, db_session):
    from app.models.user import User, UserRole
    from app.core.security import hash_password, create_access_token

    other_citizen = User(
        name="Other Citizen 2",
        email="other2@wasteiq.test",
        phone="9000088888",
        password_hash=hash_password("Test@1234"),
        role=UserRole.citizen,
    )
    db_session.add(other_citizen)
    db_session.commit()

    other_headers = {"Authorization": f"Bearer {create_access_token(str(other_citizen.id))}"}
    created = client.post(
        "/pickup-requests", data=VALID_PICKUP_PAYLOAD, headers=other_headers
    ).json()

    response = client.post(f"/pickup-requests/{created['id']}/cancel", headers=citizen_headers)
    assert response.status_code == 403


def test_collector_cannot_cancel_pickup_request(client, citizen_headers, collector_headers):
    created = client.post(
        "/pickup-requests", data=VALID_PICKUP_PAYLOAD, headers=citizen_headers
    ).json()
    response = client.post(f"/pickup-requests/{created['id']}/cancel", headers=collector_headers)
    assert response.status_code == 403


def test_citizen_summary_counts(client, citizen_headers):
    client.post("/pickup-requests", data=VALID_PICKUP_PAYLOAD, headers=citizen_headers)
    second = client.post(
        "/pickup-requests", data=VALID_PICKUP_PAYLOAD, headers=citizen_headers
    ).json()
    client.post(f"/pickup-requests/{second['id']}/cancel", headers=citizen_headers)

    response = client.get("/pickup-requests/citizen/summary", headers=citizen_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total_requests"] == 2
    assert body["pending_requests"] == 1


def test_collector_cannot_view_citizen_summary(client, collector_headers):
    response = client.get("/pickup-requests/citizen/summary", headers=collector_headers)
    assert response.status_code == 403


def test_create_pickup_request_with_sprint5_details(client, citizen_headers):
    """Sprint 5: estimated weight, preferred time and notes are persisted and returned."""
    response = client.post(
        "/pickup-requests",
        data={
            **VALID_PICKUP_PAYLOAD,
            "estimated_weight_kg": "4.5",
            "preferred_time": "2026-08-05T09:30:00",
            "notes": "Please call before arriving at the gate.",
        },
        headers=citizen_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["estimated_weight_kg"] == 4.5
    assert body["preferred_time"] == "2026-08-05T09:30:00"
    assert body["notes"] == "Please call before arriving at the gate."


def test_create_pickup_request_without_details_returns_nulls(client, citizen_headers):
    response = client.post("/pickup-requests", data=VALID_PICKUP_PAYLOAD, headers=citizen_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["estimated_weight_kg"] is None
    assert body["preferred_time"] is None
    assert body["notes"] is None


def test_create_pickup_request_rejects_invalid_weight(client, citizen_headers):
    response = client.post(
        "/pickup-requests",
        data={**VALID_PICKUP_PAYLOAD, "estimated_weight_kg": "-3"},
        headers=citizen_headers,
    )
    assert response.status_code == 422

    too_heavy = client.post(
        "/pickup-requests",
        data={**VALID_PICKUP_PAYLOAD, "estimated_weight_kg": "15000"},
        headers=citizen_headers,
    )
    assert too_heavy.status_code == 422


def test_create_pickup_request_rejects_overlong_notes(client, citizen_headers):
    response = client.post(
        "/pickup-requests",
        data={**VALID_PICKUP_PAYLOAD, "notes": "x" * 2001},
        headers=citizen_headers,
    )
    assert response.status_code == 422


def test_list_pickup_requests_returns_sprint5_details(client, citizen_headers):
    created = client.post(
        "/pickup-requests",
        data={
            **VALID_PICKUP_PAYLOAD,
            "estimated_weight_kg": "2.0",
            "preferred_time": "2026-08-06T11:00:00",
            "notes": "Leave outside the main door.",
        },
        headers=citizen_headers,
    ).json()

    response = client.get("/pickup-requests", headers=citizen_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == created["id"]
    assert body[0]["estimated_weight_kg"] == 2.0
    assert body[0]["preferred_time"] == "2026-08-06T11:00:00"
    assert body[0]["notes"] == "Leave outside the main door."
