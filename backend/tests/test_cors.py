"""Tests for CORS configuration (WIQ-V1-CORS).

Verifies that:
- localhost:5173 is an allowed development origin.
- Unauthorized origins are not blindly allowed.
- Credentials behavior is correct (allow_credentials=True requires explicit origins).
- Preflight (OPTIONS) requests receive appropriate CORS headers.
- The /admin/analytics/pilot endpoint specifically receives CORS headers.
- Existing API behavior remains unchanged.
"""

import pytest

from app.core.config import settings


def _cors_headers(response) -> dict[str, str]:
    return {
        k.lower(): v for k, v in response.headers.items() if k.lower().startswith("access-control")
    }


def test_localhost_5173_is_allowed_origin_for_pilot_endpoint(client, admin_headers):
    response = client.get(
        "/admin/analytics/pilot",
        headers={"Origin": "http://localhost:5173", **admin_headers},
    )
    assert response.status_code == 200
    headers = _cors_headers(response)
    assert headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert headers.get("access-control-allow-credentials") == "true"


def test_localhost_5173_preflight_on_pilot_endpoint(client):
    response = client.options(
        "/admin/analytics/pilot",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert response.status_code == 200
    headers = _cors_headers(response)
    assert headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert headers.get("access-control-allow-credentials") == "true"
    assert "GET" in headers.get("access-control-allow-methods", "")
    assert "authorization" in headers.get("access-control-allow-headers", "")


def test_unauthorized_origin_not_allowed_on_pilot_endpoint(client, admin_headers):
    response = client.get(
        "/admin/analytics/pilot",
        headers={"Origin": "https://malicious-site.example.com", **admin_headers},
    )
    assert response.status_code == 200
    headers = _cors_headers(response)
    assert headers.get("access-control-allow-origin") not in (
        "https://malicious-site.example.com",
        "*",
    )


def test_cors_headers_present_on_all_admin_analytics_endpoints(client, admin_headers):
    endpoints = [
        "/admin/analytics/overview",
        "/admin/analytics/materials",
        "/admin/analytics/monthly",
        "/admin/analytics/collectors",
        "/admin/analytics/dealers",
        "/admin/analytics/carbon",
        "/admin/analytics/insights",
        "/admin/analytics/pilot",
    ]
    for endpoint in endpoints:
        response = client.get(
            endpoint,
            headers={"Origin": "http://localhost:5173", **admin_headers},
        )
        headers = _cors_headers(response)
        assert (
            headers.get("access-control-allow-origin") == "http://localhost:5173"
        ), f"Missing CORS header for {endpoint}"
        assert headers.get("access-control-allow-credentials") == "true"


def test_unauthenticated_cors_headers_on_public_endpoint(client):
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.status_code == 200
    headers = _cors_headers(response)
    assert headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert headers.get("access-control-allow-credentials") == "true"


def test_health_endpoint_reports_configured_cors_origins(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert "cors_origins" in body
    assert "http://localhost:5173" in body["cors_origins"]


def test_default_cors_origins_includes_localhost_5173():
    assert "http://localhost:5173" in settings.cors_origins_list


def test_wildcard_not_in_default_cors_origins():
    assert "*" not in settings.cors_origins_list


def test_vercel_origin_allowed_when_configured(client, admin_headers):
    if "https://waste-iq-zeta.vercel.app" not in settings.cors_origins_list:
        pytest.skip("Vercel origin not in CORS_ORIGINS configuration")
    response = client.get(
        "/admin/analytics/pilot",
        headers={"Origin": "https://waste-iq-zeta.vercel.app", **admin_headers},
    )
    assert response.status_code == 200
    headers = _cors_headers(response)
    assert headers.get("access-control-allow-origin") == "https://waste-iq-zeta.vercel.app"
    assert headers.get("access-control-allow-credentials") == "true"


def test_preflight_allows_correct_methods(client):
    response = client.options(
        "/admin/analytics/pilot",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    headers = _cors_headers(response)
    assert "POST" in headers.get("access-control-allow-methods", "")
    assert headers.get("access-control-max-age") == "600"
