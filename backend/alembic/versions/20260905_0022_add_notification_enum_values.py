"""Add missing notification type enum values.

Revision ID: 20260905_0022
Revises: 20260905_0021
Create Date: 2026-09-05

Adds the missing enum values to the PostgreSQL notificationtype ENUM type:
- weight_recorded
- weight_confirmed
- weight_disputed
- dispute_resolved

These values were added to the NotificationType model but the corresponding
PostgreSQL ENUM type was never extended.
"""

from alembic import op

revision = "20260905_0022"
down_revision = "20260905_0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'weight_recorded'")
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'weight_confirmed'")
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'weight_disputed'")
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'dispute_resolved'")


def downgrade() -> None:
    pass
