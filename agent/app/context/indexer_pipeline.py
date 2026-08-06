"""Indexer pipeline — orchestrates indexing with the embedding cache."""

from __future__ import annotations

import threading
import time

from app.context.interfaces import ChunkStore, EmbeddingProvider, VectorStore
from app.context.models import IndexRunSummary
from app.context.repository_indexer import RepositoryIndexer, to_vector_points


class IndexerPipeline:
    def __init__(
        self,
        indexer: RepositoryIndexer,
        store: ChunkStore,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> None:
        self._indexer = indexer
        self._store = store
        self._embedder = embedding_provider
        self._vector_store = vector_store
        self._lock = threading.Lock()
        self._is_indexing = False

    @property
    def is_indexing(self) -> bool:
        return self._is_indexing

    def run(self) -> IndexRunSummary:
        if self._is_indexing:
            raise RuntimeError("indexing already in progress")
        self._is_indexing = True
        started = time.monotonic()
        try:
            return self._run_locked(started)
        finally:
            self._is_indexing = False

    def _run_locked(self, started: float) -> IndexRunSummary:
        files = self._indexer.iter_files()
        indexed = self._store.indexed_files()
        root = self._indexer.root
        new_files = [p for p in files if p.relative_to(root).as_posix() not in indexed]
        existing = [p for p in files if p.relative_to(root).as_posix() in indexed]
        updated_files: list = []
        removed_paths = indexed - {p.relative_to(root).as_posix() for p in files}

        stats = IndexRunSummary(
            new_files=0,
            updated_files=0,
            removed_files=len(removed_paths),
            chunks_created=0,
            chunks_removed=0,
            embeddings_created=0,
            embeddings_cache_hits=0,
            took_seconds=0.0,
        )

        all_new_chunks: list = []
        for path in new_files:
            chunks = self._indexer.index_file(path)
            all_new_chunks.extend(chunks)
            self._store.mark_indexed(
                path.relative_to(root).as_posix(),
                language=chunks[0].language if chunks else "text",
                size=path.stat().st_size,
                modified_at=path.stat().st_mtime,
                checksum=_checksum(path),
            )
            stats.new_files += 1

        for path in existing:
            rel = path.relative_to(root).as_posix()
            chunks = self._indexer.index_file(path)
            stored = self._store.get_chunks_for_file(rel)
            if _same_file(path, rel, stored, chunks):
                continue
            updated_files.append(rel)
            stale_ids = self._store.delete_chunks_for_files([rel])
            self._vector_store.delete_chunks(stale_ids)
            all_new_chunks.extend(chunks)
            self._store.mark_indexed(
                rel,
                language=chunks[0].language if chunks else "text",
                size=path.stat().st_size,
                modified_at=path.stat().st_mtime,
                checksum=_checksum(path),
            )
            stats.updated_files += 1

        if removed_paths:
            removed_list = list(removed_paths)
            removed_chunk_ids = self._store.delete_chunks_for_files(removed_list)
            self._vector_store.delete_chunks(removed_chunk_ids)
            stats.chunks_removed += len(removed_chunk_ids)
            for rel in removed_list:
                self._store.remove_file(rel)

        model = self._embedder.model_name
        vectors: list[list[float]] = []
        for chunk in all_new_chunks:
            cached = self._store.embedding_lookup(chunk.content_hash, model)
            if cached is not None:
                vectors.append(cached)
                stats.embeddings_cache_hits += 1
            else:
                vectors.append(self._embedder.embed([chunk.content])[0])
                self._store.embedding_store(chunk.content_hash, model, vectors[-1])
                stats.embeddings_created += 1

        points = to_vector_points(all_new_chunks, vectors)
        self._vector_store.upsert(points)
        for chunk in all_new_chunks:
            self._store.upsert_chunk(chunk)
        self._ensure_vector_index()
        self._store.commit()

        stats.chunks_created = len(all_new_chunks)
        stats.took_seconds = round(time.monotonic() - started, 3)
        return stats

    def _ensure_vector_index(self) -> None:
        """Rebuild any vectors missing from the in-memory store.

        The vector store is ephemeral; persisted chunks + the embedding
        cache survive restarts. This step guarantees a warm process
        (nothing changed on disk) still serves search from a populated
        index, and that a model change re-embeds stale cache entries.
        """
        persisted = self._store.all_chunks()
        missing = self._vector_store.missing_ids([c.chunk_id for c in persisted])
        if not missing:
            return
        by_id = {c.chunk_id: c for c in persisted}
        vectors: list[list[float]] = []
        for chunk_id in missing:
            chunk = by_id[chunk_id]
            cached = self._store.embedding_lookup(chunk.content_hash, self._embedder.model_name)
            if cached is not None:
                vectors.append(cached)
            else:
                vectors.append(self._embedder.embed([chunk.content])[0])
                self._store.embedding_store(
                    chunk.content_hash, self._embedder.model_name, vectors[-1]
                )
        self._vector_store.upsert(to_vector_points([by_id[cid] for cid in missing], vectors))


def _checksum(path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _same_file(path, rel: str, stored: list, new_chunks: list) -> bool:
    if not stored and not new_chunks:
        return True
    if len(stored) != len(new_chunks):
        return False
    for old, new in zip(stored, new_chunks):
        if old.content_hash != new.content_hash:
            return False
    return True
