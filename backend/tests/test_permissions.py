import pytest

ADMIN_ROUTES = [
    ("GET", "/admin/material-categories"),
    ("GET", "/admin/pricing-rules"),
    ("GET", "/admin/eligible-pickups"),
    ("GET", "/admin/inventory-lots"),
]

DEALER_ROUTES = [
    ("GET", "/dealer/inventory-lots"),
]


# ─── Citizen cannot access admin ──────────────────────────────────────────────


@pytest.mark.parametrize("method,path", ADMIN_ROUTES)
def test_citizen_cannot_access_admin_routes(client, citizen_headers, method, path):
    response = client.request(method, path, headers=citizen_headers)
    assert response.status_code == 403


# ─── Dealer cannot access admin ───────────────────────────────────────────────


@pytest.mark.parametrize("method,path", ADMIN_ROUTES)
def test_dealer_cannot_access_admin_routes(client, dealer_headers, method, path):
    response = client.request(method, path, headers=dealer_headers)
    assert response.status_code == 403


# ─── Collector cannot access admin ────────────────────────────────────────────


@pytest.mark.parametrize("method,path", ADMIN_ROUTES)
def test_collector_cannot_access_admin_routes(client, collector_headers, method, path):
    response = client.request(method, path, headers=collector_headers)
    assert response.status_code == 403


# ─── Collector cannot access dealer ───────────────────────────────────────────


@pytest.mark.parametrize("method,path", DEALER_ROUTES)
def test_collector_cannot_access_dealer_routes(client, collector_headers, method, path):
    response = client.request(method, path, headers=collector_headers)
    assert response.status_code == 403


def test_collector_cannot_create_dealer_profile(client, collector_headers):
    response = client.post(
        "/dealer/profile",
        json={
            "business_name": "Should Fail",
            "owner_name": "X",
            "phone": "9000000000",
            "address": "Some address here",
            "city": "Kolkata",
            "pincode": "700001",
            "materials_accepted": ["PET"],
        },
        headers=collector_headers,
    )
    assert response.status_code == 403


# ─── Citizen cannot access dealer or collector routes ────────────────────────


def test_citizen_cannot_access_collector_summary(client, citizen_headers):
    response = client.get("/collector/summary", headers=citizen_headers)
    assert response.status_code == 403


def test_citizen_cannot_access_dealer_inventory(client, citizen_headers):
    response = client.get("/dealer/inventory-lots", headers=citizen_headers)
    assert response.status_code == 403


def test_dealer_cannot_access_collector_routes(client, dealer_headers):
    response = client.get("/collector/summary", headers=dealer_headers)
    assert response.status_code == 403


# ─── Anonymous requests ────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "method,path",
    ADMIN_ROUTES + DEALER_ROUTES + [("GET", "/collector/summary"), ("GET", "/auth/me"), ("GET", "/pickup-requests")],
)
def test_anonymous_requests_rejected_with_401(client, method, path):
    response = client.request(method, path)
    assert response.status_code == 401


def test_anonymous_cannot_create_pickup_request(client):
    response = client.post(
        "/pickup-requests",
        json={
            "waste_type": "Plastic",
            "address": "Some address, Kolkata, 700001",
            "latitude": 22.5,
            "longitude": 88.3,
        },
    )
    assert response.status_code == 401


def test_malformed_bearer_token_rejected(client):
    response = client.get("/auth/me", headers={"Authorization": "NotBearer sometoken"})
    assert response.status_code == 401


def test_health_endpoint_does_not_require_auth(client):
    """Sanity check: health must remain public even though everything else is locked down."""
    response = client.get("/health")
    assert response.status_code == 200