import pytest

from app.context.di import Container
from app.context.embeddings import HashEmbeddingProvider
from app.context.vector_store import InMemoryVectorStore


@pytest.fixture
def container(tmp_path, clean_context_db):
    from app.db.session import SessionLocal

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def main():\n    return 0\n")
    return Container(SessionLocal, repository_root=tmp_path)


def test_container_defaults_wired(container):
    assert isinstance(container.embedder, HashEmbeddingProvider)
    assert isinstance(container.vector_store, InMemoryVectorStore)
    assert container.snapshot_provider is not None
    assert container.repository_root == container.indexer().root
    assert container.status()["indexed_files"] == 0


def test_container_settings_fallback(tmp_path, monkeypatch):
    from app.db.session import SessionLocal

    monkeypatch.setattr("app.context.di.settings.agent_repository_root", tmp_path)
    c = Container(SessionLocal, repository_root=None)
    assert c.repository_root == tmp_path


def test_container_ignores_and_tokens_overrides(tmp_path):
    from app.db.session import SessionLocal

    (tmp_path / "ignored_dir").mkdir()
    (tmp_path / "ignored_dir" / "x.py").write_text("x = 1\n")
    c = Container(
        SessionLocal,
        repository_root=tmp_path,
        ignored_dirs=["ignored_dir"],
        min_tokens=5,
        max_tokens=50,
    )
    indexer = c.indexer()
    assert indexer._min_tokens == 5  # noqa: SLF001
    assert indexer._max_tokens == 50  # noqa: SLF001
    assert indexer.iter_files() == []


def test_vector_store_swap_invalidates_cached_services(container):
    pipeline = container.pipeline()
    search = container.search_service()
    container.vector_store = InMemoryVectorStore()
    assert container.pipeline() is not pipeline
    assert container.search_service() is not search


def test_embedder_swap_invalidates_cached_services(container):
    pipeline = container.pipeline()
    container.embedder = HashEmbeddingProvider()
    assert container.pipeline() is not pipeline


def test_snapshot_provider_swap(container):
    class FakeProvider:
        def fetch(self):
            return None

    container.snapshot_provider = FakeProvider()
    assert container.snapshot_provider.fetch() is None


def test_pipeline_returns_same_instance(container):
    assert container.pipeline() is container.pipeline()


def test_status_after_index(container):
    container.pipeline().run()
    status = container.status()
    assert status["indexed_files"] == 1
    assert status["chunk_count"] >= 1
    assert status["vector_count"] >= 1
    assert status["is_indexing"] is False
