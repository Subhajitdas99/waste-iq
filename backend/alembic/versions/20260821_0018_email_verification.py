"""Add email verification to users (WIQ-V1-014).

Revision ID: 20260821_0018
Revises: 20260821_0017
Create Date: 2026-08-21

Adds the nullable email_verified_at column so accounts can start unverified
and transition once a signed verification token is presented. The column is
additive and non-destructive; existing accounts keep their current state
(NULL) and remain able to log in.
"""

from alembic import op
import sqlalchemy as sa

revision = "20260821_0018"
down_revision = "20260821_0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "email_verified_at")