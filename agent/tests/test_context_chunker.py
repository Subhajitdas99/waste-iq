from app.context.chunker import (
    chunk_lines,
    chunk_text,
    content_hash,
    estimate_tokens,
    make_chunk_id,
)
from app.context.models import Chunk


def test_estimate_tokens_minimum():
    assert estimate_tokens("") == 1
    assert estimate_tokens("a" * 400) >= 100


def test_content_hash_deterministic_and_unique():
    assert content_hash("hello") == content_hash("hello")
    assert content_hash("hello") != content_hash("world")


def test_make_chunk_id_stable_and_distinct():
    assert make_chunk_id("a.py", 1) == make_chunk_id("a.py", 1)
    assert make_chunk_id("a.py", 1) != make_chunk_id("a.py", 2)
    assert len(make_chunk_id("a.py", 1)) == 48


def test_chunk_lines_small_text_single_range():
    lines = ["def f():", "    return 1"]
    assert chunk_lines(lines, min_tokens=10, max_tokens=1000) == [(0, 1)]


def test_chunk_lines_respects_boundaries():
    lines = ["def a():", "    pass", "", "def b():", "    pass"]
    ranges = chunk_lines(lines, min_tokens=1, max_tokens=3)
    starts = [start for start, _ in ranges]
    assert starts == [0, 3]


def test_chunk_lines_merges_tiny_tail():
    lines = ["def a():", "    pass", "", "def b():", "    pass", "    return 0"]
    ranges = chunk_lines(lines, min_tokens=2, max_tokens=3)
    last_start, last_end = ranges[-1]
    assert last_end == len(lines) - 1


def test_chunk_lines_empty():
    assert chunk_lines([], min_tokens=1, max_tokens=10) == []


def test_chunk_text_builds_chunks():
    text = "def a():\n    return 1\n\ndef b():\n    return 2\n"
    chunks = chunk_text(
        "test.py", text, language="py", source_type="code", min_tokens=1, max_tokens=3
    )
    assert len(chunks) == 2
    assert chunks[0].file_path == "test.py"
    assert chunks[0].language == "py"
    assert chunks[0].source_type == "code"
    assert chunks[0].start_line == 1
    assert chunks[0].content_hash == content_hash(chunks[0].content)
    assert isinstance(chunks[0], Chunk)


def test_chunk_text_base_line_shifts_and_chunk_ids():
    text = "# H\n\nBody text here\n"
    chunks = chunk_text(
        "doc.md",
        text,
        language="markdown",
        source_type="docs",
        min_tokens=1,
        max_tokens=1000,
        section_title="H",
        base_line=10,
    )
    assert chunks[0].start_line == 11
    assert chunks[0].end_line == 13
    assert make_chunk_id("doc.md", 11) == chunks[0].chunk_id
    assert chunks[0].section_title == "H"


def test_chunk_text_max_tokens_honored():
    text = "\n".join(f"line {i} xxxxxxxxxxxxxxxx" for i in range(200))
    chunks = chunk_text(
        "big.py", text, language="py", source_type="code", min_tokens=50, max_tokens=100
    )
    # whole-line granularity + min-token merge may overshoot max_tokens
    assert max(c.token_estimate for c in chunks) <= 2 * 100
    combined = "\n".join(c.content for c in chunks)
    assert "line 0" in combined and "line 199" in combined
    joined = "\n".join(c.content for c in chunks).replace("\n\n", "\n")
    assert "line 0" in joined and "line 199" in joined
