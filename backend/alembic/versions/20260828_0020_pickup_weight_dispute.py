"""Add pickup weight verification dispute (WIQ-V1-046).

Revision ID: 20260828_0020
Revises: 20260821_0019
Create Date: 2026-08-28

Introduces the ``pickup_disputes`` table that records a citizen's dispute of
the collector-reported weight. The dispute table is the durable, auditable
record of the dispute and the admin resolution outcome. The original
collector-measured weight on ``collector_assignments`` is never overwritten
by this change — the original measurement remains the historical record and
the admin's resolution (if any) is stored separately on the dispute row.

Also extends the ``PickupStatus`` string enum with ``disputed`` to capture
the explicit "weight disputed, awaiting admin review" lifecycle state. The
enum is stored as a string column so the change is purely additive at the
SQL level; no historical rows are mutated.
"""

from alembic import op
import sqlalchemy as sa


revision = "20260828_0020"
down_revision = "20260821_0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pickup_disputes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "request_id",
            sa.Integer(),
            sa.ForeignKey("pickup_requests.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "disputed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "resolution",
            sa.Enum("upheld", "corrected", name="disputeresolution", native_enum=False),
            nullable=True,
        ),
        sa.Column("resolved_weight_kg", sa.Float(), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column(
            "resolved_by_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(op.f("ix_pickup_disputes_id"), "pickup_disputes", ["id"], unique=False)
    op.create_index(
        op.f("ix_pickup_disputes_request_id"),
        "pickup_disputes",
        ["request_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_pickup_disputes_request_id"), table_name="pickup_disputes")
    op.drop_index(op.f("ix_pickup_disputes_id"), table_name="pickup_disputes")
    op.drop_table("pickup_disputes")
