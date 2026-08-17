"""PR review agent schema

Revision ID: 0002_review
Revises: 0001_initial
Create Date: 2026-08-05

Adds: review_sessions, review_findings, review_evidence (Phase 2 PR Review Agent).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_review"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "review_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("delivery_id", sa.String(length=64), nullable=True),
        sa.Column("correlation_id", sa.String(length=128), nullable=True),
        sa.Column("repo_full_name", sa.String(length=256), nullable=False),
        sa.Column("pr_number", sa.Integer(), nullable=False),
        sa.Column("branch", sa.String(length=256), nullable=True),
        sa.Column("base_branch", sa.String(length=256), nullable=True),
        sa.Column("commit_sha", sa.String(length=64), nullable=True),
        sa.Column("author", sa.String(length=128), nullable=True),
        sa.Column("title", sa.String(length=512), nullable=True),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("findings_count", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("metrics_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("delivery_id", name="uq_review_sessions_delivery_id"),
    )
    op.create_index("ix_review_sessions_delivery_id", "review_sessions", ["delivery_id"])
    op.create_index("ix_review_sessions_correlation_id", "review_sessions", ["correlation_id"])
    op.create_index("ix_review_sessions_repo_full_name", "review_sessions", ["repo_full_name"])
    op.create_index("ix_review_sessions_pr_number", "review_sessions", ["pr_number"])

    op.create_table(
        "review_findings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "session_id",
            sa.Integer(),
            sa.ForeignKey("review_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rule_id", sa.String(length=64), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("file_path", sa.String(length=512), nullable=False),
        sa.Column("start_line", sa.Integer(), nullable=False),
        sa.Column("end_line", sa.Integer(), nullable=False),
        sa.Column("snippet", sa.Text(), nullable=True),
        sa.Column("suggestion", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("related_adrs_json", sa.Text(), nullable=True),
        sa.Column("related_files_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_review_findings_session_id", "review_findings", ["session_id"])
    op.create_index("ix_review_findings_category", "review_findings", ["category"])
    op.create_index("ix_review_findings_severity", "review_findings", ["severity"])
    op.create_index("ix_review_findings_file_path", "review_findings", ["file_path"])

    op.create_table(
        "review_evidence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "session_id",
            sa.Integer(),
            sa.ForeignKey("review_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "finding_id",
            sa.Integer(),
            sa.ForeignKey("review_findings.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("kind", sa.String(length=24), nullable=False),
        sa.Column("reference", sa.String(length=512), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
    )
    op.create_index("ix_review_evidence_session_id", "review_evidence", ["session_id"])
    op.create_index("ix_review_evidence_finding_id", "review_evidence", ["finding_id"])


def downgrade() -> None:
    op.drop_index("ix_review_evidence_finding_id", table_name="review_evidence")
    op.drop_index("ix_review_evidence_session_id", table_name="review_evidence")
    op.drop_table("review_evidence")
    op.drop_index("ix_review_findings_file_path", table_name="review_findings")
    op.drop_index("ix_review_findings_severity", table_name="review_findings")
    op.drop_index("ix_review_findings_category", table_name="review_findings")
    op.drop_index("ix_review_findings_session_id", table_name="review_findings")
    op.drop_table("review_findings")
    op.drop_index("ix_review_sessions_pr_number", table_name="review_sessions")
    op.drop_index("ix_review_sessions_repo_full_name", table_name="review_sessions")
    op.drop_index("ix_review_sessions_correlation_id", table_name="review_sessions")
    op.drop_index("ix_review_sessions_delivery_id", table_name="review_sessions")
    op.drop_table("review_sessions")
