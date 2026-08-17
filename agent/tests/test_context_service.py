import pytest

from app.context.context_service import ContextService
from app.context.models import IndexRunSummary, SearchRequest, SearchResponse


@pytest.fixture
def service(tmp_path, clean_context_db):
    from app.db.session import SessionLocal
    from app.context.di import Container

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text(
        "def serve():\n    return 'running'\n\n# TODO: rate limit\n"
    )
    return ContextService(Container(SessionLocal, repository_root=tmp_path))


def test_reindex_returns_summary(service):
    summary = service.reindex()
    assert isinstance(summary, IndexRunSummary)
    assert summary.new_files == 1


def test_status_shape(service):
    status = service.status()
    assert set(status) >= {
        "indexed_files",
        "chunk_count",
        "embedding_count",
        "vector_count",
        "is_indexing",
    }
    assert status["indexed_files"] == 0


def test_search_returns_response(service):
    service.reindex()
    response = service.search(SearchRequest(query="serve", limit=5))
    assert isinstance(response, SearchResponse)
    assert response.total >= 1


def test_reset_clears_vector_index(service):
    service.reindex()
    assert service._container.vector_store.count() >= 1  # noqa: SLF001
    service.reindex(reset=True)
    assert service.status()["chunk_count"] >= 1  # sqlite chunks persist


def test_snapshot_returns_none_when_unavailable(service, monkeypatch):
    class FailingProvider:
        def fetch(self):
            return None

    service._container.snapshot_provider = FailingProvider()  # noqa: SLF001
    assert service.snapshot() is None


def test_snapshot_persists_payload(service, monkeypatch):
    class FakeProvider:
        def fetch(self):
            return '{"fetched_at": "2026-01-01T00:00:00Z", "latest_commit_sha": "abc"}'

    service._container.snapshot_provider = FakeProvider()  # noqa: SLF001
    data = service.snapshot()
    assert data["latest_commit_sha"] == "abc"
    assert (
        service._container.store().latest_snapshot()["latest_commit_sha"] == "abc"
    )  # noqa: SLF001
    status = service.status()
    assert status["repository_version"] == "abc"
