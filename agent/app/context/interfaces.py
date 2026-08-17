"""Interfaces (protocols) for the Repository Context Service.

Injected dependencies — implementations are provided by app/context/di.py
and are swappable in tests.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.context.models import Chunk, FileMetadata, VectorPoint


@runtime_checkable
class EmbeddingProvider(Protocol):
    model_name: str

    def embed(self, texts: list[str]) -> list[list[float]]: ...


@runtime_checkable
class VectorStore(Protocol):
    def upsert(self, points: list[VectorPoint]) -> None: ...

    def search(
        self, vector: list[float], limit: int, filter_kwargs: dict
    ) -> list[tuple[str, float]]:
        """Return [(chunk_id, score), ...] sorted by relevance descending."""
        ...

    def keyword_search(
        self, tokens: list[str], limit: int, filter_kwargs: dict
    ) -> list[tuple[str, float]]:
        """Soft-BM25 keyword retrieval; returns [(chunk_id, raw_score), ...]."""
        ...

    def keyword_search_explain(
        self, tokens: list[str], filter_kwargs: dict
    ) -> tuple[list[tuple[str, float]], dict]:
        """Keyword retrieval plus corpus stats (df/idf, path bonuses)."""
        ...

    def get_vector(self, chunk_id: str) -> list[float] | None: ...

    def missing_ids(self, chunk_ids: list[str]) -> list[str]: ...

    def delete_chunks(self, chunk_ids: list[str]) -> None: ...

    def count(self) -> int: ...


@runtime_checkable
class SnapshotProvider(Protocol):
    def fetch(self) -> str | None:
        """Fetch a JSON payload snapshot of the repository (None if unavailable)."""
        ...


@runtime_checkable
class ChunkStore(Protocol):
    """Persistence for chunks and index metadata (wraps repositories)."""

    def record_file(self, chunk: Chunk) -> None: ...

    def delete_chunks_for_files(self, paths: list[str]) -> list[str]: ...

    def get_existing(self, chunk_ids: list[str]) -> dict[str, Chunk]: ...

    def get_chunks_for_file(self, path: str) -> list[Chunk]: ...

    def all_chunks(self) -> list[Chunk]: ...

    def list_indexed_files(self) -> list["FileMetadata"]: ...

    def upsert_chunk(self, chunk: Chunk) -> None: ...

    def commit(self) -> None: ...

    def indexed_files(self) -> set[str]: ...

    def mark_indexed(
        self, path: str, language: str, size: int, modified_at: float, checksum: str
    ) -> None: ...

    def remove_file(self, path: str) -> None: ...

    def indexed_file_count(self) -> int: ...

    def chunk_count(self) -> int: ...

    def embedding_count(self) -> int: ...

    def latest_indexed_at(self) -> str | None: ...

    def save_snapshot(self, payload: dict) -> None: ...

    def latest_snapshot(self) -> dict | None: ...

    def embedding_lookup(self, content_hash: str, model: str) -> list[float] | None: ...

    def embedding_store(self, content_hash: str, model: str, vector: list[float]) -> None: ...
