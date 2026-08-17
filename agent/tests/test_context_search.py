import pytest

from app.context.di import Container
from app.context.models import SearchRequest
from app.context.semantic_search import SemanticSearchService
from app.context.vector_store import InMemoryVectorStore
from app.context.embeddings import HashEmbeddingProvider


@pytest.fixture
def indexed_container(tmp_path, clean_context_db):
    from app.db.session import SessionLocal

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "math_utils.py").write_text(
        "def multiply(a, b):\n    return a * b\n\n"
        "def fibonacci(n):\n    if n <= 1:\n        return n\n"
    )
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "roadmap.md").write_text("# Roadmap\n\n## Q2\n- Milestone: search api\n")
    c = Container(SessionLocal, repository_root=tmp_path, min_tokens=10, max_tokens=100)
    c.pipeline().run()
    return c


def test_hybrid_search_returns_chunks(indexed_container):
    service = indexed_container.search_service()
    response = service.hybrid_search(SearchRequest(query="multiply two numbers", limit=3))
    assert response.total >= 1
    assert all(
        result.path.endswith("math_utils.py") or result.path.endswith("roadmap.md")
        for result in response.results
    )


def test_hybrid_search_filters_language(indexed_container):
    service = indexed_container.search_service()
    response = service.hybrid_search(SearchRequest(query="function", limit=5, languages=["py"]))
    assert response.total >= 1
    assert all(r.language == "py" for r in response.results)


def test_hybrid_search_filters_source_type(indexed_container):
    service = indexed_container.search_service()
    response = service.hybrid_search(
        SearchRequest(query="milestone", limit=5, source_types=["docs"])
    )
    assert response.total >= 1
    assert all(r.source_type == "docs" for r in response.results)


def test_search_vector_only_uses_embedding_request_flag(indexed_container):
    service = indexed_container.search_service()
    response = service.hybrid_search(SearchRequest(query="multiply", limit=3, hybrid=False))
    assert response.total >= 1


def test_search_empty_query(indexed_container):
    service = indexed_container.search_service()
    response = service.hybrid_search(SearchRequest(query="", limit=3))
    assert response.total == 0


def test_search_returns_metadata(indexed_container):
    service = indexed_container.search_service()
    response = service.hybrid_search(SearchRequest(query="fibonacci", limit=2))
    assert response.results[0].path.endswith("math_utils.py")
    assert response.results[0].start_line >= 1
    assert response.results[0].score > 0


def test_search_direct_with_missing_chunks_dropped():
    store = InMemoryVectorStore()
    store.upsert(
        [
            __import__("app.context.models", fromlist=["VectorPoint"]).VectorPoint(
                chunk_id="ghost",
                file_path="gone.py",
                start_line=1,
                end_line=2,
                section_title=None,
                language="py",
                source_type="code",
                vector=[1.0, 0.0],
            )
        ]
    )
    service = SemanticSearchService(store, HashEmbeddingProvider(), _EmptyStore())
    response = service.search(SearchRequest(query="ghost", limit=3))
    assert response.total == 0


class _EmptyStore:
    def get_existing(self, chunk_ids):
        return {}

    def indexed_files(self):
        return set()

    def latest_snapshot(self):
        return None
