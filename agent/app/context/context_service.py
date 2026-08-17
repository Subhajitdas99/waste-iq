"""Application service for the Repository Context Service API surface."""

from __future__ import annotations

from app.context.di import Container
from app.context.models import IndexRunSummary, SearchRequest, SearchResponse


class ContextService:
    def __init__(self, container: Container) -> None:
        self._container = container

    def status(self) -> dict:
        return self._container.status()

    def reindex(self, reset: bool = False) -> IndexRunSummary:
        if reset:
            self._reset_vector_index()
        return self._container.pipeline().run()

    def search(self, request: SearchRequest) -> SearchResponse:
        return self._container.search_service().hybrid_search(request)

    def snapshot(self) -> dict | None:
        payload = self._container.snapshot_provider.fetch()
        if payload is None:
            return None
        import json

        data = json.loads(payload)
        self._container.store().save_snapshot(data)
        return data

    # ------------------------------------------------------------------
    # Debug / introspection endpoints (Phase 2.6 retrieval verification)
    # ------------------------------------------------------------------

    def debug_index(self, limit: int = 100) -> dict:
        files = self._container.store().list_indexed_files()
        return {
            "total": len(files),
            "chunk_count": self._container.store().chunk_count(),
            "vector_count": self._container.vector_store.count(),
            "files": [
                {
                    "path": f.path,
                    "language": f.language,
                    "size": f.size,
                    "modified_at": f.modified_at,
                    "checksum": f.checksum,
                }
                for f in files[:limit]
            ],
        }

    def debug_chunks(self, path: str | None = None, limit: int = 50) -> dict:
        store = self._container.store()
        if path:
            chunk_records = store.get_chunks_for_file(path)
            total = len(chunk_records)
        else:
            chunk_records = store.all_chunks()
            total = len(chunk_records)
        return {
            "total": total,
            "path": path,
            "chunks": [
                {
                    "chunk_id": c.chunk_id,
                    "file_path": c.file_path,
                    "start_line": c.start_line,
                    "end_line": c.end_line,
                    "language": c.language,
                    "source_type": c.source_type,
                    "section_title": c.section_title,
                    "content_hash": c.content_hash,
                    "token_estimate": c.token_estimate,
                    "content_preview": c.content[:400],
                }
                for c in chunk_records[:limit]
            ],
        }

    def debug_vectors(self, limit: int = 50) -> dict:
        store = self._container.store()
        vector_store = self._container.vector_store
        sample_ids = vector_store.random_sample(limit)
        sample: list[dict] = []
        for chunk_id in sample_ids:
            vector = vector_store.get_vector(chunk_id)
            meta = getattr(vector_store, "_meta", {}).get(chunk_id, {})
            sample.append(
                {
                    "chunk_id": chunk_id,
                    "path": meta.get("path"),
                    "start_line": meta.get("start_line"),
                    "end_line": meta.get("end_line"),
                    "language": meta.get("language"),
                    "source_type": meta.get("source_type"),
                    "dimension": len(vector) if vector else 0,
                    "magnitude": round(sum(x * x for x in vector) ** 0.5, 4) if vector else 0.0,
                    "first_dims": [round(x, 4) for x in (vector or [])[:8]],
                }
            )
        return {
            "chunk_count": store.chunk_count(),
            "vector_count": vector_store.count(),
            "index_health": "ok" if vector_store.count() == store.chunk_count() else "mismatch",
            "sample": sample,
        }

    def debug_embeddings(self, path: str | None = None) -> dict:
        store = self._container.store()
        chunks = store.get_chunks_for_file(path) if path else store.all_chunks()
        model = self._container.embedder.model_name
        cache_hits = 0
        entries: list[dict] = []
        for chunk in chunks:
            vector = store.embedding_lookup(chunk.content_hash, model)
            if vector is not None:
                cache_hits += 1
            entries.append(
                {
                    "file_path": chunk.file_path,
                    "start_line": chunk.start_line,
                    "content_hash": chunk.content_hash,
                    "cached": vector is not None,
                    "dimension": len(vector) if vector else 0,
                }
            )
        return {
            "model": model,
            "dimension": self._container.embedder.dimension,
            "total_chunks": len(chunks),
            "cache_hits": cache_hits,
            "embedding_count": store.embedding_count(),
            "entries": entries[:50],
        }

    def debug_search(self, request: SearchRequest) -> dict:
        return self._container.search_service().explain(request)

    def _reset_vector_index(self) -> None:
        from app.context.vector_store import InMemoryVectorStore

        self._container._vector_store = InMemoryVectorStore()  # noqa: SLF001
        self._container._pipeline = None  # noqa: SLF001
        self._container._search = None  # noqa: SLF001
