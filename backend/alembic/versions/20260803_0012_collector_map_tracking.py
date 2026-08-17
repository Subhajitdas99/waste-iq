"""Add collector live map location tracking.

Creates the collector_locations table (latest reported location, one row
per collector) and the collector_location_history append-only table that
records every location update for audit and tracking purposes.
"""

from alembic import op
import sqlalchemy as sa

revision = "20260803_0012"
down_revision = "20260801_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "collector_locations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("collector_id", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("accuracy", sa.Float(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["collector_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_collector_locations_id", "collector_locations", ["id"], unique=False)
    op.create_index(
        "ix_collector_locations_collector_id",
        "collector_locations",
        ["collector_id"],
        unique=True,
    )

    op.create_table(
        "collector_location_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("collector_id", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("accuracy", sa.Float(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["collector_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_collector_location_history_id",
        "collector_location_history",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_collector_location_history_collector_id",
        "collector_location_history",
        ["collector_id"],
        unique=False,
    )
    op.create_index(
        "ix_collector_location_history_recorded_at",
        "collector_location_history",
        ["recorded_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_collector_location_history_recorded_at",
        table_name="collector_location_history",
    )
    op.drop_index(
        "ix_collector_location_history_collector_id",
        table_name="collector_location_history",
    )
    op.drop_index("ix_collector_location_history_id", table_name="collector_location_history")
    op.drop_table("collector_location_history")

    op.drop_index("ix_collector_locations_collector_id", table_name="collector_locations")
    op.drop_index("ix_collector_locations_id", table_name="collector_locations")
    op.drop_table("collector_locations")
