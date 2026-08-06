from app.context.repository_indexer import (
    SENSITIVE_PATH_PARTS,
    RepositoryIndexer,
    file_checksum,
    to_vector_points,
)
from app.context.models import Chunk


class _FakeStore:
    def __init__(self):
        self.calls = []

    def get_existing(self, *a, **k):
        return {}

    def delete_chunks_for_files(self, paths):
        return []

    def get_chunks_for_file(self, path):
        return []

    def indexed_files(self):
        return set()

    def upsert_chunk(self, chunk):
        self.calls.append(("upsert", chunk))


def _make_indexer(tmp_path):
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "main.py").write_text("def hello():\n    return 1\n")
    (tmp_path / "app" / "utils.go").write_text("package main\nfunc Run() {}\n")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "dep.js").write_text("const x = 1;\n")
    (tmp_path / "README.md").write_text("# Title\nbody\n")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "roadmap.md").write_text("# Roadmap\n## Q1\n- Milestone 1\n")
    (tmp_path / ".env").write_text("SECRET=value\n")
    (tmp_path / "app" / "credentials.json").write_text('{"password": "x"}')
    (tmp_path / "notes.txt").write_text("plain text")
    return RepositoryIndexer(
        store=_FakeStore(),
        root=tmp_path,
        ignored_dirs=["node_modules", ".git", "__pycache__"],
        ignored_files=[".env"],
        min_tokens=10,
        max_tokens=1000,
    )


def test_iter_files_skips_ignored_and_sensitive(tmp_path):
    indexer = _make_indexer(tmp_path)
    files = indexer.iter_files()
    rels = sorted(f.relative_to(tmp_path).as_posix() for f in files)
    assert "app/main.py" in rels
    assert "app/utils.go" in rels
    assert "README.md" in rels
    assert "docs/roadmap.md" in rels
    assert "node_modules/dep.js" not in rels
    assert ".env" not in rels
    assert "app/credentials.json" not in rels
    assert "notes.txt" not in rels


def test_iter_files_empty_repo(tmp_path):
    indexer = RepositoryIndexer(_FakeStore(), tmp_path, [], [], 10, 1000)
    assert indexer.iter_files() == []


def test_is_sensitive(tmp_path):
    indexer = _make_indexer(tmp_path)
    assert indexer.is_sensitive(tmp_path / "config" / "secrets.yaml")
    assert indexer.is_sensitive(tmp_path / ".env.production")
    assert not indexer.is_sensitive(tmp_path / "app" / "main.py")


def test_index_file_code(tmp_path):
    indexer = _make_indexer(tmp_path)
    chunks = indexer.index_file(tmp_path / "app" / "utils.go")
    assert all(c.source_type == "code" for c in chunks)
    assert chunks[0].language == "go"


def test_index_file_docs(tmp_path):
    indexer = _make_indexer(tmp_path)
    chunks = indexer.index_file(tmp_path / "docs" / "roadmap.md")
    assert all(c.source_type == "docs" for c in chunks)
    assert chunks[0].language == "markdown"


def test_index_includes_bytes(tmp_path):
    indexer = _make_indexer(tmp_path)
    chunks, stats = indexer.index()
    assert stats["files"] >= 3
    assert chunks
    assert stats["bytes"] > 0


def test_to_vector_points_matches_chunks():
    chunks = [
        Chunk(
            chunk_id="c1",
            file_path="a.py",
            start_line=1,
            end_line=3,
            language="py",
            source_type="code",
            content="def foo():\n    pass",
            content_hash="h1",
            token_estimate=4,
        )
    ]
    points = to_vector_points(chunks, [[0.1, 0.2]])
    assert points[0].chunk_id == "c1"
    assert points[0].vector == [0.1, 0.2]
    assert points[0].keywords


def test_file_checksum_stable_and_sensitive(tmp_path):
    path = tmp_path / "sample.py"
    path.write_text("x = 1\n")
    first = file_checksum(path)
    second = file_checksum(path)
    assert first == second
    assert len(first) == 64
    path.write_text("x = 2\n")
    assert file_checksum(path) != first


def test_sensitive_parts_cover_common_secrets():
    for part in ("secrets", "credentials", ".env", "pem", "password", "token"):
        assert part in SENSITIVE_PATH_PARTS
