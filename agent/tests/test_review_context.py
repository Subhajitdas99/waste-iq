"""Tests for the repository context probe used by review findings."""

from app.context.models import ScoredChunk, SearchResponse
from app.review.review_context import RepositoryProbe
from app.review.review_models import ChangedFile, ContextReference

_CHANGED = [
    ChangedFile(
        path="backend/app/routes/payments.py",
        status="added",
        content="import json\n\ndef refunds_by_amount(amount):\n    return []\n",
    )
]


class FakeSearch:
    def __init__(self, responses=None, record=None):
        self._responses = responses or []
        self._calls = []
        self._record = record

    def hybrid_search(self, request):
        self._calls.append(request)
        if self._record is not None:
            self._record.append(request)
        results = [
            ScoredChunk(
                chunk_id=f"c{i}",
                path=path,
                start_line=1,
                end_line=2,
                source_type=source_type,
                language="python",
                score=0.8,
            )
            for i, (path, source_type) in enumerate(self._responses)
            if not request.source_types or source_type in request.source_types
        ]
        return SearchResponse(results=results, total=len(results))


class FakeStore:
    def __init__(self, indexed=None):
        self._indexed = indexed or set()

    def indexed_files(self):
        return self._indexed


class FakeContainer:
    def __init__(self, search, store):
        self._search = search
        self._store = store

    def search_service(self):
        return self._search

    def store(self):
        return self._store


def test_probe_collects_references_and_metrics():
    search = FakeSearch(
        responses=[
            ("backend/app/routes/payments.py", "code"),
            ("docs/architecture/api.md", "docs"),
            ("docs/adr/ADR-003-secrets.md", "adr"),
            ("docs/roadmap.md", "roadmap"),
        ]
    )
    probe = RepositoryProbe(FakeContainer(search, FakeStore()), max_references=5, query_limit=5)
    context = probe.collect(_CHANGED, "waste-iq/demo")

    assert context.has_context is True
    assert [r.path for r in context.related_files] == ["backend/app/routes/payments.py"]
    assert [r.path for r in context.related_docs] == ["docs/architecture/api.md"]
    assert [r.path for r in context.related_adrs] == ["docs/adr/ADR-003-secrets.md"]
    assert [r.path for r in context.related_roadmap] == ["docs/roadmap.md"]
    assert probe.context_queries == 6
    assert probe.references_retrieved == 6

    queries = search._calls
    assert any(q.source_types == ["adr"] for q in queries)
    assert any(q.source_types == ["docs"] for q in queries)
    assert any(q.source_types == ["roadmap"] for q in queries)
    assert any(q.source_types == ["code"] for q in queries)


def test_probe_reference_fields():
    search = FakeSearch(
        responses=[
            ("backend/app/routes/payments.py", "code"),
            ("docs/adr/ADR-003-secrets.md", "adr"),
        ]
    )
    probe = RepositoryProbe(FakeContainer(search, FakeStore()), max_references=2, query_limit=2)
    context = probe.collect(_CHANGED, "waste-iq/demo")
    ref = context.related_files[0]
    assert isinstance(ref, ContextReference)
    assert ref.path == "backend/app/routes/payments.py"
    assert ref.score == 0.8


def test_probe_without_index_returns_empty_context():
    search = FakeSearch(responses=[])
    probe = RepositoryProbe(FakeContainer(search, FakeStore()), max_references=2, query_limit=2)
    context = probe.collect(_CHANGED, "waste-iq/demo")
    assert context.has_context is False
    assert context.related_files == []
    assert context.related_adrs == []
    assert probe.references_retrieved == 0


def test_known_test_files_filtered():
    store = FakeStore(indexed={"backend/app/main.py", "backend/tests/test_main.py", "docs/x.md"})
    search = FakeSearch(responses=[])
    probe = RepositoryProbe(FakeContainer(search, store), max_references=2, query_limit=2)
    context = probe.collect(_CHANGED, "waste-iq/demo")
    assert context.test_files_known == ["backend/tests/test_main.py"]


def test_similar_code_query_uses_symbols():
    record: list = []
    search = FakeSearch(responses=[("backend/app/similar.py", "code")], record=record)
    probe = RepositoryProbe(FakeContainer(search, FakeStore()), max_references=2, query_limit=2)
    probe.collect(_CHANGED, "waste-iq/demo")
    queries = [q.query for q in record]
    assert any("refunds_by_amount" in q for q in queries)


def test_architecture_query_filters_results():
    search = FakeSearch(
        responses=[
            ("docs/architecture/overview.md", "docs"),
            ("README.md", "docs"),
        ]
    )
    probe = RepositoryProbe(FakeContainer(search, FakeStore()), max_references=5, query_limit=5)
    refs = probe.find_architecture()
    assert [r.path for r in refs] == ["docs/architecture/overview.md"]


def test_probe_with_real_container(clean_context_db):
    from pathlib import Path

    from app.api.dependencies import get_container
    from app.core.config import settings
    from app.review.pr_provider import FixturePullRequestProvider
    from app.review.review_agent import ReviewAgent
    from app.review.review_engine import ReviewEngine
    from app.review.review_models import ReviewRequest

    root = Path(settings.agent_repository_root)
    docs = root / "docs" / "architecture"
    docs.mkdir(parents=True, exist_ok=True)
    adr = docs / "ADR-003-secrets.md"
    adr.write_text(
        "# ADR-003: Secrets in environment variables\n\n"
        "Never store secrets in source code; use environment variables.\n"
    )
    overview = docs / "overview.md"
    overview.write_text("# Architecture Overview\n\nThe system uses FastAPI.\n")
    try:
        container = get_container()
        container.pipeline().run()

        probe = RepositoryProbe(container, max_references=5, query_limit=5)
        agent = ReviewAgent(FixturePullRequestProvider(), probe, ReviewEngine(probe))
        review = agent.review(ReviewRequest(repository="waste-iq/demo", pr_number=1))
        assert review.repository_context.has_context is True
        assert len(review.repository_context.related_docs) >= 1
        assert probe.context_queries > 0
    finally:
        adr.unlink(missing_ok=True)
        overview.unlink(missing_ok=True)
