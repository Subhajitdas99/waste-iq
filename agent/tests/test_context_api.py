def test_status_endpoint(client, clean_context_db):
    response = client.get("/api/context/status")
    assert response.status_code == 200
    body = response.json()
    assert "indexed_files" in body
    assert "chunk_count" in body
    assert "is_indexing" in body


def test_reindex_endpoint_returns_summary(client, clean_context_db):
    response = client.post("/api/context/reindex")
    assert response.status_code == 200
    body = response.json()
    assert body["new_files"] >= 1
    assert "took_seconds" in body


def test_reindex_with_reset_flag(client, clean_context_db):
    client.post("/api/context/reindex")
    response = client.post("/api/context/reindex?reset=true")
    assert response.status_code == 200
    body = response.json()
    assert "chunks_created" in body


def test_search_endpoint_returns_results(client, clean_context_db):
    client.post("/api/context/reindex")
    response = client.post(
        "/api/context/search",
        json={"query": "add", "limit": 3},
    )
    assert response.status_code == 200
    body = response.json()
    assert "results" in body
    assert body["total"] >= 0
    for result in body["results"]:
        assert "path" in result
        assert "score" in result


def test_search_endpoint_rejects_bad_limit(client):
    response = client.post(
        "/api/context/search",
        json={"query": "add", "limit": 0},
    )
    assert response.status_code == 422


def test_search_endpoint_filters(client, clean_context_db):
    client.post("/api/context/reindex")
    response = client.post(
        "/api/context/search",
        json={"query": "add", "limit": 5, "languages": ["py"]},
    )
    assert response.status_code == 200
    assert all(r["language"] == "py" for r in response.json()["results"])


def test_snapshot_endpoint(client, clean_context_db):
    response = client.post("/api/context/snapshot")
    assert response.status_code == 200
    body = response.json()
    assert body is None or isinstance(body, dict)


def test_health_endpoint_unchanged(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
