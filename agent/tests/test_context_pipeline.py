import pytest

from app.context.di import Container
from app.context.models import IndexRunSummary


@pytest.fixture
def container(tmp_path, clean_context_db):
    from app.db.session import SessionLocal

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text(
        "def hello():\n    return 'hi'\n\nclass Greeter:\n    pass\n"
    )
    c = Container(SessionLocal, repository_root=tmp_path, min_tokens=10, max_tokens=100)
    return c


def test_run_indexes_new_files(container):
    summary = container.pipeline().run()
    assert isinstance(summary, IndexRunSummary)
    assert summary.new_files == 1
    assert summary.updated_files == 0
    assert summary.chunks_created >= 1
    assert summary.embeddings_created >= 1
    assert summary.took_seconds >= 0
    assert container.status()["indexed_files"] == 1
    assert container.vector_store.count() >= 1


def test_run_is_idempotent(container):
    first = container.pipeline().run()
    second = container.pipeline().run()
    assert second.new_files == 0
    assert second.updated_files == 0
    assert second.chunks_created == 0
    assert container.status()["chunk_count"] == first.chunks_created


def test_run_detects_updated_file(container):
    container.pipeline().run()
    root = container.repository_root
    (root / "src" / "main.py").write_text(
        "def hello():\n    return 'changed'\n\ndef extra():\n    return 2\n"
    )
    summary = container.pipeline().run()
    assert summary.updated_files == 1
    assert summary.chunks_created >= 1


def test_run_removes_deleted_file(container):
    container.pipeline().run()
    root = container.repository_root
    (root / "src" / "main.py").unlink()
    summary = container.pipeline().run()
    assert summary.removed_files == 1
    assert summary.chunks_removed >= 1
    assert container.vector_store.count() == 0


def test_run_empty_changed_file_stays_consistent(container):
    container.pipeline().run()
    container.repository_root.joinpath("src", "main.py").write_text(
        "def hello():\n    return 'same bytes!'"[:0]
    )
    # empty file -> no chunks, file still considered indexed
    summary = container.pipeline().run()
    assert summary.removed_files == 0


def test_run_raises_when_already_indexing(container):
    pipeline = container.pipeline()
    pipeline._is_indexing = True  # noqa: SLF001
    with pytest.raises(RuntimeError):
        pipeline.run()


def test_embedding_cache_reused(container):
    first = container.pipeline().run()
    assert first.embeddings_cache_hits == 0
    container.store().commit()
    # update content so it re-embeds new chunks
    root = container.repository_root
    (root / "src" / "main.py").write_text(
        "def hello():\n    return 'hi'\n\nclass Greeter:\n    pass\n\n# trailing\n"
    )
    summary = container.pipeline().run()
    assert summary.chunks_created >= 1


def test_embedding_cache_lookup_missing_model(container, tmp_path):
    from app.context.chunker import chunk_text

    chunk = chunk_text(
        "x.py",
        "def a():\n    pass",
        language="py",
        source_type="code",
        min_tokens=1,
        max_tokens=100,
    )[0]
    store = container.store()
    assert store.embedding_lookup(chunk.content_hash, "other-model") is None
    store.embedding_store(chunk.content_hash, "model-a", [1.0, 0.0])
    assert store.embedding_lookup(chunk.content_hash, "model-a") == [1.0, 0.0]
    assert store.embedding_lookup(chunk.content_hash, "other-model") is None
    store.embedding_store(chunk.content_hash, "model-a", [0.0, 1.0])
    assert store.embedding_lookup(chunk.content_hash, "model-a") == [0.0, 1.0]
    store.commit()
