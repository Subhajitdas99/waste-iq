"""Add the notifications table.

Creates the notifications table used by the centralized notification &
communication system. Each row targets a single user (`user_id`), records a
human-readable title/message, the typed event that produced it, an optional
deep-link to the related page, and read state (`unread`/`read`).
"""

from alembic import op
import sqlalchemy as sa

revision = "20260803_0013"
down_revision = "20260803_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    notification_type_enum = sa.Enum(
        "pickup_created",
        "pickup_accepted",
        "pickup_started",
        "pickup_collected",
        "pickup_completed",
        "dealer_profile_submitted",
        "dealer_profile_approved",
        "dealer_profile_rejected",
        "inventory_created",
        "inventory_reserved",
        "reservation_cancelled",
        "reservation_expired",
        "inventory_purchased",
        "admin_announcement",
        "system",
        name="notificationtype",
    )
    notification_status_enum = sa.Enum(
        "unread",
        "read",
        name="notificationstatus",
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("type", notification_type_enum, nullable=False),
        sa.Column("status", notification_status_enum, nullable=False, server_default="unread"),
        sa.Column("link", sa.String(length=255), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_notifications_id", "notifications", ["id"], unique=False)
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"], unique=False)
    op.create_index("ix_notifications_type", "notifications", ["type"], unique=False)
    op.create_index("ix_notifications_status", "notifications", ["status"], unique=False)
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"], unique=False)
    op.create_index(
        "ix_notifications_user_created", "notifications", ["user_id", "created_at"], unique=False
    )
    op.create_index(
        "ix_notifications_user_status", "notifications", ["user_id", "status"], unique=False
    )
    op.create_index(
        "ix_notifications_user_type", "notifications", ["user_id", "type"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_notifications_user_type", table_name="notifications")
    op.drop_index("ix_notifications_user_status", table_name="notifications")
    op.drop_index("ix_notifications_user_created", table_name="notifications")
    op.drop_index("ix_notifications_created_at", table_name="notifications")
    op.drop_index("ix_notifications_status", table_name="notifications")
    op.drop_index("ix_notifications_type", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_index("ix_notifications_id", table_name="notifications")
    op.drop_table("notifications")

    sa.Enum(name="notificationtype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="notificationstatus").drop(op.get_bind(), checkfirst=True)
