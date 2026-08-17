"""Vector store — Phase 1 ships an in-memory store.

The VectorStore protocol (see app/context/interfaces.py) keeps this
swappable: a Qdrant implementation can be dropped in later without
touching the indexer or search services. Persistence of derived chunks
lives in SQLite (chunks table); the in-memory index (vectors + token
stats) is rebuilt from persisted chunks on every pipeline run, so a
process restart cannot leave the index empty.
"""

from __future__ import annotations

import hashlib
import math
import threading
import uuid

from app.context.interfaces import VectorStore
from app.context.models import VectorPoint

# Keyword component weights (soft BM25 saturation + path bonus).
_KEYWORD_K = 1.2
_PATH_BONUS = 1.5


class InMemoryVectorStore(VectorStore):
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._vectors: dict[str, list[float]] = {}
        self._meta: dict[str, dict] = {}

    def upsert(self, points: list[VectorPoint]) -> None:
        with self._lock:
            for point in points:
                self._vectors[point.chunk_id] = point.vector
                self._meta[point.chunk_id] = {
                    "path": point.file_path,
                    "start_line": point.start_line,
                    "end_line": point.end_line,
                    "section_title": point.section_title,
                    "language": point.language,
                    "source_type": point.source_type,
                    "keywords": point.keywords,
                    "subword_tokens": point.subword_tokens,
                    "path_tokens": point.path_tokens,
                }

    def search(
        self, vector: list[float], limit: int, filter_kwargs: dict
    ) -> list[tuple[str, float]]:
        with self._lock:
            scored: list[tuple[str, float]] = []
            for chunk_id, candidate in self._vectors.items():
                if not self._passes_filters(chunk_id, filter_kwargs):
                    continue
                score = _cosine(vector, candidate)
                if score > 0:
                    scored.append((chunk_id, score))
            scored.sort(key=lambda item: item[1], reverse=True)
            return scored[:limit]

    def keyword_search(
        self, tokens: list[str], limit: int, filter_kwargs: dict
    ) -> list[tuple[str, float]]:
        """Soft-BM25 keyword retrieval over subword tokens with a path bonus.

        ``tokens`` must be deduplicated subword tokens. Scores are raw
        (unnormalized) keyword scores; callers normalize before fusing.
        """
        if not tokens:
            return []
        scores, _path_bonus, _stats = self._keyword_scores(tokens, filter_kwargs)
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        return ranked[:limit]

    def keyword_search_explain(
        self, tokens: list[str], filter_kwargs: dict
    ) -> tuple[list[tuple[str, float]], dict]:
        """Keyword search plus corpus statistics and per-chunk path bonuses."""
        scores, path_bonus, stats = self._keyword_scores(tokens, filter_kwargs)
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        stats["path_bonus"] = path_bonus
        return ranked, stats

    def get_vector(self, chunk_id: str) -> list[float] | None:
        with self._lock:
            return self._vectors.get(chunk_id)

    def _keyword_scores(
        self, tokens: list[str], filter_kwargs: dict
    ) -> tuple[dict[str, float], dict[str, float], dict]:
        empty: tuple[dict[str, float], dict[str, float], dict] = (
            {},
            {},
            {"corpus": 0, "df": {}, "idf": {}},
        )
        if not tokens:
            return empty
        with self._lock:
            n = len(self._vectors)
            if n == 0:
                return empty
            df = {token: 0 for token in tokens}
            for meta in self._meta.values():
                counts = meta["subword_tokens"]
                for token in tokens:
                    if token in counts:
                        df[token] += 1
            idf = {
                token: math.log((n - doc_freq + 0.5) / (doc_freq + 0.5) + 1.0)
                for token, doc_freq in df.items()
            }
            scores: dict[str, float] = {}
            path_bonus: dict[str, float] = {}
            for chunk_id, meta in self._meta.items():
                if not self._passes_filters(chunk_id, filter_kwargs):
                    continue
                counts = meta["subword_tokens"]
                score = 0.0
                for token in tokens:
                    freq = counts.get(token, 0)
                    if freq == 0:
                        continue
                    score += idf[token] * freq / (freq + _KEYWORD_K)
                path_tokens = meta["path_tokens"]
                bonus = 0.0
                if path_tokens:
                    bonus = _PATH_BONUS * sum(
                        idf[token] for token in tokens if token in path_tokens
                    )
                    score += bonus
                if score > 0:
                    scores[chunk_id] = score
                path_bonus[chunk_id] = bonus
            return scores, path_bonus, {"corpus": n, "df": df, "idf": idf}

    def _passes_filters(self, chunk_id: str, filter_kwargs: dict) -> bool:
        meta = self._meta[chunk_id]
        languages = filter_kwargs.get("languages")
        source_types = filter_kwargs.get("source_types")
        paths = filter_kwargs.get("paths")
        if languages and meta["language"] not in languages:
            return False
        if source_types and meta["source_type"] not in source_types:
            return False
        if paths and not any(p in meta["path"] for p in paths):
            return False
        return True

    def missing_ids(self, chunk_ids: list[str]) -> list[str]:
        with self._lock:
            return [chunk_id for chunk_id in chunk_ids if chunk_id not in self._vectors]

    def delete_chunks(self, chunk_ids: list[str]) -> None:
        with self._lock:
            for chunk_id in chunk_ids:
                self._vectors.pop(chunk_id, None)
                self._meta.pop(chunk_id, None)

    def count(self) -> int:
        with self._lock:
            return len(self._vectors)

    def random_sample(self, n: int) -> list[str]:
        with self._lock:
            ids = list(self._vectors.keys())
            if not ids:
                return []
            digest = int.from_bytes(hashlib.md5(str(ids).encode()).digest()[:4], "little")
            start = digest % max(1, len(ids))
            return ids[start : start + n]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    if dot <= 0:
        return 0.0
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if not norm_a or not norm_b:
        return 0.0
    return dot / (norm_a * norm_b)


def make_keywords(text: str, limit: int = 12) -> list[str]:
    """Backwards-compatible wrapper around the tokenizer-based extraction."""
    from app.context.tokenizer import make_keywords as _make_keywords

    return _make_keywords(text, limit)


def new_id() -> str:
    return uuid.uuid4().hex[:32]
