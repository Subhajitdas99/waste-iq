"""Create dealer profile and verification workflow."""

from alembic import op
import sqlalchemy as sa

revision = "20260619_0004"
down_revision = "20260618_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    verification_status = sa.Enum(
        "pending", "approved", "rejected", name="dealerverificationstatus", native_enum=False
    )

    op.create_table(
        "dealer_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("business_name", sa.String(length=160), nullable=False),
        sa.Column("owner_name", sa.String(length=120), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("pincode", sa.String(length=12), nullable=False),
        sa.Column("gst_number", sa.String(length=30), nullable=True),
        sa.Column("license_number", sa.String(length=50), nullable=True),
        sa.Column("materials_accepted", sa.JSON(), nullable=False),
        sa.Column(
            "verification_status", verification_status, server_default="pending", nullable=False
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_dealer_profiles_id"), "dealer_profiles", ["id"], unique=False)
    op.create_index(
        op.f("ix_dealer_profiles_user_id"), "dealer_profiles", ["user_id"], unique=False
    )
    op.create_index(op.f("ix_dealer_profiles_city"), "dealer_profiles", ["city"], unique=False)
    op.create_index(
        op.f("ix_dealer_profiles_pincode"), "dealer_profiles", ["pincode"], unique=False
    )
    op.create_index(
        op.f("ix_dealer_profiles_verification_status"),
        "dealer_profiles",
        ["verification_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_dealer_profiles_verification_status"), table_name="dealer_profiles")
    op.drop_index(op.f("ix_dealer_profiles_pincode"), table_name="dealer_profiles")
    op.drop_index(op.f("ix_dealer_profiles_city"), table_name="dealer_profiles")
    op.drop_index(op.f("ix_dealer_profiles_user_id"), table_name="dealer_profiles")
    op.drop_index(op.f("ix_dealer_profiles_id"), table_name="dealer_profiles")
    op.drop_table("dealer_profiles")
