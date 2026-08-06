"""Semantic search service — hybrid keyword + vector retrieval."""

from __future__ import annotations

from app.context.interfaces import ChunkStore, EmbeddingProvider, VectorStore
from app.context.models import SearchRequest, SearchResponse, ScoredChunk
from app.context.tokenizer import expand_query_tokens

# Fused-score blend: keyword scoring is the primary, high-precision signal
# for code retrieval; the vector component adds semantic recall.
_KEYWORD_WEIGHT = 0.75
_VECTOR_WEIGHT = 0.25


class SemanticSearchService:
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_provider: EmbeddingProvider,
        chunk_store: ChunkStore,
    ) -> None:
        self._vector_store = vector_store
        self._embedder = embedding_provider
        self._chunk_store = chunk_store

    def search(self, request: SearchRequest) -> SearchResponse:
        vector = self._embedder.embed([request.query])[0]
        vector_hits = self._vector_store.search(vector, request.limit, self._filters(request))
        return self._to_response(vector_hits)

    def hybrid_search(self, request: SearchRequest) -> SearchResponse:
        """Keyword (soft-BM25 + path bonus) fused with vector cosine."""
        tokens = expand_query_tokens(request.query)
        if not tokens:
            return SearchResponse(results=[], total=0)

        filters = self._filters(request)
        keyword_hits = self._vector_store.keyword_search(tokens, request.limit * 3, filters)

        if request.hybrid:
            vector = self._embedder.embed([request.query])[0]
            vector_hits = dict(self._vector_store.search(vector, request.limit * 3, filters))
        else:
            vector_hits = {}

        scored: dict[str, float] = {}
        if keyword_hits:
            max_kw = max(score for _, score in keyword_hits)
            max_vec = max(vector_hits.values(), default=0.0)
            for chunk_id, kw_score in keyword_hits:
                fused = kw_score / max_kw
                if request.hybrid:
                    vec_score = vector_hits.get(chunk_id, 0.0)
                    if max_vec > 0:
                        fused = _KEYWORD_WEIGHT * fused + _VECTOR_WEIGHT * (vec_score / max_vec)
                scored[chunk_id] = max(scored.get(chunk_id, 0.0), fused)
        elif vector_hits:
            max_vec = max(vector_hits.values())
            for chunk_id, score in vector_hits.items():
                scored[chunk_id] = score / max_vec

        ranked = sorted(scored.items(), key=lambda item: item[1], reverse=True)[: request.limit]
        return self._to_response(ranked)

    def explain(self, request: SearchRequest) -> dict:
        """Full scoring breakdown for a query (debug/introspection)."""
        tokens = expand_query_tokens(request.query)
        filters = self._filters(request)
        vector = self._embedder.embed([request.query])[0]
        hits, stats = self._vector_store.keyword_search_explain(tokens, filters)
        max_kw = max((score for _, score in hits), default=0.0)
        candidates: list[dict] = []
        chunks = self._chunk_store.get_existing([chunk_id for chunk_id, _ in hits])
        vector = self._embedder.embed([request.query])[0]
        vector_scores = {
            chunk_id: _cosine(vector, vec)
            for chunk_id, vec in ((cid, self._vector_store.get_vector(cid)) for cid, _ in hits)
            if vec is not None
        }
        max_vec = max(vector_scores.values(), default=0.0)
        for chunk_id, kw_score in hits:
            chunk = chunks.get(chunk_id)
            if chunk is None:
                continue
            cos = vector_scores.get(chunk_id, 0.0)
            norm_kw = kw_score / max_kw if max_kw else 0.0
            norm_vec = (cos / max_vec) if max_vec > 0 else 0.0
            fused = _KEYWORD_WEIGHT * norm_kw + _VECTOR_WEIGHT * norm_vec
            candidates.append(
                {
                    "chunk_id": chunk_id,
                    "path": chunk.file_path,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "language": chunk.language,
                    "source_type": chunk.source_type,
                    "keyword_score": round(kw_score, 4),
                    "keyword_normalized": round(norm_kw, 4),
                    "path_bonus": round(stats["path_bonus"].get(chunk_id, 0.0), 4),
                    "vector_score": round(cos, 4),
                    "vector_normalized": round(norm_vec, 4),
                    "fused_score": round(fused, 4),
                }
            )
        candidates.sort(key=lambda item: item["fused_score"], reverse=True)
        return {
            "query": request.query,
            "tokens": tokens,
            "corpus_size": stats["corpus"],
            "document_frequency": {t: stats["df"].get(t, 0) for t in tokens},
            "inverse_document_frequency": {t: round(stats["idf"].get(t, 0.0), 4) for t in tokens},
            "vector_count": self._vector_store.count(),
            "total_candidates": len(candidates),
            "candidates": candidates[: request.limit],
        }

    @staticmethod
    def _filters(request: SearchRequest) -> dict:
        return {
            "languages": request.languages,
            "source_types": request.source_types,
            "paths": request.paths,
        }

    def _to_response(self, hits: list[tuple[str, float]]) -> SearchResponse:
        results: list[ScoredChunk] = []
        for chunk_id, score in hits:
            chunk = self._chunk_store.get_existing([chunk_id]).get(chunk_id)
            if chunk is None:
                continue
            results.append(
                ScoredChunk(
                    chunk_id=chunk.chunk_id,
                    path=chunk.file_path,
                    start_line=chunk.start_line,
                    end_line=chunk.end_line,
                    section_title=chunk.section_title,
                    language=chunk.language,
                    source_type=chunk.source_type,
                    score=round(float(score), 6),
                )
            )
        return SearchResponse(results=results, total=len(results))


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    if dot <= 0:
        return 0.0
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if not norm_a or not norm_b:
        return 0.0
    return dot / (norm_a * norm_b)
