from app.context.code_parser import (
    parse_code,
    parse_docstring_sections,
    parse_document,
)
from app.context.documentation_parser import (
    chunk_document,
    split_document_chunks,
)


def test_parse_code_imports():
    elements = parse_code("a.py", "import os\nfrom fastapi import FastAPI\n", language="py")
    kinds = [e.kind for e in elements]
    assert kinds == ["import", "import"]


def test_parse_code_classes_and_functions():
    text = "class Foo:\n" "    def bar(self):\n" "        pass\n" "def baz():\n" "    pass\n"
    elements = parse_code("a.py", text, language="py")
    by_kind = {(e.kind, e.name) for e in elements}
    assert ("class", "Foo") in by_kind
    assert ("function", "bar") in by_kind
    assert ("function", "baz") in by_kind


def test_parse_code_typescript_arrow_functions():
    text = "export function run() {}\nconst go = async () => {}\n"
    elements = parse_code("a.ts", text, language="ts")
    assert len(elements) == 2
    assert all(e.kind == "function" for e in elements)


def test_parse_docstring_sections():
    text = "# Title\nsome text\n## Sub\nmore\n"
    assert parse_docstring_sections(text) == ["Title", "Sub"]


def test_parse_document_kind_classification():
    assert parse_document("docs/architecture/overview.md", "# x").kind == "architecture"
    assert parse_document("docs/roadmap.md", "# x").kind == "roadmap"
    assert parse_document("docs/ADR-001.md", "# x").kind == "adr"
    assert parse_document("api/client.md", "# x").kind == "api"
    assert parse_document("README.md", "# x").kind == "readme"
    assert parse_document("CHANGELOG.md", "# x").kind == "changelog"
    assert parse_document("misc/notes.txt", "# x").kind == "other"


def test_parse_document_extracts_metadata():
    text = (
        "# Project\n\n"
        "## Goal\n\n"
        "- Milestone 1: build\n"
        "- Feature: search\n"
        "- Decision: use sqlite\n"
        "- Status: accepted\n"
        "TODO: fix bug\n"
        "FIXME: crash\n"
        "ADR-0007 referenced\n"
    )
    meta = parse_document("docs/design/plan.md", text)
    assert meta.title == "Project"
    assert meta.sections == ["Project", "Goal"]
    assert "TODO: fix bug" in meta.todos
    assert "FIXME: crash" in meta.todos
    assert any("Milestone 1" in m for m in meta.milestones)
    assert any("Feature: search" in f for f in meta.features)
    assert any("Decision: use sqlite" in d for d in meta.decisions)
    assert "0007" in meta.adr_ids


def test_parse_document_empty_text():
    meta = parse_document("README.md", "")
    assert meta.title is None
    assert meta.kind == "readme"


def test_split_document_chunks_headings():
    text = "# A\nx\n## B\ny\n### C\nz\n"
    ranges = split_document_chunks(text)
    assert ranges == [
        (0, 1, "A"),
        (2, 3, "B"),
        (4, 5, "C"),
    ]


def test_split_document_chunks_no_headings():
    assert split_document_chunks("plain text only") == [(0, 0, None)]


def test_chunk_document_unique_chunk_ids_and_offsets():
    text = "# Title\nline one\n## Section\nline two\n"
    chunks = chunk_document("doc.md", text, min_tokens=1, max_tokens=1000)
    ids = [c.chunk_id for c in chunks]
    assert len(set(ids)) == len(ids)
    assert all(c.source_type == "docs" for c in chunks)
    starts = sorted(c.start_line for c in chunks)
    assert starts == [1, 3]


def test_chunk_document_empty_text_falls_back():
    chunks = chunk_document("doc.md", "", min_tokens=1, max_tokens=1000)
    assert chunks == [] or all(c.source_type == "docs" for c in chunks)
