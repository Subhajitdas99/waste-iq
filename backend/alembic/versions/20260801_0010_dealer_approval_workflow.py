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


def _cleanup_sqlite_batch_table(table_name: str) -> None:
    if op.get_bind().dialect.name != "sqlite":
        return

    op.execute(sa.text(f'DROP TABLE IF EXISTS "_alembic_tmp_{table_name}"'))


def _has_table(table_name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table_name)


def _column_names(table_name: str) -> set[str]:
    if not _has_table(table_name):
        return set()

    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table_name)}


def _index_names(table_name: str) -> set[str]:
    if not _has_table(table_name):
        return set()

    return {
        index["name"]
        for index in sa.inspect(op.get_bind()).get_indexes(table_name)
        if index["name"] is not None
    }


def upgrade() -> None:
    APPROVAL_ENUM.create(bind=op.get_bind(), checkfirst=True)
    approval_status = APPROVAL_ENUM

    profile_columns = _column_names("dealer_profiles")
    profile_indexes = _index_names("dealer_profiles")
    if (
        "email" not in profile_columns
        or "state" not in profile_columns
        or "postal_code" not in profile_columns
        or "business_type" not in profile_columns
        or "profile_image" not in profile_columns
        or "description" not in profile_columns
        or "rejection_reason" not in profile_columns
        or "is_verified" not in profile_columns
        or "approval_status" not in profile_columns
        or "ix_dealer_profiles_approval_status" not in profile_indexes
    ):
        _cleanup_sqlite_batch_table("dealer_profiles")
        with op.batch_alter_table("dealer_profiles") as batch_op:
            if "email" not in profile_columns:
                batch_op.add_column(sa.Column("email", sa.String(length=255), nullable=True))
            if "state" not in profile_columns:
                batch_op.add_column(sa.Column("state", sa.String(length=100), nullable=True))
            if "postal_code" not in profile_columns:
                batch_op.add_column(sa.Column("postal_code", sa.String(length=12), nullable=True))
            if "business_type" not in profile_columns:
                batch_op.add_column(sa.Column("business_type", sa.String(length=50), nullable=True))
            if "profile_image" not in profile_columns:
                batch_op.add_column(
                    sa.Column("profile_image", sa.String(length=500), nullable=True)
                )
            if "description" not in profile_columns:
                batch_op.add_column(sa.Column("description", sa.Text(), nullable=True))
            if "rejection_reason" not in profile_columns:
                batch_op.add_column(sa.Column("rejection_reason", sa.Text(), nullable=True))
            if "is_verified" not in profile_columns:
                batch_op.add_column(
                    sa.Column(
                        "is_verified",
                        sa.Boolean(),
                        server_default=sa.text("false"),
                        nullable=False,
                    )
                )
            if "approval_status" not in profile_columns:
                batch_op.add_column(
                    sa.Column(
                        "approval_status",
                        approval_status,
                        server_default="draft",
                        nullable=False,
                    )
                )
            if "ix_dealer_profiles_approval_status" not in profile_indexes:
                batch_op.create_index("ix_dealer_profiles_approval_status", ["approval_status"])

    # Backfill: copy legacy pincode into postal_code and map the old
    # verification_status values onto the new approval workflow states.
    profile_columns = _column_names("dealer_profiles")
    if {"postal_code", "pincode"}.issubset(profile_columns):
        op.execute("UPDATE dealer_profiles SET postal_code = pincode")
    if {"approval_status", "verification_status"}.issubset(profile_columns):
        op.execute("""
            UPDATE dealer_profiles
            SET approval_status = CASE verification_status
                WHEN 'approved' THEN 'approved'
                WHEN 'rejected' THEN 'rejected'
                ELSE 'submitted'
            END
            """)

    profile_columns = _column_names("dealer_profiles")
    profile_indexes = _index_names("dealer_profiles")
    if (
        "ix_dealer_profiles_gst_number" not in profile_indexes
        or "ix_dealer_profiles_license_number" not in profile_indexes
        or "ix_dealer_profiles_pincode" in profile_indexes
        or "ix_dealer_profiles_verification_status" in profile_indexes
        or "pincode" in profile_columns
        or "verification_status" in profile_columns
    ):
        _cleanup_sqlite_batch_table("dealer_profiles")
        with op.batch_alter_table("dealer_profiles") as batch_op:
            if "ix_dealer_profiles_pincode" in profile_indexes:
                batch_op.drop_index("ix_dealer_profiles_pincode")
            if "ix_dealer_profiles_verification_status" in profile_indexes:
                batch_op.drop_index("ix_dealer_profiles_verification_status")
            if "ix_dealer_profiles_gst_number" not in profile_indexes:
                batch_op.create_index("ix_dealer_profiles_gst_number", ["gst_number"], unique=True)
            if "ix_dealer_profiles_license_number" not in profile_indexes:
                batch_op.create_index(
                    "ix_dealer_profiles_license_number",
                    ["license_number"],
                    unique=True,
                )
            if "pincode" in profile_columns:
                batch_op.drop_column("pincode")
            if "verification_status" in profile_columns:
                batch_op.drop_column("verification_status")

    if not _has_table("dealer_profile_events"):
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

    event_indexes = _index_names("dealer_profile_events")
    if op.f("ix_dealer_profile_events_id") not in event_indexes:
        op.create_index(
            op.f("ix_dealer_profile_events_id"),
            "dealer_profile_events",
            ["id"],
            unique=False,
        )
    if op.f("ix_dealer_profile_events_profile_id") not in event_indexes:
        op.create_index(
            op.f("ix_dealer_profile_events_profile_id"),
            "dealer_profile_events",
            ["profile_id"],
            unique=False,
        )
    if op.f("ix_dealer_profile_events_actor_user_id") not in event_indexes:
        op.create_index(
            op.f("ix_dealer_profile_events_actor_user_id"),
            "dealer_profile_events",
            ["actor_user_id"],
            unique=False,
        )
    if op.f("ix_dealer_profile_events_status") not in event_indexes:
        op.create_index(
            op.f("ix_dealer_profile_events_status"),
            "dealer_profile_events",
            ["status"],
            unique=False,
        )
    if op.f("ix_dealer_profile_events_created_at") not in event_indexes:
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
        WHERE NOT EXISTS (
            SELECT 1
            FROM dealer_profile_events
            WHERE dealer_profile_events.profile_id = dealer_profiles.id
        )
        """)


def downgrade() -> None:
    if _has_table("dealer_profile_events"):
        event_indexes = _index_names("dealer_profile_events")
        if op.f("ix_dealer_profile_events_created_at") in event_indexes:
            op.drop_index(
                op.f("ix_dealer_profile_events_created_at"),
                table_name="dealer_profile_events",
            )
        if op.f("ix_dealer_profile_events_status") in event_indexes:
            op.drop_index(
                op.f("ix_dealer_profile_events_status"), table_name="dealer_profile_events"
            )
        if op.f("ix_dealer_profile_events_actor_user_id") in event_indexes:
            op.drop_index(
                op.f("ix_dealer_profile_events_actor_user_id"),
                table_name="dealer_profile_events",
            )
        if op.f("ix_dealer_profile_events_profile_id") in event_indexes:
            op.drop_index(
                op.f("ix_dealer_profile_events_profile_id"),
                table_name="dealer_profile_events",
            )
        if op.f("ix_dealer_profile_events_id") in event_indexes:
            op.drop_index(op.f("ix_dealer_profile_events_id"), table_name="dealer_profile_events")
        op.drop_table("dealer_profile_events")

    verification_status = sa.Enum(
        "pending", "approved", "rejected", name="dealerverificationstatus", native_enum=False
    )
    verification_status.create(bind=op.get_bind(), checkfirst=True)

    profile_columns = _column_names("dealer_profiles")
    if "pincode" not in profile_columns or "verification_status" not in profile_columns:
        _cleanup_sqlite_batch_table("dealer_profiles")
        with op.batch_alter_table("dealer_profiles") as batch_op:
            if "pincode" not in profile_columns:
                batch_op.add_column(
                    sa.Column("pincode", sa.String(length=12), nullable=True, index=True)
                )
            if "verification_status" not in profile_columns:
                batch_op.add_column(
                    sa.Column(
                        "verification_status",
                        verification_status,
                        server_default="pending",
                        nullable=False,
                    )
                )

    profile_columns = _column_names("dealer_profiles")
    if {"postal_code", "pincode"}.issubset(profile_columns):
        op.execute("UPDATE dealer_profiles SET pincode = postal_code")
    if {"approval_status", "verification_status"}.issubset(profile_columns):
        op.execute("""
            UPDATE dealer_profiles
            SET verification_status = CASE approval_status
                WHEN 'approved' THEN 'approved'
                WHEN 'rejected' THEN 'rejected'
                ELSE 'pending'
            END
            """)

    profile_columns = _column_names("dealer_profiles")
    profile_indexes = _index_names("dealer_profiles")
    if (
        "ix_dealer_profiles_approval_status" in profile_indexes
        or "ix_dealer_profiles_gst_number" in profile_indexes
        or "ix_dealer_profiles_license_number" in profile_indexes
        or "approval_status" in profile_columns
        or "is_verified" in profile_columns
        or "rejection_reason" in profile_columns
        or "description" in profile_columns
        or "profile_image" in profile_columns
        or "business_type" in profile_columns
        or "postal_code" in profile_columns
        or "state" in profile_columns
        or "email" in profile_columns
        or "ix_dealer_profiles_pincode" not in profile_indexes
        or "ix_dealer_profiles_verification_status" not in profile_indexes
    ):
        _cleanup_sqlite_batch_table("dealer_profiles")
        with op.batch_alter_table("dealer_profiles") as batch_op:
            if "ix_dealer_profiles_approval_status" in profile_indexes:
                batch_op.drop_index("ix_dealer_profiles_approval_status")
            if "ix_dealer_profiles_gst_number" in profile_indexes:
                batch_op.drop_index("ix_dealer_profiles_gst_number")
            if "ix_dealer_profiles_license_number" in profile_indexes:
                batch_op.drop_index("ix_dealer_profiles_license_number")
            if "approval_status" in profile_columns:
                batch_op.drop_column("approval_status")
            if "is_verified" in profile_columns:
                batch_op.drop_column("is_verified")
            if "rejection_reason" in profile_columns:
                batch_op.drop_column("rejection_reason")
            if "description" in profile_columns:
                batch_op.drop_column("description")
            if "profile_image" in profile_columns:
                batch_op.drop_column("profile_image")
            if "business_type" in profile_columns:
                batch_op.drop_column("business_type")
            if "postal_code" in profile_columns:
                batch_op.drop_column("postal_code")
            if "state" in profile_columns:
                batch_op.drop_column("state")
            if "email" in profile_columns:
                batch_op.drop_column("email")
            if "ix_dealer_profiles_pincode" not in profile_indexes:
                batch_op.create_index("ix_dealer_profiles_pincode", ["pincode"])
            if "ix_dealer_profiles_verification_status" not in profile_indexes:
                batch_op.create_index(
                    "ix_dealer_profiles_verification_status",
                    ["verification_status"],
                )
