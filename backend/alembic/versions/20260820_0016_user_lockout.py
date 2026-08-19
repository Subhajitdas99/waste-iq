"""Add account lockout columns to users (WIQ-V1-017).

Revision ID: 20260820_0016
Revises: 20260819_0015
Create Date: 2026-08-20

Adds failed_login_count and locked_until to the users table so repeated
failed login attempts can lock an account for a configurable cooldown.
Both columns are additive and non-destructive.
"""

from alembic import op
import sqlalchemy as sa

revision = "20260820_0016"
down_revision = "20260819_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "failed_login_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "locked_until",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_login_count")