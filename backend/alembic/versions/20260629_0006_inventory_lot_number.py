"""Add human-readable lot number to inventory lots."""

from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20260629_0006"
down_revision = "20260620_0005"
branch_labels = None
depends_on = None


inventory_lots = sa.table(
    "inventory_lots",
    sa.column("id", sa.Integer()),
    sa.column("lot_number", sa.String(length=40)),
    sa.column("created_at", sa.DateTime(timezone=True)),
)


def _build_backfill_lot_number(created_at: datetime | None, lot_id: int) -> str:
    year = (
        created_at.year
        if created_at is not None
        else datetime.now(timezone.utc).year
    )
    return f"LOT-{year:04d}-{lot_id:06d}"


def _backfill(bind) -> None:
    rows = bind.execute(
        sa.select(
            inventory_lots.c.id,
            inventory_lots.c.created_at,
        )
        .where(inventory_lots.c.lot_number.is_(None))
        .order_by(inventory_lots.c.id)
    ).fetchall()

    for row in rows:
        bind.execute(
            sa.update(inventory_lots)
            .where(inventory_lots.c.id == row.id)
            .values(
                lot_number=_build_backfill_lot_number(
                    row.created_at,
                    row.id,
                )
            )
        )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    columns = {
        column["name"]
        for column in inspector.get_columns("inventory_lots")
    }

    indexes = {
        index["name"]
        for index in inspector.get_indexes("inventory_lots")
    }

    # ------------------------------------------------------------------
    # Add column only if missing
    # ------------------------------------------------------------------

    if "lot_number" not in columns:
        op.add_column(
            "inventory_lots",
            sa.Column(
                "lot_number",
                sa.String(length=40),
                nullable=True,
            ),
        )

    # ------------------------------------------------------------------
    # Backfill existing rows
    # ------------------------------------------------------------------

    _backfill(bind)

    # ------------------------------------------------------------------
    # Make NOT NULL if possible
    # ------------------------------------------------------------------

    with op.batch_alter_table("inventory_lots") as batch_op:
        batch_op.alter_column(
            "lot_number",
            existing_type=sa.String(length=40),
            nullable=False,
        )

    # ------------------------------------------------------------------
    # Create unique index only if missing
    # ------------------------------------------------------------------

    index_name = op.f("ix_inventory_lots_lot_number")

    if index_name not in indexes:
        op.create_index(
            index_name,
            "inventory_lots",
            ["lot_number"],
            unique=True,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    indexes = {
        index["name"]
        for index in inspector.get_indexes("inventory_lots")
    }

    index_name = op.f("ix_inventory_lots_lot_number")

    if index_name in indexes:
        op.drop_index(index_name, table_name="inventory_lots")

    columns = {
        column["name"]
        for column in inspector.get_columns("inventory_lots")
    }

    if "lot_number" in columns:
        with op.batch_alter_table("inventory_lots") as batch_op:
            batch_op.drop_column("lot_number")
