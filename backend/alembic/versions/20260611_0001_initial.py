"""Initial Waste-IQ schema."""

from alembic import op
import sqlalchemy as sa

revision = "20260611_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    user_role = sa.Enum("citizen", "collector", "admin", name="userrole", native_enum=False)
    pickup_status = sa.Enum("pending", "accepted", "completed", "cancelled", name="pickupstatus", native_enum=False)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_phone"), "users", ["phone"], unique=True)
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)

    op.create_table(
        "pickup_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("waste_type", sa.String(length=100), nullable=False),
        sa.Column("photo_url", sa.Text(), nullable=True),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("status", pickup_status, server_default="pending", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index(op.f("ix_pickup_requests_id"), "pickup_requests", ["id"], unique=False)
    op.create_index(op.f("ix_pickup_requests_status"), "pickup_requests", ["status"], unique=False)
    op.create_index(op.f("ix_pickup_requests_user_id"), "pickup_requests", ["user_id"], unique=False)

    op.create_table(
        "collector_assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_id", sa.Integer(), sa.ForeignKey("pickup_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("collector_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.UniqueConstraint("request_id"),
    )
    op.create_index(op.f("ix_collector_assignments_id"), "collector_assignments", ["id"], unique=False)
    op.create_index(op.f("ix_collector_assignments_collector_id"), "collector_assignments", ["collector_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_collector_assignments_collector_id"), table_name="collector_assignments")
    op.drop_index(op.f("ix_collector_assignments_id"), table_name="collector_assignments")
    op.drop_table("collector_assignments")

    op.drop_index(op.f("ix_pickup_requests_user_id"), table_name="pickup_requests")
    op.drop_index(op.f("ix_pickup_requests_status"), table_name="pickup_requests")
    op.drop_index(op.f("ix_pickup_requests_id"), table_name="pickup_requests")
    op.drop_table("pickup_requests")

    op.drop_index(op.f("ix_users_role"), table_name="users")
    op.drop_index(op.f("ix_users_phone"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")
