"""Inventory marketplace foundation: material categories, pricing rules, inventory lots, lot events."""

from alembic import op
import sqlalchemy as sa

revision = "20260620_0005"
down_revision = "20260619_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inventory_lot_status = sa.Enum(
        "available",
        "reserved",
        "sold",
        name="inventorylotstatus",
        native_enum=False,
    )
    inventory_lot_event_type = sa.Enum(
        "created",
        "updated",
        "status_changed",
        "archived",
        name="inventoryloteventtype",
        native_enum=False,
    )

    # ─── material_categories ────────────────────────────────────────────────
    op.create_table(
        "material_categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("display_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_material_categories_id"), "material_categories", ["id"], unique=False)
    op.create_index(op.f("ix_material_categories_code"), "material_categories", ["code"], unique=True)
    op.create_index(op.f("ix_material_categories_name"), "material_categories", ["name"], unique=False)
    op.create_index(op.f("ix_material_categories_is_active"), "material_categories", ["is_active"], unique=False)
    op.create_index(op.f("ix_material_categories_display_order"), "material_categories", ["display_order"], unique=False)

    # ─── pricing_rules ───────────────────────────────────────────────────────
    op.create_table(
        "pricing_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "material_category_id",
            sa.Integer(),
            sa.ForeignKey("material_categories.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("unit_price_per_kg", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency_code", sa.String(length=3), server_default="INR", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index(op.f("ix_pricing_rules_id"), "pricing_rules", ["id"], unique=False)
    op.create_index(op.f("ix_pricing_rules_material_category_id"), "pricing_rules", ["material_category_id"], unique=False)
    op.create_index(op.f("ix_pricing_rules_city"), "pricing_rules", ["city"], unique=False)
    op.create_index(op.f("ix_pricing_rules_is_active"), "pricing_rules", ["is_active"], unique=False)
    op.create_index(op.f("ix_pricing_rules_effective_from"), "pricing_rules", ["effective_from"], unique=False)
    op.create_index(op.f("ix_pricing_rules_created_by"), "pricing_rules", ["created_by"], unique=False)
    op.create_index(op.f("ix_pricing_rules_updated_by"), "pricing_rules", ["updated_by"], unique=False)

    # ─── inventory_lots ──────────────────────────────────────────────────────
    op.create_table(
        "inventory_lots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "pickup_request_id",
            sa.Integer(),
            sa.ForeignKey("pickup_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("citizen_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("collector_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column(
            "material_category_id",
            sa.Integer(),
            sa.ForeignKey("material_categories.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("material_description", sa.Text(), nullable=True),
        sa.Column("weight_kg", sa.Float(), nullable=False),
        sa.Column("unit_price_per_kg_snapshot", sa.Numeric(10, 2), nullable=False),
        sa.Column("total_listed_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "pricing_rule_id",
            sa.Integer(),
            sa.ForeignKey("pricing_rules.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("source_city", sa.String(length=100), nullable=False),
        sa.Column("source_address_snapshot", sa.Text(), nullable=True),
        sa.Column("status", inventory_lot_status, server_default="available", nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("pickup_request_id"),
        sa.CheckConstraint("weight_kg > 0", name="ck_inventory_lots_weight_positive"),
        sa.CheckConstraint("unit_price_per_kg_snapshot >= 0", name="ck_inventory_lots_unit_price_non_negative"),
        sa.CheckConstraint("total_listed_amount >= 0", name="ck_inventory_lots_total_amount_non_negative"),
    )
    op.create_index(op.f("ix_inventory_lots_id"), "inventory_lots", ["id"], unique=False)
    op.create_index(op.f("ix_inventory_lots_pickup_request_id"), "inventory_lots", ["pickup_request_id"], unique=True)
    op.create_index(op.f("ix_inventory_lots_citizen_id"), "inventory_lots", ["citizen_id"], unique=False)
    op.create_index(op.f("ix_inventory_lots_collector_id"), "inventory_lots", ["collector_id"], unique=False)
    op.create_index(op.f("ix_inventory_lots_material_category_id"), "inventory_lots", ["material_category_id"], unique=False)
    op.create_index(op.f("ix_inventory_lots_pricing_rule_id"), "inventory_lots", ["pricing_rule_id"], unique=False)
    op.create_index(op.f("ix_inventory_lots_source_city"), "inventory_lots", ["source_city"], unique=False)
    op.create_index(op.f("ix_inventory_lots_status"), "inventory_lots", ["status"], unique=False)
    op.create_index(op.f("ix_inventory_lots_archived_at"), "inventory_lots", ["archived_at"], unique=False)
    op.create_index(op.f("ix_inventory_lots_created_by"), "inventory_lots", ["created_by"], unique=False)
    op.create_index(op.f("ix_inventory_lots_updated_by"), "inventory_lots", ["updated_by"], unique=False)
    op.create_index(op.f("ix_inventory_lots_created_at"), "inventory_lots", ["created_at"], unique=False)

    # ─── inventory_lot_events ────────────────────────────────────────────────
    op.create_table(
        "inventory_lot_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "inventory_lot_id",
            sa.Integer(),
            sa.ForeignKey("inventory_lots.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", inventory_lot_event_type, nullable=False),
        sa.Column("previous_status", inventory_lot_status, nullable=True),
        sa.Column("new_status", inventory_lot_status, nullable=True),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event_notes", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index(op.f("ix_inventory_lot_events_id"), "inventory_lot_events", ["id"], unique=False)
    op.create_index(
        op.f("ix_inventory_lot_events_inventory_lot_id"), "inventory_lot_events", ["inventory_lot_id"], unique=False
    )
    op.create_index(op.f("ix_inventory_lot_events_event_type"), "inventory_lot_events", ["event_type"], unique=False)
    op.create_index(
        op.f("ix_inventory_lot_events_actor_user_id"), "inventory_lot_events", ["actor_user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_inventory_lot_events_actor_user_id"), table_name="inventory_lot_events")
    op.drop_index(op.f("ix_inventory_lot_events_event_type"), table_name="inventory_lot_events")
    op.drop_index(op.f("ix_inventory_lot_events_inventory_lot_id"), table_name="inventory_lot_events")
    op.drop_index(op.f("ix_inventory_lot_events_id"), table_name="inventory_lot_events")
    op.drop_table("inventory_lot_events")

    op.drop_index(op.f("ix_inventory_lots_created_at"), table_name="inventory_lots")
    op.drop_index(op.f("ix_inventory_lots_updated_by"), table_name="inventory_lots")
    op.drop_index(op.f("ix_inventory_lots_created_by"), table_name="inventory_lots")
    op.drop_index(op.f("ix_inventory_lots_archived_at"), table_name="inventory_lots")
    op.drop_index(op.f("ix_inventory_lots_status"), table_name="inventory_lots")
    op.drop_index(op.f("ix_inventory_lots_source_city"), table_name="inventory_lots")
    op.drop_index(op.f("ix_inventory_lots_pricing_rule_id"), table_name="inventory_lots")
    op.drop_index(op.f("ix_inventory_lots_material_category_id"), table_name="inventory_lots")
    op.drop_index(op.f("ix_inventory_lots_collector_id"), table_name="inventory_lots")
    op.drop_index(op.f("ix_inventory_lots_citizen_id"), table_name="inventory_lots")
    op.drop_index(op.f("ix_inventory_lots_pickup_request_id"), table_name="inventory_lots")
    op.drop_index(op.f("ix_inventory_lots_id"), table_name="inventory_lots")
    op.drop_table("inventory_lots")

    op.drop_index(op.f("ix_pricing_rules_updated_by"), table_name="pricing_rules")
    op.drop_index(op.f("ix_pricing_rules_created_by"), table_name="pricing_rules")
    op.drop_index(op.f("ix_pricing_rules_effective_from"), table_name="pricing_rules")
    op.drop_index(op.f("ix_pricing_rules_is_active"), table_name="pricing_rules")
    op.drop_index(op.f("ix_pricing_rules_city"), table_name="pricing_rules")
    op.drop_index(op.f("ix_pricing_rules_material_category_id"), table_name="pricing_rules")
    op.drop_index(op.f("ix_pricing_rules_id"), table_name="pricing_rules")
    op.drop_table("pricing_rules")

    op.drop_index(op.f("ix_material_categories_display_order"), table_name="material_categories")
    op.drop_index(op.f("ix_material_categories_is_active"), table_name="material_categories")
    op.drop_index(op.f("ix_material_categories_name"), table_name="material_categories")
    op.drop_index(op.f("ix_material_categories_code"), table_name="material_categories")
    op.drop_index(op.f("ix_material_categories_id"), table_name="material_categories")
    op.drop_table("material_categories")