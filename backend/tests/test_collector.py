import pytest
from fastapi import HTTPException

from app.models.user import UserRole


def _create_pending_request(client, citizen_headers, payload) -> dict:
    return client.post("/pickup-requests", data=payload, headers=citizen_headers).json()


def test_collector_available_lists_unassigned_pending_requests(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    available_request = _create_pending_request(client, citizen_headers, valid_pickup_payload)
    assigned_request = _create_pending_request(client, citizen_headers, valid_pickup_payload)
    client.post(f"/collector/accept/{assigned_request['id']}", headers=collector_headers)

    response = client.get("/collector/available", headers=collector_headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == available_request["id"]
    assert body[0]["status"] == "pending"
    assert body[0]["assignment"] is None
    assert body[0]["assigned_collector_name"] is None
    assert body[0]["citizen_name"]
    assert body[0]["address"] == valid_pickup_payload["address"]
    assert body[0]["waste_type"] == valid_pickup_payload["waste_type"]
    assert body[0]["latitude"] == valid_pickup_payload["latitude"]
    assert body[0]["longitude"] == valid_pickup_payload["longitude"]
    assert body[0]["created_at"]


def test_collector_nearby_lists_pending_pickups_by_distance(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    near_request = _create_pending_request(client, citizen_headers, valid_pickup_payload)
    far_payload = {
        **valid_pickup_payload,
        "address": "99 Far Street, Delhi, 110001",
        "latitude": 28.6139,
        "longitude": 77.2090,
    }
    far_request = client.post("/pickup-requests", data=far_payload, headers=citizen_headers).json()

    response = client.get(
        "/collector/nearby",
        params={"latitude": 22.5720, "longitude": 88.3630, "radius_km": 5},
        headers=collector_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert [item["id"] for item in body] == [near_request["id"]]
    assert body[0]["distance_km"] >= 0
    assert far_request["id"] not in {item["id"] for item in body}


def test_collector_nearby_sorts_by_distance(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    farther_payload = {
        **valid_pickup_payload,
        "address": "22 Park Street, Kolkata, 700016",
        "latitude": 22.5540,
        "longitude": 88.3510,
    }
    nearer_payload = {
        **valid_pickup_payload,
        "address": "14 Lake Road, Kolkata, 700029",
        "latitude": 22.5727,
        "longitude": 88.3640,
    }
    farther_request = client.post(
        "/pickup-requests", data=farther_payload, headers=citizen_headers
    ).json()
    nearer_request = client.post(
        "/pickup-requests", data=nearer_payload, headers=citizen_headers
    ).json()

    response = client.get(
        "/collector/nearby",
        params={"latitude": 22.5726, "longitude": 88.3639, "radius_km": 10},
        headers=collector_headers,
    )

    assert response.status_code == 200
    body = response.json()
    returned_ids = [item["id"] for item in body]
    assert returned_ids.index(nearer_request["id"]) < returned_ids.index(farther_request["id"])
    assert body[0]["distance_km"] <= body[1]["distance_km"]


def test_collector_assigned_lists_authenticated_collector_jobs(
    client, citizen_headers, collector_headers, make_user, auth_headers, valid_pickup_payload
):
    other_collector = make_user(
        role=UserRole.collector, email="assigned-other@wasteiq.test", phone="9000044444"
    )
    other_collector_headers = auth_headers(other_collector)

    accepted_request = _create_pending_request(client, citizen_headers, valid_pickup_payload)
    on_the_way_request = _create_pending_request(client, citizen_headers, valid_pickup_payload)
    collected_request = _create_pending_request(client, citizen_headers, valid_pickup_payload)
    completed_request = _create_pending_request(client, citizen_headers, valid_pickup_payload)
    unassigned_pending_request = _create_pending_request(
        client, citizen_headers, valid_pickup_payload
    )
    other_collector_request = _create_pending_request(client, citizen_headers, valid_pickup_payload)

    client.post(f"/collector/accept/{accepted_request['id']}", headers=collector_headers)

    client.post(f"/collector/accept/{on_the_way_request['id']}", headers=collector_headers)
    client.post(f"/collector/start/{on_the_way_request['id']}", headers=collector_headers)

    client.post(f"/collector/accept/{collected_request['id']}", headers=collector_headers)
    client.post(f"/collector/start/{collected_request['id']}", headers=collector_headers)
    client.post(f"/collector/collect/{collected_request['id']}", headers=collector_headers)

    client.post(f"/collector/accept/{completed_request['id']}", headers=collector_headers)
    client.post(f"/collector/start/{completed_request['id']}", headers=collector_headers)
    client.post(f"/collector/collect/{completed_request['id']}", headers=collector_headers)
    client.post(
        f"/collector/complete/{completed_request['id']}",
        json={"weight_kg": 12},
        headers=collector_headers,
    )

    client.post(
        f"/collector/accept/{other_collector_request['id']}", headers=other_collector_headers
    )

    response = client.get("/collector/assigned", headers=collector_headers)

    assert response.status_code == 200
    body = response.json()
    returned_ids = {item["id"] for item in body}
    assert returned_ids == {
        accepted_request["id"],
        on_the_way_request["id"],
        collected_request["id"],
        completed_request["id"],
    }
    assert unassigned_pending_request["id"] not in returned_ids
    assert other_collector_request["id"] not in returned_ids
    assert {item["status"] for item in body} == {"accepted", "on_the_way", "collected", "completed"}
    assert all(item["assignment"] is not None for item in body)
    assert all(item["citizen_name"] for item in body)
    assert all(item["created_at"] for item in body)


def test_collector_accept_success(client, citizen_headers, collector_headers, valid_pickup_payload):
    request = _create_pending_request(client, citizen_headers, valid_pickup_payload)
    response = client.post(f"/collector/accept/{request['id']}", headers=collector_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


def test_citizen_cannot_accept_pickup(client, citizen_headers, valid_pickup_payload):
    request = _create_pending_request(client, citizen_headers, valid_pickup_payload)
    response = client.post(f"/collector/accept/{request['id']}", headers=citizen_headers)
    assert response.status_code == 403


def test_accept_own_request_rejected_at_service_layer(db_session, collector_user):
    """A collector cannot accept their own pickup request (service layer enforces it)."""
    from app.models.pickup_request import PickupRequest, PickupStatus
    from app.services.pickup_requests import accept_pickup_request

    own_request = PickupRequest(
        user_id=collector_user.id,
        waste_type="Plastic bottles",
        address="12 Lake Road, Kolkata, 700029",
        latitude=22.5726,
        longitude=88.3639,
        status=PickupStatus.pending,
    )
    db_session.add(own_request)
    db_session.commit()
    db_session.refresh(own_request)

    with pytest.raises(HTTPException) as exc_info:
        accept_pickup_request(db_session, collector_user, own_request.id)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Collectors cannot accept their own request"


def test_accept_already_accepted_request_fails(
    client, citizen_headers, collector_headers, make_user, auth_headers, valid_pickup_payload
):
    request = _create_pending_request(client, citizen_headers, valid_pickup_payload)
    client.post(f"/collector/accept/{request['id']}", headers=collector_headers)

    second_headers = auth_headers(
        make_user(role=UserRole.collector, email="collector2@wasteiq.test", phone="9000066666")
    )

    response = client.post(f"/collector/accept/{request['id']}", headers=second_headers)
    assert response.status_code == 400


def test_accept_nonexistent_request_fails(client, collector_headers):
    response = client.post("/collector/accept/999999", headers=collector_headers)
    assert response.status_code == 404


def test_start_request_success(client, citizen_headers, collector_headers, valid_pickup_payload):
    request = _create_pending_request(client, citizen_headers, valid_pickup_payload)
    client.post(f"/collector/accept/{request['id']}", headers=collector_headers)

    response = client.post(f"/collector/start/{request['id']}", headers=collector_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "on_the_way"


def test_start_pending_request_fails(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    """Cannot start a request that hasn't been accepted yet."""
    request = _create_pending_request(client, citizen_headers, valid_pickup_payload)
    response = client.post(f"/collector/start/{request['id']}", headers=collector_headers)
    assert response.status_code == 403


def test_start_request_not_assigned_to_this_collector_fails(
    client, citizen_headers, collector_headers, make_user, auth_headers, valid_pickup_payload
):
    request = _create_pending_request(client, citizen_headers, valid_pickup_payload)
    client.post(f"/collector/accept/{request['id']}", headers=collector_headers)

    other_headers = auth_headers(
        make_user(role=UserRole.collector, email="othercollector@wasteiq.test", phone="9000055555")
    )

    response = client.post(f"/collector/start/{request['id']}", headers=other_headers)
    assert response.status_code == 403


def test_collect_request_success(client, citizen_headers, collector_headers, valid_pickup_payload):
    request = _create_pending_request(client, citizen_headers, valid_pickup_payload)
    client.post(f"/collector/accept/{request['id']}", headers=collector_headers)
    client.post(f"/collector/start/{request['id']}", headers=collector_headers)

    response = client.post(f"/collector/collect/{request['id']}", headers=collector_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "collected"


def test_collect_accepted_but_not_started_request_fails(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    """Cannot skip directly from accepted -> collected, must go through on_the_way."""
    request = _create_pending_request(client, citizen_headers, valid_pickup_payload)
    client.post(f"/collector/accept/{request['id']}", headers=collector_headers)

    response = client.post(f"/collector/collect/{request['id']}", headers=collector_headers)
    assert response.status_code == 400


def test_complete_request_success(client, citizen_headers, collector_headers, valid_pickup_payload):
    request = _create_pending_request(client, citizen_headers, valid_pickup_payload)
    client.post(f"/collector/accept/{request['id']}", headers=collector_headers)
    client.post(f"/collector/start/{request['id']}", headers=collector_headers)
    client.post(f"/collector/collect/{request['id']}", headers=collector_headers)

    response = client.post(
        f"/collector/complete/{request['id']}",
        json={"weight_kg": 15.5},
        headers=collector_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["assignment"]["weight_kg"] == 15.5


def test_complete_request_skipping_collected_state_fails(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    """Cannot complete directly from accepted, must pass through on_the_way and collected."""
    request = _create_pending_request(client, citizen_headers, valid_pickup_payload)
    client.post(f"/collector/accept/{request['id']}", headers=collector_headers)

    response = client.post(
        f"/collector/complete/{request['id']}",
        json={"weight_kg": 10.0},
        headers=collector_headers,
    )
    assert response.status_code == 400


def test_complete_request_with_zero_weight_rejected(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    request = _create_pending_request(client, citizen_headers, valid_pickup_payload)
    client.post(f"/collector/accept/{request['id']}", headers=collector_headers)
    client.post(f"/collector/start/{request['id']}", headers=collector_headers)
    client.post(f"/collector/collect/{request['id']}", headers=collector_headers)

    response = client.post(
        f"/collector/complete/{request['id']}",
        json={"weight_kg": 0},
        headers=collector_headers,
    )
    assert response.status_code == 422


def test_collector_summary_reflects_completed_jobs(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    request = _create_pending_request(client, citizen_headers, valid_pickup_payload)
    client.post(f"/collector/accept/{request['id']}", headers=collector_headers)
    client.post(f"/collector/start/{request['id']}", headers=collector_headers)
    client.post(f"/collector/collect/{request['id']}", headers=collector_headers)
    client.post(
        f"/collector/complete/{request['id']}", json={"weight_kg": 20.0}, headers=collector_headers
    )

    response = client.get("/collector/summary", headers=collector_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["completed_jobs"] == 1
    assert body["total_weight_kg"] == 20.0


def test_citizen_cannot_view_collector_summary(client, citizen_headers):
    response = client.get("/collector/summary", headers=citizen_headers)
    assert response.status_code == 403


# ─── Canonical /collector/pickups/* lifecycle ───────────────────────────────


def test_pickups_available_lists_unassigned_pending_requests(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    available_request = _create_pending_request(client, citizen_headers, valid_pickup_payload)
    assigned_request = _create_pending_request(client, citizen_headers, valid_pickup_payload)
    client.post(f"/collector/pickups/{assigned_request['id']}/accept", headers=collector_headers)

    response = client.get("/collector/pickups/available", headers=collector_headers)

    assert response.status_code == 200
    body = response.json()
    assert [item["id"] for item in body] == [available_request["id"]]
    assert body[0]["assignment"] is None


def test_pickups_assigned_lists_requests_accepted_by_collector(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    assigned_request = _create_pending_request(client, citizen_headers, valid_pickup_payload)
    client.post(f"/collector/pickups/{assigned_request['id']}/accept", headers=collector_headers)

    response = client.get("/collector/pickups/assigned", headers=collector_headers)

    assert response.status_code == 200
    body = response.json()
    assert [item["id"] for item in body] == [assigned_request["id"]]
    assert body[0]["status"] == "accepted"
    assert body[0]["assignment"]["collector_id"] is not None


def test_pickup_detail_includes_timeline_for_assigned_collector(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    request = _create_pending_request(client, citizen_headers, valid_pickup_payload)
    client.post(f"/collector/pickups/{request['id']}/accept", headers=collector_headers)

    response = client.get(f"/collector/pickups/{request['id']}", headers=collector_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == request["id"]
    assert body["status"] == "accepted"
    statuses = [event["status"] for event in body["timeline"]]
    assert statuses == ["pending", "accepted"]
    accepted_event = body["timeline"][1]
    assert accepted_event["actor_role"] == "collector"
    assert accepted_event["actor_name"]


def test_pickup_detail_allows_viewing_available_pending_request(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    request = _create_pending_request(client, citizen_headers, valid_pickup_payload)

    response = client.get(f"/collector/pickups/{request['id']}", headers=collector_headers)

    assert response.status_code == 200
    assert response.json()["status"] == "pending"


def test_pickup_detail_hidden_from_other_collectors(
    client, citizen_headers, collector_headers, make_user, auth_headers, valid_pickup_payload
):
    request = _create_pending_request(client, citizen_headers, valid_pickup_payload)
    client.post(f"/collector/pickups/{request['id']}/accept", headers=collector_headers)

    other_headers = auth_headers(
        make_user(role=UserRole.collector, email="other2@wasteiq.test", phone="9000077777")
    )

    response = client.get(f"/collector/pickups/{request['id']}", headers=other_headers)
    assert response.status_code == 403


def test_pickup_detail_nonexistent_returns_404(client, collector_headers):
    response = client.get("/collector/pickups/999999", headers=collector_headers)
    assert response.status_code == 404


def test_pickup_cancel_releases_request_back_to_available(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    request = _create_pending_request(client, citizen_headers, valid_pickup_payload)
    client.post(f"/collector/pickups/{request['id']}/accept", headers=collector_headers)

    response = client.post(f"/collector/pickups/{request['id']}/cancel", headers=collector_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "pending"
    assert body["assignment"] is None
    assert body["can_cancel"] is True

    available = client.get("/collector/pickups/available", headers=collector_headers).json()
    assert [item["id"] for item in available] == [request["id"]]

    detail = client.get(f"/collector/pickups/{request['id']}", headers=collector_headers).json()
    assert detail["timeline"][-1]["status"] == "pending"
    assert "available again" in detail["timeline"][-1]["note"]
    assert detail["timeline"][-1]["actor_role"] == "collector"


def test_pickup_cancel_only_allowed_before_trip_starts(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    request = _create_pending_request(client, citizen_headers, valid_pickup_payload)
    client.post(f"/collector/pickups/{request['id']}/accept", headers=collector_headers)
    client.post(f"/collector/pickups/{request['id']}/start", headers=collector_headers)

    response = client.post(f"/collector/pickups/{request['id']}/cancel", headers=collector_headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "Only accepted requests can be cancelled"


def test_pickup_cancel_unassigned_request_fails(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    request = _create_pending_request(client, citizen_headers, valid_pickup_payload)

    response = client.post(f"/collector/pickups/{request['id']}/cancel", headers=collector_headers)

    assert response.status_code == 403


def test_pickup_cancel_nonexistent_returns_404(client, collector_headers):
    response = client.post("/collector/pickups/999999/cancel", headers=collector_headers)
    assert response.status_code == 404


def test_pickup_cancel_by_other_collector_fails(
    client, citizen_headers, collector_headers, make_user, auth_headers, valid_pickup_payload
):
    request = _create_pending_request(client, citizen_headers, valid_pickup_payload)
    client.post(f"/collector/pickups/{request['id']}/accept", headers=collector_headers)

    other_headers = auth_headers(
        make_user(role=UserRole.collector, email="other3@wasteiq.test", phone="9000088888")
    )

    response = client.post(f"/collector/pickups/{request['id']}/cancel", headers=other_headers)
    assert response.status_code == 403


def test_pickup_full_lifecycle_via_canonical_routes(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    request = _create_pending_request(client, citizen_headers, valid_pickup_payload)

    accepted = client.post(f"/collector/pickups/{request['id']}/accept", headers=collector_headers)
    assert accepted.json()["status"] == "accepted"

    started = client.post(f"/collector/pickups/{request['id']}/start", headers=collector_headers)
    assert started.json()["status"] == "on_the_way"

    collected = client.post(
        f"/collector/pickups/{request['id']}/collect", headers=collector_headers
    )
    assert collected.json()["status"] == "collected"

    completed = client.post(
        f"/collector/pickups/{request['id']}/complete",
        json={"weight_kg": 12.0},
        headers=collector_headers,
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"
    assert completed.json()["assignment"]["weight_kg"] == 12.0

    detail = client.get(f"/collector/pickups/{request['id']}", headers=collector_headers).json()
    assert [event["status"] for event in detail["timeline"]] == [
        "pending",
        "accepted",
        "on_the_way",
        "collected",
        "completed",
    ]
