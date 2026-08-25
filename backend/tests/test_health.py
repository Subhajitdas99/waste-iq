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
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "cloudinary_cloud_name", "test-cloud")
    monkeypatch.setattr(settings, "cloudinary_api_key", "test-key")
    monkeypatch.setattr(settings, "cloudinary_api_secret", "test-secret")

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_readiness_production_fails_without_cloudinary_configuration(
    client, db_session, monkeypatch
):
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "cloudinary_cloud_name", None)
    monkeypatch.setattr(settings, "cloudinary_api_key", None)
    monkeypatch.setattr(settings, "cloudinary_api_secret", None)

    response = client.get("/health/ready")

    assert response.status_code == 503

    body = response.json()
    assert body["status"] == "not_ready"
    assert body["reason"] == "cloudinary_not_configured"


def test_readiness_non_production_does_not_require_cloudinary(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "environment", "test")
    monkeypatch.setattr(settings, "cloudinary_cloud_name", None)
    monkeypatch.setattr(settings, "cloudinary_api_key", None)
    monkeypatch.setattr(settings, "cloudinary_api_secret", None)

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
