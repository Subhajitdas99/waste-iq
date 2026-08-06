"""SQLAlchemy repositories for the Repository Context Service.

Sessions are injected — repositories never create their own connections,
and business logic never instantiates repositories directly (see app/context/di.py).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    ChunkRecord,
    EmbeddingCacheEntry,
    IndexedFile,
    RepositorySnapshotEntry,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class IndexedFileRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, path: str) -> IndexedFile | None:
        return self._session.get(IndexedFile, path)

    def upsert(self, record: IndexedFile) -> IndexedFile:
        existing = self._session.get(IndexedFile, record.path)
        if existing is None:
            self._session.add(record)
            self._session.flush()
            return record
        existing.language = record.language
        existing.size = record.size
        existing.modified_at = record.modified_at
        existing.checksum = record.checksum
        existing.last_indexed_at = _utcnow()
        self._session.flush()
        return existing

    def all_paths(self) -> set[str]:
        rows = self._session.execute(select(IndexedFile.path)).scalars().all()
        return set(rows)

    def all_records(self) -> list[IndexedFile]:
        return list(self._session.execute(select(IndexedFile)).scalars().all())

    def delete(self, path: str) -> bool:
        record = self._session.get(IndexedFile, path)
        if record is None:
            return False
        self._session.delete(record)
        self._session.flush()
        return True

    def commit(self) -> None:
        self._session.commit()

    def count(self) -> int:
        return self._session.query(IndexedFile).count()


class ChunkRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_indices(self, chunk_ids: list[str]) -> dict[str, ChunkRecord]:
        if not chunk_ids:
            return {}
        rows = (
            self._session.execute(select(ChunkRecord).where(ChunkRecord.chunk_id.in_(chunk_ids)))
            .scalars()
            .all()
        )
        return {row.chunk_id: row for row in rows}

    def upsert(self, chunk: ChunkRecord) -> None:
        existing = (
            self._session.execute(select(ChunkRecord).where(ChunkRecord.chunk_id == chunk.chunk_id))
            .scalars()
            .first()
        )
        if existing is None:
            self._session.add(chunk)
        else:
            existing.content = chunk.content
            existing.content_hash = chunk.content_hash
            existing.token_estimate = chunk.token_estimate
            existing.file_path = chunk.file_path
            existing.start_line = chunk.start_line
            existing.end_line = chunk.end_line
            existing.section_title = chunk.section_title
            existing.language = chunk.language
            existing.source_type = chunk.source_type
        self._session.flush()

    def delete_for_files(self, paths: list[str]) -> list[str]:
        if not paths:
            return []
        rows = (
            self._session.execute(select(ChunkRecord).where(ChunkRecord.file_path.in_(paths)))
            .scalars()
            .all()
        )
        chunk_ids = [row.chunk_id for row in rows]
        for row in rows:
            self._session.delete(row)
        self._session.flush()
        return chunk_ids

    def for_file(self, path: str) -> list[ChunkRecord]:
        return list(
            self._session.execute(select(ChunkRecord).where(ChunkRecord.file_path == path))
            .scalars()
            .all()
        )

    def all(self) -> list[ChunkRecord]:
        return list(self._session.execute(select(ChunkRecord)).scalars().all())

    def commit(self) -> None:
        self._session.commit()

    def count(self) -> int:
        return self._session.query(ChunkRecord).count()


class EmbeddingCacheRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, content_hash: str, model: str) -> list[float] | None:
        entry = self._session.get(EmbeddingCacheEntry, content_hash)
        if entry is None or entry.model != model:
            return None
        return json.loads(entry.vector_json)

    def set(self, content_hash: str, model: str, vector: list[float]) -> None:
        entry = self._session.get(EmbeddingCacheEntry, content_hash)
        if entry is None:
            entry = EmbeddingCacheEntry(
                content_hash=content_hash, model=model, vector_json=json.dumps(vector)
            )
            self._session.add(entry)
        else:
            entry.model = model
            entry.vector_json = json.dumps(vector)
        self._session.flush()

    def commit(self) -> None:
        self._session.commit()

    def count(self) -> int:
        return self._session.query(EmbeddingCacheEntry).count()


class SnapshotRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, payload: dict) -> None:
        entry = RepositorySnapshotEntry(payload_json=json.dumps(payload))
        self._session.add(entry)
        self._session.commit()

    def latest(self) -> dict | None:
        row = (
            self._session.execute(
                select(RepositorySnapshotEntry).order_by(RepositorySnapshotEntry.id.desc())
            )
            .scalars()
            .first()
        )
        if row is None:
            return None
        return json.loads(row.payload_json)
