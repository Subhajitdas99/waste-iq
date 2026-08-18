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
