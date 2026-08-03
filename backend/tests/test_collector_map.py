from app.repositories.collector_locations import CollectorLocationRepository
from app.services.location import estimate_travel_time_minutes, nearest_search
from app.services.routing import MultiStopRoute, RoutePoint, RouteStop, optimize_route


def _create_pending_request(client, citizen_headers, payload):
    return client.post("/pickup-requests", data=payload, headers=citizen_headers).json()


def _report_location(client, collector_headers, latitude, longitude, accuracy=None):
    body = {"latitude": latitude, "longitude": longitude}
    if accuracy is not None:
        body["accuracy"] = accuracy
    return client.post("/collector/location", json=body, headers=collector_headers)


def _complete_pickup(client, collector_headers, pickup_id):
    client.post(f"/collector/accept/{pickup_id}", headers=collector_headers)
    client.post(f"/collector/start/{pickup_id}", headers=collector_headers)
    client.post(f"/collector/collect/{pickup_id}", headers=collector_headers)
    return client.post(
        f"/collector/complete/{pickup_id}", json={"weight_kg": 6.5}, headers=collector_headers
    )


# ─── Location updates ────────────────────────────────────────────────────────


def test_updates_collector_location_and_records_history(
    client, db_session, collector_headers, collector_user
):
    response = _report_location(client, collector_headers, 22.5726, 88.3639, accuracy=12)

    assert response.status_code == 200
    body = response.json()
    assert body["latitude"] == 22.5726
    assert body["longitude"] == 88.3639
    assert body["accuracy"] == 12
    assert body["updated_at"]

    fetched = client.get("/collector/location", headers=collector_headers)
    assert fetched.status_code == 200
    assert fetched.json()["latitude"] == 22.5726

    repository = CollectorLocationRepository()
    history = repository.list_history(db_session, collector_user.id)
    assert len(history) == 1
    assert history[0].latitude == 22.5726
    assert history[0].longitude == 88.3639


def test_post_location_upserts_latest_and_appends_history(
    db_session, client, collector_headers, collector_user
):
    _report_location(client, collector_headers, 22.5726, 88.3639)
    response = _report_location(client, collector_headers, 22.5730, 88.3640, accuracy=5)

    assert response.status_code == 200
    assert response.json()["latitude"] == 22.5730

    latest = client.get("/collector/location", headers=collector_headers)
    assert latest.json()["longitude"] == 88.3640

    repository = CollectorLocationRepository()
    assert len(repository.list_history(db_session, collector_user.id)) == 2


def test_get_location_returns_404_when_never_reported(client, collector_headers):
    response = client.get("/collector/location", headers=collector_headers)

    assert response.status_code == 404
    assert "not been reported" in response.json()["detail"].lower()


def test_post_location_requires_collector_role(client, citizen_headers, dealer_headers):
    payload = {"latitude": 22.5726, "longitude": 88.3639}

    citizen_response = client.post("/collector/location", json=payload, headers=citizen_headers)
    dealer_response = client.post("/collector/location", json=payload, headers=dealer_headers)

    assert citizen_response.status_code == 403
    assert dealer_response.status_code == 403


def test_get_location_requires_collector_role(client, citizen_headers):
    response = client.get("/collector/location", headers=citizen_headers)

    assert response.status_code == 403


# ─── Map payload ─────────────────────────────────────────────────────────────


