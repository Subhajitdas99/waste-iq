"""API tests for Phase 2.6 debug/introspection endpoints."""

import pytest


def _seed_repo(tmp_path):
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "dealer_approval.py").write_text(
        "class AdminDealerApprovalService:\n"
        "    def approve_dealer(self, db, dealer_user_id):\n"
        "        return True\n"
    )
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "readme.md").write_text("# Dealer approval flow\n")


@pytest.fixture
def debug_container(client, tmp_path, clean_context_db, monkeypatch):
    """Wire the API to a fresh container over the seeded tmp repo."""
    from app.api import dependencies
    from app.context.di import Container
    from app.db.session import SessionLocal

    _seed_repo(tmp_path)
    container = Container(SessionLocal, repository_root=tmp_path, min_tokens=10, max_tokens=200)
    dependencies._container = container  # noqa: SLF001
    dependencies._pipeline = None  # noqa: SLF001
    dependencies._search = None  # noqa: SLF001
    monkeypatch.setattr(dependencies, "get_container", lambda: container)
    client.post("/api/context/reindex")
    return container


def test_debug_index_endpoint(client, debug_container):
    response = client.get("/api/context/debug/index")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 2
    assert body["chunk_count"] >= 1
    assert body["vector_count"] == body["chunk_count"]
    paths = {f["path"] for f in body["files"]}
    assert "app/dealer_approval.py" in paths


def test_debug_chunks_endpoint(client, debug_container):
    response = client.get("/api/context/debug/chunks", params={"path": "app/dealer_approval.py"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    chunk = body["chunks"][0]
    assert chunk["file_path"] == "app/dealer_approval.py"
    assert chunk["start_line"] >= 1
    assert "content_preview" in chunk
    assert "dealer" in chunk["content_preview"].lower()


def test_debug_vectors_endpoint(client, debug_container):
    response = client.get("/api/context/debug/vectors")
    assert response.status_code == 200
    body = response.json()
    assert body["index_health"] == "ok"
    assert body["vector_count"] == body["chunk_count"]
    assert body["vector_count"] >= 1
    sample = body["sample"]
    assert sample
    assert sample[0]["dimension"] > 0
    assert "first_dims" in sample[0]


def test_debug_embeddings_endpoint(client, debug_container):
    response = client.get(
        "/api/context/debug/embeddings", params={"path": "app/dealer_approval.py"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total_chunks"] >= 1
    assert body["cache_hits"] == body["total_chunks"]
    assert body["dimension"] == 384
    assert body["entries"][0]["cached"] is True


def test_debug_search_endpoint_returns_scoring_breakdown(client, debug_container):
    response = client.post(
        "/api/context/debug/search",
        json={"query": "dealer approval", "limit": 5},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "dealer approval"
    assert "dealer" in body["tokens"]
    assert body["corpus_size"] >= 2
    assert "document_frequency" in body
    assert "inverse_document_frequency" in body
    assert body["total_candidates"] >= 1
    top = body["candidates"][0]
    for key in (
        "chunk_id",
        "path",
        "keyword_score",
        "keyword_normalized",
        "path_bonus",
        "vector_score",
        "vector_normalized",
        "fused_score",
    ):
        assert key in top
    assert "dealer_approval" in top["path"]
