"""Dealer profile approval workflow.

Extends dealer_profiles with the dealer onboarding fields and the
draft/submitted/approved/rejected approval workflow, replaces the old
verification_status column, and adds a dealer_profile_events table that
records the approval history timeline.
"""

from alembic import op
import sqlalchemy as sa

revision = "20260801_0010"
down_revision = "1697652c68bf"
branch_labels = None
depends_on = None

APPROVAL_ENUM = sa.Enum(
    "draft",
    "submitted",
    "approved",
    "rejected",
    name="dealerapprovalstatus",
    native_enum=False,
)


def upgrade() -> None:
    APPROVAL_ENUM.create(bind=op.get_bind(), checkfirst=True)
    approval_status = APPROVAL_ENUM

    with op.batch_alter_table("dealer_profiles") as batch_op:
        batch_op.add_column(sa.Column("email", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("state", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("postal_code", sa.String(length=12), nullable=True))
        batch_op.add_column(sa.Column("business_type", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("profile_image", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("description", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("rejection_reason", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column("is_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False)
        )
        batch_op.add_column(
            sa.Column(
                "approval_status",
                approval_status,
                server_default="draft",
                nullable=False,
            )
        )
        batch_op.create_index("ix_dealer_profiles_approval_status", ["approval_status"])

    # Backfill: copy legacy pincode into postal_code and map the old
    # verification_status values onto the new approval workflow states.
    op.execute("UPDATE dealer_profiles SET postal_code = pincode")
    op.execute("""
        UPDATE dealer_profiles
        SET approval_status = CASE verification_status
            WHEN 'approved' THEN 'approved'
            WHEN 'rejected' THEN 'rejected'
            ELSE 'submitted'
        END
        """)

    with op.batch_alter_table("dealer_profiles") as batch_op:
        batch_op.create_index("ix_dealer_profiles_gst_number", ["gst_number"], unique=True)
        batch_op.create_index("ix_dealer_profiles_license_number", ["license_number"], unique=True)
        batch_op.drop_column("pincode")
        batch_op.drop_column("verification_status")

    op.create_table(
        "dealer_profile_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "profile_id",
            sa.Integer(),
            sa.ForeignKey("dealer_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "actor_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", approval_status, nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index(
        op.f("ix_dealer_profile_events_id"), "dealer_profile_events", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_dealer_profile_events_profile_id"),
        "dealer_profile_events",
        ["profile_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dealer_profile_events_actor_user_id"),
        "dealer_profile_events",
        ["actor_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dealer_profile_events_status"),
        "dealer_profile_events",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dealer_profile_events_created_at"),
        "dealer_profile_events",
        ["created_at"],
        unique=False,
    )

    op.execute("""
        INSERT INTO dealer_profile_events (profile_id, actor_user_id, status, note, created_at)
        SELECT id, user_id,
            CASE approval_status
                WHEN 'approved' THEN 'approved'
                WHEN 'rejected' THEN 'rejected'
                ELSE 'submitted'
            END,
            CASE approval_status
                WHEN 'approved' THEN 'Profile approved.'
                WHEN 'rejected' THEN 'Profile rejected.'
                ELSE 'Profile submitted for review.'
            END,
            created_at
        FROM dealer_profiles
        """)


def downgrade() -> None:
    op.drop_index(op.f("ix_dealer_profile_events_created_at"), table_name="dealer_profile_events")
    op.drop_index(op.f("ix_dealer_profile_events_status"), table_name="dealer_profile_events")
    op.drop_index(
        op.f("ix_dealer_profile_events_actor_user_id"), table_name="dealer_profile_events"
    )
    op.drop_index(op.f("ix_dealer_profile_events_profile_id"), table_name="dealer_profile_events")
    op.drop_index(op.f("ix_dealer_profile_events_id"), table_name="dealer_profile_events")
    op.drop_table("dealer_profile_events")

    verification_status = sa.Enum(
        "pending", "approved", "rejected", name="dealerverificationstatus", native_enum=False
    )
    verification_status.create(bind=op.get_bind(), checkfirst=True)

    with op.batch_alter_table("dealer_profiles") as batch_op:
        batch_op.add_column(sa.Column("pincode", sa.String(length=12), nullable=True, index=True))
        batch_op.add_column(
            sa.Column(
                "verification_status",
                verification_status,
                server_default="pending",
                nullable=False,
            )
        )

    op.execute("UPDATE dealer_profiles SET pincode = postal_code")
    op.execute("""
        UPDATE dealer_profiles
        SET verification_status = CASE approval_status
            WHEN 'approved' THEN 'approved'
            WHEN 'rejected' THEN 'rejected'
            ELSE 'pending'
        END
        """)

    with op.batch_alter_table("dealer_profiles") as batch_op:
        batch_op.drop_index("ix_dealer_profiles_approval_status")
        batch_op.drop_index("ix_dealer_profiles_gst_number")
        batch_op.drop_index("ix_dealer_profiles_license_number")
        batch_op.drop_column("approval_status")
        batch_op.drop_column("is_verified")
        batch_op.drop_column("rejection_reason")
        batch_op.drop_column("description")
        batch_op.drop_column("profile_image")
        batch_op.drop_column("business_type")
        batch_op.drop_column("postal_code")
        batch_op.drop_column("state")
        batch_op.drop_column("email")
