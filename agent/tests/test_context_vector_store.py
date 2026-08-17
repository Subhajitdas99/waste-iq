from app.context.models import VectorPoint
from app.context.vector_store import InMemoryVectorStore, make_keywords


def _point(chunk_id, vector, language="py", source_type="code", path="a.py"):
    return VectorPoint(
        chunk_id=chunk_id,
        file_path=path,
        start_line=1,
        end_line=2,
        section_title=None,
        language=language,
        source_type=source_type,
        vector=vector,
    )


def test_upsert_and_count():
    store = InMemoryVectorStore()
    store.upsert([_point("c1", [1.0, 0.0]), _point("c2", [0.0, 1.0])])
    assert store.count() == 2
    store.upsert([_point("c1", [0.5, 0.5])])
    assert store.count() == 2


def test_search_ranking():
    store = InMemoryVectorStore()
    store.upsert([_point("c1", [1.0, 0.0]), _point("c2", [0.9, 0.1]), _point("c3", [0.1, 0.9])])
    hits = store.search([1.0, 0.0], limit=2, filter_kwargs={})
    ids = [chunk_id for chunk_id, _ in hits]
    assert ids == ["c1", "c2"]


def test_search_filters():
    store = InMemoryVectorStore()
    store.upsert(
        [
            _point("c1", [1.0, 0.0], language="py"),
            _point("c2", [0.9, 0.0], language="go"),
            _point("c3", [0.8, 0.0], language="markdown", source_type="docs", path="README.md"),
        ]
    )
    hits = store.search([1.0, 0.0], limit=5, filter_kwargs={"languages": ["py"]})
    assert [cid for cid, _ in hits] == ["c1"]
    docs = store.search([1.0, 0.0], limit=5, filter_kwargs={"source_types": ["docs"]})
    assert [cid for cid, _ in docs] == ["c3"]
    paths = store.search([1.0, 0.0], limit=5, filter_kwargs={"paths": ["README"]})
    assert [cid for cid, _ in paths] == ["c3"]


def test_search_zero_score_excluded():
    store = InMemoryVectorStore()
    store.upsert([_point("c1", [1.0, 0.0]), _point("c2", [-1.0, 1.0])])
    hits = store.search([1.0, 0.0], limit=5, filter_kwargs={})
    assert [cid for cid, _ in hits] == ["c1"]


def test_delete_chunks():
    store = InMemoryVectorStore()
    store.upsert([_point("c1", [1.0, 0.0]), _point("c2", [0.0, 1.0])])
    store.delete_chunks(["c1"])
    assert store.count() == 1
    assert [cid for cid, _ in store.search([1.0, 0.0], 5, {})] == []


def test_random_sample_bounds():
    store = InMemoryVectorStore()
    assert store.random_sample(3) == []
    store.upsert([_point(f"c{i}", [1.0, 0.0]) for i in range(5)])
    sample = store.random_sample(2)
    assert len(sample) == 2
    assert set(sample) <= {"c1", "c2", "c3", "c4", "c5"}


def test_make_keywords():
    words = make_keywords("the add function for vector qdrant qdrant search")
    assert "qdrant" in words
    assert "the" not in words
    assert make_keywords("") == []
    assert make_keywords("aa bb") == []
