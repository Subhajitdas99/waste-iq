"""SQL-backed ChunkStore — bridges the context layer to SQLAlchemy repositories."""

from __future__ import annotations

from typing import cast

from sqlalchemy.orm import Session

from app.context.interfaces import ChunkStore
from app.context.models import Chunk, FileMetadata, SourceType
from app.db.models import ChunkRecord, IndexedFile
from app.db.repositories import (
    ChunkRepository,
    EmbeddingCacheRepository,
    IndexedFileRepository,
    SnapshotRepository,
)


class SqlChunkStore(ChunkStore):
    def __init__(self, session: Session) -> None:
        self._session = session
        self._chunks = ChunkRepository(session)
        self._files = IndexedFileRepository(session)
        self._cache = EmbeddingCacheRepository(session)
        self._snapshots = SnapshotRepository(session)

    def record_file(self, chunk: Chunk) -> None:
        self._chunks.upsert(_to_record(chunk))

    def delete_chunks_for_files(self, paths: list[str]) -> list[str]:
        return self._chunks.delete_for_files(paths)

    def get_existing(self, chunk_ids: list[str]) -> dict[str, Chunk]:
        return {
            chunk_id: _from_record(row)
            for chunk_id, row in self._chunks.find_by_indices(chunk_ids).items()
        }

    def get_chunks_for_file(self, path: str) -> list[Chunk]:
        return [_from_record(row) for row in self._chunks.for_file(path)]

    def all_chunks(self) -> list[Chunk]:
        return [_from_record(row) for row in self._chunks.all()]

    def list_indexed_files(self) -> list[FileMetadata]:
        return [
            FileMetadata(
                path=record.path,
                language=record.language,
                size=record.size,
                modified_at=record.modified_at,
                checksum=record.checksum,
            )
            for record in self._files.all_records()
        ]

    def upsert_chunk(self, chunk: Chunk) -> None:
        self._chunks.upsert(_to_record(chunk))

    def commit(self) -> None:
        self._session.commit()

    def indexed_files(self) -> set[str]:
        return self._files.all_paths()

    def mark_indexed(
        self, path: str, language: str, size: int, modified_at: float, checksum: str
    ) -> None:
        self._files.upsert(
            IndexedFile(
                path=path,
                language=language,
                size=size,
                modified_at=modified_at,
                checksum=checksum,
            )
        )

    def remove_file(self, path: str) -> None:
        self._files.delete(path)

    def indexed_file_count(self) -> int:
        return self._files.count()

    def chunk_count(self) -> int:
        return self._chunks.count()

    def embedding_count(self) -> int:
        return self._cache.count()

    def latest_indexed_at(self) -> str | None:
        rows = (
            self._session.query(IndexedFile.last_indexed_at)
            .order_by(IndexedFile.last_indexed_at.desc())
            .first()
        )
        if not rows:
            return None
        return rows[0].isoformat()

    def save_snapshot(self, payload: dict) -> None:
        self._snapshots.save(payload)

    def latest_snapshot(self) -> dict | None:
        return self._snapshots.latest()

    def embedding_lookup(self, content_hash: str, model: str) -> list[float] | None:
        return self._cache.get(content_hash, model)

    def embedding_store(self, content_hash: str, model: str, vector: list[float]) -> None:
        self._cache.set(content_hash, model, vector)


def _to_record(chunk: Chunk) -> ChunkRecord:
    return ChunkRecord(
        chunk_id=chunk.chunk_id,
        file_path=chunk.file_path,
        start_line=chunk.start_line,
        end_line=chunk.end_line,
        section_title=chunk.section_title,
        language=chunk.language,
        source_type=chunk.source_type,
        content=chunk.content,
        content_hash=chunk.content_hash,
        token_estimate=chunk.token_estimate,
    )


def _from_record(row: ChunkRecord) -> Chunk:
    return Chunk(
        chunk_id=row.chunk_id,
        file_path=row.file_path,
        start_line=row.start_line,
        end_line=row.end_line,
        section_title=row.section_title,
        language=row.language,
        source_type=cast(SourceType, row.source_type),
        content=row.content,
        content_hash=row.content_hash,
        token_estimate=row.token_estimate,
    )
