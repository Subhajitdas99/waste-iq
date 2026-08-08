"""Unit tests for the chat context builder (Phase 5)."""

from app.chat.context_builder import (
    build_repository_context,
    chat_references_from_chunks,
    classify_chunk,
    evidence_entries_from_chunks,
)
from app.context.models import ScoredChunk


def _chunk(
    path: str,
    source_type: str = "code",
    start: int = 1,
    end: int = 10,
    score: float = 0.5,
    chunk_id: str = "chunk-x",
    section_title: str | None = None,
    language: str = "python",
) -> ScoredChunk:
    return ScoredChunk(
        chunk_id=chunk_id,
        path=path,
        start_line=start,
        end_line=end,
        section_title=section_title,
        language=language,
        source_type=source_type,
        score=score,
    )


def test_classify_code():
    chunk = _chunk("src/services/approval.py", "code")
    assert classify_chunk(chunk) == "code"


def test_classify_docs():
    assert classify_chunk(_chunk("docs/guide.md", "docs")) == "docs"


def test_classify_adr_by_path_markers():
    for path in ("docs/architecture/ADR-001.md", "docs/adr/0001.md"):
        assert classify_chunk(_chunk(path, "docs")) == "adr"


def test_classify_roadmap_by_path_markers():
    for path in ("docs/roadmap.md", "docs/backlog.md", "docs/milestones.md"):
        assert classify_chunk(_chunk(path, "docs")) == "roadmap"


def test_build_repository_context_buckets():
    results = [
        _chunk("src/app.py", "code"),
        _chunk("docs/guide.md", "docs"),
        _chunk("docs/architecture/ADR-002.md", "docs"),
        _chunk("docs/roadmap.md", "docs"),
    ]
    context = build_repository_context(results, indexed_files={"src/app.py", "tests/test_app.py"})
    assert [r.path for r in context.related_files] == ["src/app.py"]
    assert [r.path for r in context.related_docs] == ["docs/guide.md"]
    assert [r.path for r in context.related_adrs] == ["docs/architecture/ADR-002.md"]
    assert [r.path for r in context.related_roadmap] == ["docs/roadmap.md"]
    assert context.has_context
    assert context.test_files_known == ["tests/test_app.py"]


def test_build_repository_context_empty():
    context = build_repository_context([], indexed_files=set())
    assert not context.has_context
    assert context.related_files == []
    assert context.related_docs == []
    assert context.related_adrs == []
    assert context.related_roadmap == []
    assert context.test_files_known == []


def test_evidence_entries_code_format():
    entries = evidence_entries_from_chunks([_chunk("src/app.py", "code", start=4, end=9)])
    assert len(entries) == 1
    assert entries[0].evidence_id == "code:src/app.py:4"
    assert entries[0].start_line == 4
    assert entries[0].end_line == 9


def test_evidence_entries_doc_format():
    entries = evidence_entries_from_chunks([_chunk("docs/guide.md", "docs", start=2, end=5)])
    assert entries[0].evidence_id == "docs:docs/guide.md:2-5"


def test_evidence_entries_deduplicated():
    entries = evidence_entries_from_chunks(
        [
            _chunk("src/app.py", "code", start=4, end=9, chunk_id="a"),
            _chunk("src/app.py", "code", start=4, end=9, chunk_id="b"),
        ]
    )
    assert len(entries) == 1


def test_chat_references_from_chunks():
    refs = chat_references_from_chunks(
        [
            _chunk("src/app.py", "code", start=4, end=9),
            _chunk("docs/guide.md", "docs", start=2, end=5),
        ]
    )
    assert refs[0].evidence_id == "code:src/app.py:4"
    assert refs[0].file_path == "src/app.py"
    assert refs[1].evidence_id == "docs:docs/guide.md:2-5"
    assert refs[1].source_type == "docs"
