"""Deterministic hash-based embeddings — Phase 1 does NOT call any LLM.

Produces reproducible dense vectors so search works without external
services. A real embedding provider (e.g. sentence-transformers or an
API) can replace this implementation without changing call sites.

The embedder hashes character n-grams of *subword tokens* (see
app/context/tokenizer.py), so identifiers written as snake_case or
camelCase align with the words a human would type in a query.
"""

from __future__ import annotations

import hashlib
import math

from app.context.tokenizer import subword_tokens

_DIM = 384


class HashEmbeddingProvider:
    """Subword n-gram hashing embedding: stable, fast, dependency-free."""

    model_name = "hash-subword-v1"
    dimension = _DIM

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def embed_query(self, query: str) -> list[float]:
        return self._embed_one(query)

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * _DIM
        for token in subword_tokens(text):
            for n in (2, 3):
                for i in range(max(0, len(token) - n + 1)):
                    ngram = token[i : i + n]
                    digest = hashlib.md5(ngram.encode("utf-8")).digest()
                    index = int.from_bytes(digest[:4], "little") % _DIM
                    sign = 1.0 if digest[4] % 2 == 0 else -1.0
                    vector[index] += sign
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [x / norm for x in vector]
        return vector
