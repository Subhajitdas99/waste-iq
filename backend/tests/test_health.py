from app.core.config import settings


def test_health_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_shape(client):
    response = client.get("/health")
    body = response.json()
    assert body["status"] == "ok"
    assert "app" in body


def test_readiness_returns_200_when_database_is_available(client):
    response = client.get("/health/ready")

    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ready"
    assert "app" in body


def test_readiness_returns_503_when_database_is_unavailable(client, db_session, monkeypatch):
    def _raise_unavailable(*args, **kwargs):
        raise RuntimeError("database unreachable")

    monkeypatch.setattr(db_session, "execute", _raise_unavailable)

    response = client.get("/health/ready")

    assert response.status_code == 503

    body = response.json()
    assert body["status"] == "not_ready"
    assert "app" in body


def test_readiness_production_ready_when_cloudinary_configured(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "deployment_mode", "production")
    monkeypatch.setattr(settings, "cloudinary_cloud_name", "test-cloud")
    monkeypatch.setattr(settings, "cloudinary_api_key", "test-key")
    monkeypatch.setattr(settings, "cloudinary_api_secret", "test-secret")

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_readiness_production_fails_without_cloudinary_configuration(
    client, db_session, monkeypatch
):
    monkeypatch.setattr(settings, "deployment_mode", "production")
    monkeypatch.setattr(settings, "cloudinary_cloud_name", None)
    monkeypatch.setattr(settings, "cloudinary_api_key", None)
    monkeypatch.setattr(settings, "cloudinary_api_secret", None)

    response = client.get("/health/ready")

    assert response.status_code == 503

    body = response.json()
    assert body["status"] == "not_ready"
    assert body["reason"] == "cloudinary_not_configured"


def test_readiness_local_simulation_ready_when_fallback_enabled_and_no_cloudinary(
    client, db_session, monkeypatch
):
    """WIQ-V1-054: local simulation with fallback enabled and no Cloudinary."""
    monkeypatch.setattr(settings, "deployment_mode", "local-simulation")
    monkeypatch.setattr(settings, "cloudinary_cloud_name", None)
    monkeypatch.setattr(settings, "cloudinary_api_key", None)
    monkeypatch.setattr(settings, "cloudinary_api_secret", None)
    monkeypatch.setattr(settings, "local_image_storage_enabled", True)

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_readiness_production_never_ready_with_fallback_and_no_cloudinary(
    client, db_session, monkeypatch
):
    """Security boundary: production + fallback + no Cloudinary MUST NOT be ready."""
    monkeypatch.setattr(settings, "deployment_mode", "production")
    monkeypatch.setattr(settings, "cloudinary_cloud_name", None)
    monkeypatch.setattr(settings, "cloudinary_api_key", None)
    monkeypatch.setattr(settings, "cloudinary_api_secret", None)
    monkeypatch.setattr(settings, "local_image_storage_enabled", True)

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["reason"] == "cloudinary_not_configured"


def test_readiness_production_uses_cloudinary_when_configured(client, db_session, monkeypatch):
    """Even with the fallback flag set, Cloudinary is used and readiness passes."""
    monkeypatch.setattr(settings, "deployment_mode", "production")
    monkeypatch.setattr(settings, "cloudinary_cloud_name", "demo-cloud")
    monkeypatch.setattr(settings, "cloudinary_api_key", "demo-key")
    monkeypatch.setattr(settings, "cloudinary_api_secret", "demo-secret")
    monkeypatch.setattr(settings, "local_image_storage_enabled", True)

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_readiness_production_fallback_false_without_cloudinary(client, db_session, monkeypatch):
    """Production with fallback disabled and no Cloudinary: not ready."""
    monkeypatch.setattr(settings, "deployment_mode", "production")
    monkeypatch.setattr(settings, "cloudinary_cloud_name", None)
    monkeypatch.setattr(settings, "cloudinary_api_key", None)
    monkeypatch.setattr(settings, "cloudinary_api_secret", None)
    monkeypatch.setattr(settings, "local_image_storage_enabled", False)

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["reason"] == "cloudinary_not_configured"


def test_readiness_development_always_ready(client, db_session, monkeypatch):
    """Development mode never requires Cloudinary."""
    monkeypatch.setattr(settings, "deployment_mode", "development")
    monkeypatch.setattr(settings, "cloudinary_cloud_name", None)
    monkeypatch.setattr(settings, "cloudinary_api_key", None)
    monkeypatch.setattr(settings, "cloudinary_api_secret", None)

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_readiness_development_unaffected_by_local_fallback(client, db_session, monkeypatch):
    """Development is unaffected by the fallback flag."""
    monkeypatch.setattr(settings, "deployment_mode", "development")
    monkeypatch.setattr(settings, "cloudinary_cloud_name", None)
    monkeypatch.setattr(settings, "cloudinary_api_key", None)
    monkeypatch.setattr(settings, "cloudinary_api_secret", None)
    monkeypatch.setattr(settings, "local_image_storage_enabled", True)

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
