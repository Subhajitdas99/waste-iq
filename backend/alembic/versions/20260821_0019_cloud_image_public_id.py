"""Add image_public_id to pickup_requests (WIQ-V1-020).

Revision ID: 20260821_0019
Revises: 20260821_0018
Create Date: 2026-08-21

Stores the Cloudinary public_id (or future provider asset identifier) of the
uploaded waste photo so the exact stored asset can be deleted when a pickup
request is cancelled. Nullable and additive; existing rows are unaffected.
The public_id is never exposed in API responses and is not a credential.
"""

from alembic import op
import sqlalchemy as sa

revision = "20260821_0019"
down_revision = "20260821_0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "pickup_requests",
        sa.Column("image_public_id", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("pickup_requests", "image_public_id")
