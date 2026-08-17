"""Add citizen pickup request detail fields (Sprint 5).

Adds estimated_weight_kg, preferred_time and notes to pickup_requests
so citizens can schedule and describe pickups at request time.
"""

from alembic import op
import sqlalchemy as sa

revision = "20260731_0009"
down_revision = "458a9daa25fd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "pickup_requests",
        sa.Column("estimated_weight_kg", sa.Float(), nullable=True),
    )
    op.add_column(
        "pickup_requests",
        sa.Column("preferred_time", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "pickup_requests",
        sa.Column("notes", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("pickup_requests", "notes")
    op.drop_column("pickup_requests", "preferred_time")
    op.drop_column("pickup_requests", "estimated_weight_kg")
