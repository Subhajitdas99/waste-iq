from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    delivery_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    event_action: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    assistant: Mapped[str | None] = mapped_column(String(64), nullable=True)
    outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class AuditLogEntry(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    delivery_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    actor: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class IndexedFile(Base):
    """Per-file index metadata for incremental indexing (Repository Context Service)."""

    __tablename__ = "indexed_files"

    path: Mapped[str] = mapped_column(String(512), primary_key=True)
    language: Mapped[str] = mapped_column(String(32), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    modified_at: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    last_indexed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ChunkRecord(Base):
    """Derived chunks produced from indexed files."""

    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chunk_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    section_title: Mapped[str | None] = mapped_column(String(256), nullable=True)
    language: Mapped[str] = mapped_column(String(32), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, default="code")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    token_estimate: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class EmbeddingCacheEntry(Base):
    """Embedding cache keyed by content hash — unchanged content is never re-embedded."""

    __tablename__ = "embedding_cache"

    content_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    vector_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RepositorySnapshotEntry(Base):
    """Latest repository snapshot fetched from GitHub (single row, JSON payload)."""

    __tablename__ = "repository_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ReviewSession(Base):
    """A single PR review run (Phase 2 PR Review Agent)."""

    __tablename__ = "review_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    delivery_id: Mapped[str | None] = mapped_column(
        String(64), unique=True, nullable=True, index=True
    )
    correlation_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    repo_full_name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    pr_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    branch: Mapped[str | None] = mapped_column(String(256), nullable=True)
    base_branch: Mapped[str | None] = mapped_column(String(256), nullable=True)
    commit_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    author: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source: Mapped[str] = mapped_column(String(16), nullable=False, default="api")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="completed")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    findings_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metrics_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class ReviewFindingRow(Base):
    """A single review finding produced for a PR review session."""

    __tablename__ = "review_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("review_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rule_id: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggestion: Mapped[str] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    related_adrs_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_files_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ReviewEvidenceRow(Base):
    """Repository evidence backing a review finding (grounding / anti-hallucination)."""

    __tablename__ = "review_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("review_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    finding_id: Mapped[int | None] = mapped_column(
        ForeignKey("review_findings.id", ondelete="CASCADE"), nullable=True, index=True
    )
    kind: Mapped[str] = mapped_column(String(24), nullable=False)
    reference: Mapped[str] = mapped_column(String(512), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
