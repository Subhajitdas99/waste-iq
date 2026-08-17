"""Dependency injection container for the Repository Context Service.

A single place wiring interfaces to implementations. Tests replace the
vector store / embedder / snapshot provider / repository root via
constructor overrides.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.context.chunk_store import SqlChunkStore
from app.context.embeddings import HashEmbeddingProvider
from app.context.indexer_pipeline import IndexerPipeline
from app.context.repository_indexer import RepositoryIndexer
from app.context.semantic_search import SemanticSearchService
from app.context.snapshot import GitSnapshotProvider
from app.context.vector_store import InMemoryVectorStore
from app.core.config import settings


class Container:
    """Holds service instances; all are lazily created and shared."""

    def __init__(
        self,
        session_factory: Callable[[], Any],
        repository_root: Path | None = None,
        ignored_dirs: list[str] | None = None,
        ignored_files: list[str] | None = None,
        min_tokens: int | None = None,
        max_tokens: int | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._repository_root_override = repository_root
        self._ignored_dirs = ignored_dirs or settings.agent_ignored_dirs
        self._ignored_files = ignored_files or settings.agent_ignored_files
        self._min_tokens = min_tokens or settings.agent_chunk_min_tokens
        self._max_tokens = max_tokens or settings.agent_chunk_max_tokens
        self._vector_store = InMemoryVectorStore()
        self._embedder = HashEmbeddingProvider()
        self._snapshot_provider = GitSnapshotProvider(self.repository_root)
        self._indexer: RepositoryIndexer | None = None
        self._pipeline: IndexerPipeline | None = None
        self._search: SemanticSearchService | None = None

    @property
    def repository_root(self) -> Path:
        if self._repository_root_override is not None:
            return self._repository_root_override
        return Path(settings.agent_repository_root).resolve()

    @property
    def snapshot_provider(self) -> GitSnapshotProvider:
        return self._snapshot_provider

    @snapshot_provider.setter
    def snapshot_provider(self, provider: Any) -> None:
        self._snapshot_provider = provider

    @property
    def vector_store(self) -> InMemoryVectorStore:
        return self._vector_store

    @vector_store.setter
    def vector_store(self, store: Any) -> None:
        self._vector_store = store
        self._pipeline = None
        self._search = None

    @property
    def embedder(self) -> HashEmbeddingProvider:
        return self._embedder

    @embedder.setter
    def embedder(self, provider: Any) -> None:
        self._embedder = provider
        self._pipeline = None
        self._search = None

    def _session(self) -> Any:
        return self._session_factory()

    def store(self) -> SqlChunkStore:
        return SqlChunkStore(self._session())

    def indexer(self) -> RepositoryIndexer:
        if self._indexer is None:
            self._indexer = RepositoryIndexer(
                store=self.store(),
                root=self.repository_root,
                ignored_dirs=self._ignored_dirs,
                ignored_files=self._ignored_files,
                min_tokens=self._min_tokens,
                max_tokens=self._max_tokens,
            )
        return self._indexer

    def pipeline(self) -> IndexerPipeline:
        if self._pipeline is None:
            self._pipeline = IndexerPipeline(
                indexer=self.indexer(),
                store=self.store(),
                embedding_provider=self._embedder,
                vector_store=self._vector_store,
            )
        return self._pipeline

    def search_service(self) -> SemanticSearchService:
        if self._search is None:
            self._search = SemanticSearchService(
                vector_store=self._vector_store,
                embedding_provider=self._embedder,
                chunk_store=self.store(),
            )
        return self._search

    def status(self) -> dict:
        store = self.store()
        latest = store.latest_snapshot()
        version = latest.get("latest_commit_sha") if latest else None
        return {
            "indexed_files": store.indexed_file_count(),
            "chunk_count": store.chunk_count(),
            "embedding_count": store.embedding_count(),
            "vector_count": self._vector_store.count(),
            "last_indexed_at": store.latest_indexed_at(),
            "repository_version": version,
            "is_indexing": self.pipeline().is_indexing,
        }
