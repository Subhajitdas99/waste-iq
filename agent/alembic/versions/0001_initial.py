"""initial schema for the agent service

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-04

Creates: agent_runs, audit_log (Phase 0) and indexed_files, chunks,
embedding_cache, repository_snapshots (Phase 1 Repository Context Service).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("delivery_id", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("event_action", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("delivery_id", name="uq_agent_runs_delivery_id"),
    )
    op.create_index("ix_agent_runs_delivery_id", "agent_runs", ["delivery_id"])

    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("delivery_id", sa.String(length=64), nullable=False),
        sa.Column("actor", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_log_delivery_id", "audit_log", ["delivery_id"])

    op.create_table(
        "indexed_files",
        sa.Column("path", sa.String(length=512), primary_key=True),
        sa.Column("language", sa.String(length=32), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("modified_at", sa.Float(), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("last_indexed_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("chunk_id", sa.String(length=64), nullable=False),
        sa.Column("file_path", sa.String(length=512), nullable=False),
        sa.Column("start_line", sa.Integer(), nullable=False),
        sa.Column("end_line", sa.Integer(), nullable=False),
        sa.Column("section_title", sa.String(length=256), nullable=True),
        sa.Column("language", sa.String(length=32), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("token_estimate", sa.Integer(), nullable=False),
        sa.UniqueConstraint("chunk_id", name="uq_chunks_chunk_id"),
    )
    op.create_index("ix_chunks_chunk_id", "chunks", ["chunk_id"])
    op.create_index("ix_chunks_file_path", "chunks", ["file_path"])
    op.create_index("ix_chunks_content_hash", "chunks", ["content_hash"])

    op.create_table(
        "embedding_cache",
        sa.Column("content_hash", sa.String(length=64), primary_key=True),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column("vector_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "repository_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("repository_snapshots")
    op.drop_table("embedding_cache")
    op.drop_index("ix_chunks_content_hash", table_name="chunks")
    op.drop_index("ix_chunks_file_path", table_name="chunks")
    op.drop_index("ix_chunks_chunk_id", table_name="chunks")
    op.drop_table("chunks")
    op.drop_table("indexed_files")
    op.drop_index("ix_audit_log_delivery_id", table_name="audit_log")
    op.drop_table("audit_log")
    op.drop_index("ix_agent_runs_delivery_id", table_name="agent_runs")
    op.drop_table("agent_runs")
