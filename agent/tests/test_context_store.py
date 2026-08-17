import pytest

from app.context.chunk_store import SqlChunkStore, _from_record, _to_record
from app.context.chunker import chunk_text
from app.db.repositories import (
    ChunkRepository,
    EmbeddingCacheRepository,
    IndexedFileRepository,
    SnapshotRepository,
)
from app.db.models import IndexedFile
from app.db.session import SessionLocal


@pytest.fixture
def session(clean_context_db):
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def chunk():
    return chunk_text(
        "a.py",
        "def foo():\n    return 1\n",
        language="py",
        source_type="code",
        min_tokens=1,
        max_tokens=100,
    )[0]


def test_indexed_file_repo_upsert_and_get(session, chunk):
    repo = IndexedFileRepository(session)
    record = IndexedFile(path="a.py", language="py", size=1, modified_at=0.0, checksum="c1")
    repo.upsert(record)
    loaded = repo.get("a.py")
    assert loaded is not None
    assert loaded.checksum == "c1"
    # upsert updates
    record2 = IndexedFile(path="a.py", language="py", size=2, modified_at=1.0, checksum="c2")
    repo.upsert(record2)
    assert repo.get("a.py").checksum == "c2"
    assert repo.all_paths() == {"a.py"}
    assert repo.count() == 1


def test_indexed_file_repo_delete(session):
    repo = IndexedFileRepository(session)
    repo.upsert(IndexedFile(path="x.py", language="py", size=1, modified_at=0, checksum="c"))
    assert repo.delete("x.py") is True
    assert repo.delete("x.py") is False
    assert repo.count() == 0


def test_chunk_repo_upsert_dedupe_and_lookup(session, chunk):
    repo = ChunkRepository(session)
    repo.upsert(_to_record(chunk))
    found = repo.find_by_indices([chunk.chunk_id])
    assert chunk.chunk_id in found
    # re-upsert updates content instead of duplicating
    changed = chunk.model_copy(update={"content": "def foo():\n    pass\n"})
    repo.upsert(_to_record(changed))
    assert repo.count() == 1
    assert repo.find_by_indices([chunk.chunk_id])[chunk.chunk_id].content != chunk.content
    assert repo.for_file("a.py")[0].file_path == "a.py"


def test_chunk_repo_delete_for_files(session, chunk):
    repo = ChunkRepository(session)
    repo.upsert(_to_record(chunk))
    removed = repo.delete_for_files(["a.py"])
    assert removed == [chunk.chunk_id]
    assert repo.delete_for_files(["nope.py"]) == []
    assert repo.count() == 0


def test_embedding_cache_repo(session):
    repo = EmbeddingCacheRepository(session)
    assert repo.get("hash-1", "model-a") is None
    repo.set("hash-1", "model-a", [1.0, 2.0])
    assert repo.get("hash-1", "model-a") == [1.0, 2.0]
    assert repo.get("hash-1", "model-b") is None
    repo.set("hash-1", "model-a", [9.0, 9.0])
    assert repo.get("hash-1", "model-a") == [9.0, 9.0]
    assert repo.count() == 1


def test_snapshot_repo_save_and_latest(session):
    repo = SnapshotRepository(session)
    assert repo.latest() is None
    repo.save({"fetched_at": "2026-01-01T00:00:00", "x": 1})
    repo.save({"fetched_at": "2026-01-02T00:00:00", "x": 2})
    latest = repo.latest()
    assert latest["x"] == 2


def test_to_from_record_roundtrip(session, chunk):
    record = _to_record(chunk)
    loaded = _from_record(record)
    assert loaded.chunk_id == chunk.chunk_id
    assert loaded.source_type == "code"


def test_sql_chunk_store_full_surface(session, chunk):
    store = SqlChunkStore(session)
    # embedding lookup/store
    store.embedding_store(chunk.content_hash, "model-a", [0.5, 0.5])
    assert store.embedding_lookup(chunk.content_hash, "model-a") == [0.5, 0.5]
    store.embedding_store(chunk.content_hash, "model-a", [1.0, 0.0])
    store.commit()
    assert store.embedding_count() == 1
    assert store.embedding_lookup(chunk.content_hash, "other") is None
    # chunks
    store.upsert_chunk(chunk)
    store.record_file(chunk)
    store.commit()
    assert store.get_existing([chunk.chunk_id])[chunk.chunk_id].chunk_id == chunk.chunk_id
    assert len(store.get_chunks_for_file("a.py")) >= 1
    assert store.get_chunks_for_file("missing.py") == []
    # files
    store.mark_indexed("a.py", "py", 10, 1.0, "c1")
    store.commit()
    assert store.indexed_files() == {"a.py"}
    assert store.indexed_file_count() == 1
    assert store.latest_indexed_at() is not None
    # deleted chunks surfaced
    store.delete_chunks_for_files(["a.py"])
    store.remove_file("a.py")
    store.commit()
    assert store.indexed_file_count() == 0
    assert store.chunk_count() == 0


def test_sql_chunk_store_delete_returns_ids(session, chunk):
    store = SqlChunkStore(session)
    store.upsert_chunk(chunk)
    store.commit()
    removed = store.delete_chunks_for_files(["a.py"])
    assert removed == [chunk.chunk_id]
    assert store.delete_chunks_for_files([]) == []


def test_sql_chunk_store_snapshots(session):
    store = SqlChunkStore(session)
    store.save_snapshot({"fetched_at": "x", "y": 1})
    store.commit()
    assert store.latest_snapshot() == {"fetched_at": "x", "y": 1}


def test_sql_chunk_store_counts(session, chunk):
    store = SqlChunkStore(session)
    assert store.indexed_file_count() == 0
    assert store.chunk_count() == 0
    assert store.embedding_count() == 0
    store.upsert_chunk(chunk)
    store.commit()
    assert store.chunk_count() == 1
