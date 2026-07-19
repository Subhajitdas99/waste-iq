"""Add dealer inventory reservation fields."""

from alembic import op
import sqlalchemy as sa

revision = "20260629_0008"
down_revision = "20260629_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("inventory_lots") as batch_op:
        # Add new columns
        batch_op.add_column(
            sa.Column(
                "reserved_by_dealer_id",
                sa.Integer(),
                nullable=True,
            )
        )

        batch_op.add_column(
            sa.Column(
                "reserved_at",
                sa.DateTime(timezone=True),
                nullable=True,
            )
        )

        batch_op.add_column(
            sa.Column(
                "reservation_expires_at",
                sa.DateTime(timezone=True),
                nullable=True,
            )
        )

        # Create a NAMED foreign key (required for SQLite batch mode)
        batch_op.create_foreign_key(
            "fk_inventory_lots_reserved_by_dealer",
            "users",
            ["reserved_by_dealer_id"],
            ["id"],
            ondelete="SET NULL",
        )

        # Indexes
        batch_op.create_index(
            "ix_inventory_lots_reserved_by_dealer_id",
            ["reserved_by_dealer_id"],
            unique=False,
        )

        batch_op.create_index(
            "ix_inventory_lots_reservation_expires_at",
            ["reservation_expires_at"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("inventory_lots") as batch_op:
        batch_op.drop_index("ix_inventory_lots_reservation_expires_at")
        batch_op.drop_index("ix_inventory_lots_reserved_by_dealer_id")

        batch_op.drop_constraint(
            "fk_inventory_lots_reserved_by_dealer",
            type_="foreignkey",
        )

        batch_op.drop_column("reservation_expires_at")
        batch_op.drop_column("reserved_at")
        batch_op.drop_column("reserved_by_dealer_id")
