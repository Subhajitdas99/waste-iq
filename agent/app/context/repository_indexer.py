"""Repository indexer — walks the working tree, chunks, and stores.

Security: secrets and credentials files are NEVER embedded (explicit
deny-list), the repository snapshot payload is stored in SQLite only,
and chunk content is stored in SQLite (not the vector store payloads
may be exposed to later LLM context).
"""

from __future__ import annotations

from pathlib import Path

from app.context.chunker import chunk_text, content_hash
from app.context.documentation_parser import chunk_document
from app.context.interfaces import ChunkStore
from app.context.models import Chunk, VectorPoint
from app.context.tokenizer import make_keywords, subword_tokens

# Never index these paths — credentials/secrets/commercial files.
SENSITIVE_PATH_PARTS = (
    "secrets",
    "credentials",
    ".env",
    "id_rsa",
    "id_ed25519",
    "pem",
    "p12",
    "keystore",
    "password",
    "token",
    "secret",
)

CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".go",
    ".rs",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".rb",
    ".php",
    ".kt",
    ".swift",
    ".sql",
    ".sh",
}
DOC_EXTENSIONS = {".md", ".markdown", ".rst"}


class RepositoryIndexer:
    def __init__(
        self,
        store: ChunkStore,
        root: Path,
        ignored_dirs: list[str],
        ignored_files: list[str],
        min_tokens: int,
        max_tokens: int,
    ) -> None:
        self._store = store
        self._root = root
        self._ignored_dirs = set(ignored_dirs)
        self._ignored_files = set(ignored_files)
        self._min_tokens = min_tokens
        self._max_tokens = max_tokens

    @property
    def root(self) -> Path:
        return self._root

    def is_sensitive(self, path: Path) -> bool:
        rel = path.relative_to(self._root).as_posix()
        parts = [part.lower() for part in rel.split("/")]
        return any(any(seg in part for seg in SENSITIVE_PATH_PARTS) for part in parts)

    def iter_files(self) -> list[Path]:
        """All indexable files under root, sorted by relative path."""
        files: list[Path] = []
        for candidate in sorted(self._root.rglob("*")):
            if not candidate.is_file():
                continue
            if any(part in self._ignored_dirs for part in candidate.parts):
                continue
            if candidate.name in self._ignored_files:
                continue
            if self.is_sensitive(candidate):
                continue
            if candidate.suffix not in CODE_EXTENSIONS | DOC_EXTENSIONS:
                continue
            files.append(candidate)
        return files

    def index_file(self, path: Path, last_indexed_at: float | None = None) -> list[Chunk]:
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(self._root).as_posix()
        if path.suffix in DOC_EXTENSIONS:
            chunks = chunk_document(rel, text, self._min_tokens, self._max_tokens)
            for chunk in chunks:
                chunk.language = "markdown"
        else:
            language = path.suffix.lstrip(".") or "text"
            chunks = chunk_text(
                rel,
                text,
                language=language,
                source_type="code",
                min_tokens=self._min_tokens,
                max_tokens=self._max_tokens,
            )
        return chunks

    def index(self) -> tuple[list[Chunk], dict]:
        """Index the whole tree. Returns (chunks, stats)."""
        files = self.iter_files()
        chunks: list[Chunk] = []
        stats = {"files": len(files), "bytes": 0}
        for path in files:
            stats["bytes"] += path.stat().st_size
            chunks.extend(self.index_file(path))
        return chunks, stats


def to_vector_points(chunks: list[Chunk], vectors: list[list[float]]) -> list[VectorPoint]:
    points: list[VectorPoint] = []
    for chunk, vector in zip(chunks, vectors):
        from collections import Counter

        points.append(
            VectorPoint(
                chunk_id=chunk.chunk_id,
                file_path=chunk.file_path,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                section_title=chunk.section_title,
                language=chunk.language,
                source_type=chunk.source_type,
                vector=vector,
                keywords=make_keywords(chunk.content),
                subword_tokens=dict(Counter(subword_tokens(chunk.content))),
                path_tokens=list(set(subword_tokens(chunk.file_path))),
            )
        )
    return points


def file_checksum(path: Path) -> str:
    data = path.read_bytes()
    return content_hash(data.hex())


def chunk_requires_update(existing: Chunk, new: Chunk) -> bool:
    return existing.content_hash != new.content_hash or existing.end_line != new.end_line
