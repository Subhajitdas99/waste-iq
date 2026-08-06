import math

from app.context.embeddings import HashEmbeddingProvider


def test_embedding_deterministic():
    provider = HashEmbeddingProvider()
    a = provider.embed(["hello world"])
    b = provider.embed(["hello world"])
    assert a[0] == b[0]


def test_embedding_dimension_and_normalized():
    provider = HashEmbeddingProvider()
    vector = provider.embed(["waste iq agent"])[0]
    assert len(vector) == provider.dimension == 384
    norm = math.sqrt(sum(x * x for x in vector))
    assert abs(norm - 1.0) < 1e-6


def test_embedding_distinguishes_texts():
    provider = HashEmbeddingProvider()
    a = provider.embed(["vector database qdrant"])
    b = provider.embed(["css styling color"])
    assert a[0] != b[0]


def test_embed_query_matches_embed():
    provider = HashEmbeddingProvider()
    assert provider.embed_query("query text") == provider.embed(["query text"])[0]


def test_empty_text_returns_zero_vector():
    provider = HashEmbeddingProvider()
    vector = provider.embed([""])[0]
    assert sum(vector) == 0.0
