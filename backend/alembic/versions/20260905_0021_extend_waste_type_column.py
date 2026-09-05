"""Extend pickup_request waste_type column to VARCHAR(100).

Revision ID: 20260905_0021
Revises: 20260828_0020
Create Date: 2026-09-05

Fixes a schema defect where the pickup_requests.waste_type column was
created with VARCHAR(10) instead of VARCHAR(100) as defined in the
initial migration. The model PickupRequest.waste_type maps to String(100)
and the API schema enforces max_length=100, so the column must support
100-character values.
"""

from alembic import op
import sqlalchemy as sa

revision = "20260905_0021"
down_revision = "20260828_0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "pickup_requests",
        "waste_type",
        existing_type=sa.String(length=10),
        type_=sa.String(length=100),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "pickup_requests",
        "waste_type",
        existing_type=sa.String(length=100),
        type_=sa.String(length=10),
        existing_nullable=False,
    )