def test_collector_map_returns_markers_by_status(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    _report_location(client, collector_headers, 22.5726, 88.3639)

    pending = _create_pending_request(client, citizen_headers, valid_pickup_payload)
    accepted = _create_pending_request(client, citizen_headers, valid_pickup_payload)
    completed = _create_pending_request(client, citizen_headers, valid_pickup_payload)

    client.post(f"/collector/accept/{accepted['id']}", headers=collector_headers)
    _complete_pickup(client, collector_headers, completed["id"])

    response = client.get("/collector/map", headers=collector_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["collector"]["latitude"] == 22.5726
    assert body["radius_km"] == 5

    markers = {item["id"]: item for item in body["pickups"]}
    assert markers[pending["id"]]["status"] == "pending"
    assert markers[accepted["id"]]["status"] == "accepted"
    assert markers[completed["id"]]["status"] == "completed"
    assert markers[pending["id"]]["distance_km"] == 0
    assert markers[pending["id"]]["eta_minutes"] == 0

    route_stop_ids = {stop["pickup_id"] for stop in body["route"]["stops"]}
    assert route_stop_ids == {accepted["id"]}
    assert body["route"]["total_distance_km"] == 0
    assert body["route"]["total_duration_minutes"] == 0


def test_collector_map_sorts_nearby_pickups_by_distance(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    _report_location(client, collector_headers, 22.5726, 88.3639)

    nearer = _create_pending_request(client, citizen_headers, valid_pickup_payload)
    farther_payload = {
        **valid_pickup_payload,
        "address": "22 Park Street, Kolkata, 700016",
        "latitude": 22.5540,
        "longitude": 88.3510,
    }
    farther = _create_pending_request(client, citizen_headers, farther_payload)

    response = client.get("/collector/map", headers=collector_headers)

    assert response.status_code == 200
    nearby_ids = [item["id"] for item in response.json()["nearby_pickups"]]
    assert nearby_ids == [nearer["id"], farther["id"]]


def test_collector_map_without_location_returns_empty(client, collector_headers):
    response = client.get("/collector/map", headers=collector_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["collector"] is None
    assert body["pickups"] == []
    assert body["route"] is None
    assert body["nearby_pickups"] == []


def test_collector_map_blocks_other_roles(client, dealer_headers):
    response = client.get("/collector/map", headers=dealer_headers)

    assert response.status_code == 403


# ─── Route generation ────────────────────────────────────────────────────────


def test_collector_route_orders_active_stops_nearest_first(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    _report_location(client, collector_headers, 22.5726, 88.3639)

    far_payload = {
        **valid_pickup_payload,
        "address": "22 Far Park Street, Kolkata, 700016",
        "latitude": 22.5540,
        "longitude": 88.3510,
    }
    far_request = _create_pending_request(client, citizen_headers, far_payload)
    near_payload = {
        **valid_pickup_payload,
        "address": "14 Lake Road, Kolkata, 700029",
        "latitude": 22.5727,
        "longitude": 88.3640,
    }
    near_request = _create_pending_request(client, citizen_headers, near_payload)

    client.post(f"/collector/accept/{far_request['id']}", headers=collector_headers)
    client.post(f"/collector/accept/{near_request['id']}", headers=collector_headers)

    response = client.get("/collector/route", headers=collector_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["origin_latitude"] == 22.5726
    assert body["origin_longitude"] == 88.3639

    stops = body["stops"]
    assert [stop["pickup_id"] for stop in stops] == [near_request["id"], far_request["id"]]
    assert stops[0]["order"] == 1
    assert stops[0]["eta_minutes"] >= 1
    assert body["total_distance_km"] > 0
    assert body["total_duration_minutes"] > 0
    assert stops[1]["distance_from_previous_km"] > 0


def test_collector_route_empty_without_active_pickups(client, collector_headers):
    response = client.get("/collector/route", headers=collector_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["stops"] == []
    assert body["total_distance_km"] == 0
    assert body["total_duration_minutes"] == 0


# ─── Nearby pickups ──────────────────────────────────────────────────────────


def test_nearby_pickups_use_stored_location(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    _report_location(client, collector_headers, 22.5726, 88.3639)
    request = _create_pending_request(client, citizen_headers, valid_pickup_payload)

    response = client.get("/collector/nearby-pickups", headers=collector_headers)

    assert response.status_code == 200
    body = response.json()
    assert [item["id"] for item in body] == [request["id"]]
    assert body[0]["distance_km"] == 0


def test_nearby_pickups_accept_latitude_and_longitude(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    request = _create_pending_request(client, citizen_headers, valid_pickup_payload)

    response = client.get(
        "/collector/nearby-pickups",
        params={"latitude": 22.5726, "longitude": 88.3639, "radius_km": 2},
        headers=collector_headers,
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [request["id"]]


def test_nearby_pickups_requires_a_location(client, collector_headers):
    response = client.get("/collector/nearby-pickups", headers=collector_headers)

    assert response.status_code == 400


def test_nearby_pickups_rejects_only_one_coordinate(client, collector_headers):
    response = client.get(
        "/collector/nearby-pickups",
        params={"latitude": 22.5726},
        headers=collector_headers,
    )

    assert response.status_code == 400


# ─── Navigation ──────────────────────────────────────────────────────────────


def test_navigation_to_assigned_pickup(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    _report_location(client, collector_headers, 22.5726, 88.3639)
    request = _create_pending_request(client, citizen_headers, valid_pickup_payload)
    client.post(f"/collector/accept/{request['id']}", headers=collector_headers)

    response = client.get(f"/collector/navigation/{request['id']}", headers=collector_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["pickup"]["id"] == request["id"]
    assert body["distance_km"] == 0
    assert body["duration_minutes"] == 0
    assert body["origin_latitude"] == 22.5726
    assert body["geometry"] == [
        {"latitude": 22.5726, "longitude": 88.3639},
        {"latitude": 22.5726, "longitude": 88.3639},
    ]


def test_navigation_to_pending_pickup(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    _report_location(client, collector_headers, 22.5726, 88.3639)
    request = _create_pending_request(client, citizen_headers, valid_pickup_payload)

    response = client.get(f"/collector/navigation/{request['id']}", headers=collector_headers)

    assert response.status_code == 200


def test_navigation_requires_collector_location(
    client, citizen_headers, collector_headers, valid_pickup_payload
):
    request = _create_pending_request(client, citizen_headers, valid_pickup_payload)

    response = client.get(f"/collector/navigation/{request['id']}", headers=collector_headers)

    assert response.status_code == 409


def test_navigation_missing_pickup_returns_404(client, collector_headers):
    _report_location(client, collector_headers, 22.5726, 88.3639)

    response = client.get("/collector/navigation/999999", headers=collector_headers)

    assert response.status_code == 404


# ─── Geo helper unit tests ───────────────────────────────────────────────────


def test_estimate_travel_time_minutes_rounds_and_clamps_to_one():
    assert estimate_travel_time_minutes(0) == 0
    assert estimate_travel_time_minutes(2.46, average_speed_kmph=30) == 5
    assert estimate_travel_time_minutes(0.01, average_speed_kmph=100) == 1
    assert estimate_travel_time_minutes(30, average_speed_kmph=60) == 30


def test_nearest_search_orders_candidates_nearest_first():
    scored = nearest_search(
        22.5726,
        88.3639,
        [(22.5540, 88.3510), (22.5727, 88.3640), (28.6139, 77.2090)],
    )

    assert [index for index, _ in scored] == [1, 0, 2]
    assert scored[0][1] < scored[1][1] < scored[2][1]


def test_nearest_search_filters_by_radius():
    scored = nearest_search(
        22.5726,
        88.3639,
        [(22.5727, 88.3640), (28.6139, 77.2090)],
        radius_km=2,
    )

    assert len(scored) == 1
    assert scored[0][0] == 0


def test_optimize_route_orders_stops_nearest_and_totals():
    origin = RoutePoint(latitude=22.5726, longitude=88.3639)
    stops = [
        RouteStop(pickup_id=1, latitude=22.5540, longitude=88.3510),
        RouteStop(pickup_id=2, latitude=22.5727, longitude=88.3640),
    ]

    route = optimize_route(origin, stops)

    assert isinstance(route, MultiStopRoute)
    assert [stop.pickup_id for stop in route.stops] == [2, 1]
    assert route.stops[0].pickup_id == 2
    assert route.distance_km > 0
    assert route.duration_minutes > 0
    assert route.stops[1].pickup_id == 1


def test_optimize_route_empty_stops():
    route = optimize_route(RoutePoint(latitude=22.5726, longitude=88.3639), [])

    assert route.stops == ()
    assert route.distance_km == 0
    assert route.duration_minutes == 0
