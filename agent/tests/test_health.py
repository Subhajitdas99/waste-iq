def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["environment"] == "test"
    assert "app" in data


def test_admin_requires_auth(client):
    response = client.get("/api/admin/runs")
    assert response.status_code == 401


def test_admin_accepts_bearer_token(client):
    response = client.get("/api/admin/runs", headers={"Authorization": "Bearer test-admin-token"})
    assert response.status_code == 200
    assert "runs" in response.json()
