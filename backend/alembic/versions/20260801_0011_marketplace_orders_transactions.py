"""Add marketplace orders and transactions.

Creates the marketplace_orders and marketplace_transactions tables that
record dealer purchases and the transaction history (reservation,
cancellation, purchase, reservation expiry), and widens
inventory_lot_events.event_type to fit the new reservation_cancelled
event type.
"""

from alembic import op
import sqlalchemy as sa

revision = "20260801_0011"
down_revision = "20260801_0010"
branch_labels = None
depends_on = None


def _cleanup_sqlite_batch_table(table_name: str) -> None:
    if op.get_bind().dialect.name != "sqlite":
        return

    op.execute(sa.text(f'DROP TABLE IF EXISTS "_alembic_tmp_{table_name}"'))


def upgrade() -> None:
    op.create_table(
        "marketplace_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_number", sa.String(length=40), nullable=False),
        sa.Column("inventory_lot_id", sa.Integer(), nullable=False),
        sa.Column("dealer_id", sa.Integer(), nullable=False),
        sa.Column("quantity_kg", sa.Float(), nullable=False),
        sa.Column("unit_price_per_kg_snapshot", sa.Numeric(10, 2), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("quantity_kg > 0", name="ck_marketplace_orders_quantity_positive"),
        sa.CheckConstraint(
            "unit_price_per_kg_snapshot >= 0",
            name="ck_marketplace_orders_unit_price_non_negative",
        ),
        sa.CheckConstraint(
            "total_amount >= 0", name="ck_marketplace_orders_total_amount_non_negative"
        ),
        sa.ForeignKeyConstraint(["dealer_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["inventory_lot_id"], ["inventory_lots.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_marketplace_orders_id", "marketplace_orders", ["id"], unique=False)
    op.create_index(
        "ix_marketplace_orders_order_number",
        "marketplace_orders",
        ["order_number"],
        unique=True,
    )
    op.create_index(
        "ix_marketplace_orders_inventory_lot_id",
        "marketplace_orders",
        ["inventory_lot_id"],
        unique=True,
    )
    op.create_index(
        "ix_marketplace_orders_dealer_id", "marketplace_orders", ["dealer_id"], unique=False
    )
    op.create_index("ix_marketplace_orders_status", "marketplace_orders", ["status"], unique=False)
    op.create_index(
        "ix_marketplace_orders_created_at",
        "marketplace_orders",
        ["created_at"],
        unique=False,
    )

    op.create_table(
        "marketplace_transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("dealer_id", sa.Integer(), nullable=False),
        sa.Column("inventory_lot_id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("transaction_type", sa.String(length=24), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("quantity_kg", sa.Float(), nullable=False),
        sa.Column("unit_price_per_kg_snapshot", sa.Numeric(10, 2), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("quantity_kg > 0", name="ck_marketplace_transactions_quantity_positive"),
        sa.CheckConstraint(
            "unit_price_per_kg_snapshot >= 0",
            name="ck_marketplace_transactions_unit_price_non_negative",
        ),
        sa.CheckConstraint(
            "total_amount >= 0", name="ck_marketplace_transactions_total_amount_non_negative"
        ),
        sa.ForeignKeyConstraint(["dealer_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["inventory_lot_id"], ["inventory_lots.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["order_id"], ["marketplace_orders.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_marketplace_transactions_id",
        "marketplace_transactions",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_marketplace_transactions_dealer_id",
        "marketplace_transactions",
        ["dealer_id"],
        unique=False,
    )
    op.create_index(
        "ix_marketplace_transactions_inventory_lot_id",
        "marketplace_transactions",
        ["inventory_lot_id"],
        unique=False,
    )
    op.create_index(
        "ix_marketplace_transactions_order_id",
        "marketplace_transactions",
        ["order_id"],
        unique=False,
    )
    op.create_index(
        "ix_marketplace_transactions_transaction_type",
        "marketplace_transactions",
        ["transaction_type"],
        unique=False,
    )
    op.create_index(
        "ix_marketplace_transactions_status",
        "marketplace_transactions",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_marketplace_transactions_created_at",
        "marketplace_transactions",
        ["created_at"],
        unique=False,
    )

    _cleanup_sqlite_batch_table("inventory_lot_events")
    with op.batch_alter_table("inventory_lot_events") as batch_op:
        batch_op.alter_column(
            "event_type",
            existing_type=sa.String(length=14),
            type_=sa.String(length=32),
            existing_nullable=False,
        )


def downgrade() -> None:
    _cleanup_sqlite_batch_table("inventory_lot_events")
    with op.batch_alter_table("inventory_lot_events") as batch_op:
        batch_op.alter_column(
            "event_type",
            existing_type=sa.String(length=32),
            type_=sa.String(length=14),
            existing_nullable=False,
        )

    op.drop_index("ix_marketplace_transactions_created_at", table_name="marketplace_transactions")
    op.drop_index("ix_marketplace_transactions_status", table_name="marketplace_transactions")
    op.drop_index(
        "ix_marketplace_transactions_transaction_type", table_name="marketplace_transactions"
    )
    op.drop_index("ix_marketplace_transactions_order_id", table_name="marketplace_transactions")
    op.drop_index(
        "ix_marketplace_transactions_inventory_lot_id", table_name="marketplace_transactions"
    )
    op.drop_index("ix_marketplace_transactions_dealer_id", table_name="marketplace_transactions")
    op.drop_index("ix_marketplace_transactions_id", table_name="marketplace_transactions")
    op.drop_table("marketplace_transactions")

    op.drop_index("ix_marketplace_orders_created_at", table_name="marketplace_orders")
    op.drop_index("ix_marketplace_orders_status", table_name="marketplace_orders")
    op.drop_index("ix_marketplace_orders_dealer_id", table_name="marketplace_orders")
    op.drop_index("ix_marketplace_orders_inventory_lot_id", table_name="marketplace_orders")
    op.drop_index("ix_marketplace_orders_order_number", table_name="marketplace_orders")
    op.drop_index("ix_marketplace_orders_id", table_name="marketplace_orders")
    op.drop_table("marketplace_orders")
