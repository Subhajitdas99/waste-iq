"""Add citizen dashboard statuses and pickup request timeline."""

from alembic import op
import sqlalchemy as sa

revision = "20260616_0002"
down_revision = "20260611_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    old_pickup_status = sa.Enum("pending", "accepted", "completed", "cancelled", name="pickupstatus", native_enum=False)
    new_pickup_status = sa.Enum(
        "pending",
        "accepted",
        "on_the_way",
        "collected",
        "completed",
        "cancelled",
        name="pickupstatus",
        native_enum=False,
    )

    with op.batch_alter_table("pickup_requests") as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=old_pickup_status,
            type_=new_pickup_status,
            existing_nullable=False,
            existing_server_default="pending",
        )

    op.create_table(
        "pickup_request_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_id", sa.Integer(), sa.ForeignKey("pickup_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", new_pickup_status, nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index(op.f("ix_pickup_request_events_id"), "pickup_request_events", ["id"], unique=False)
    op.create_index(op.f("ix_pickup_request_events_request_id"), "pickup_request_events", ["request_id"], unique=False)
    op.create_index(op.f("ix_pickup_request_events_actor_id"), "pickup_request_events", ["actor_id"], unique=False)
    op.create_index(op.f("ix_pickup_request_events_status"), "pickup_request_events", ["status"], unique=False)

    op.execute(
        """
        INSERT INTO pickup_request_events (request_id, actor_id, status, note, created_at)
        SELECT id, user_id, 'pending', 'Pickup request created.', created_at
        FROM pickup_requests
        """
    )
    op.execute(
        """
        INSERT INTO pickup_request_events (request_id, actor_id, status, note, created_at)
        SELECT pr.id, ca.collector_id, 'accepted', 'Collector accepted the pickup request.', ca.accepted_at
        FROM pickup_requests pr
        JOIN collector_assignments ca ON ca.request_id = pr.id
        WHERE pr.status IN ('accepted', 'completed')
        """
    )
    op.execute(
        """
        INSERT INTO pickup_request_events (request_id, actor_id, status, note, created_at)
        SELECT pr.id, ca.collector_id, 'completed', 'Pickup completed.', COALESCE(ca.completed_at, pr.created_at)
        FROM pickup_requests pr
        JOIN collector_assignments ca ON ca.request_id = pr.id
        WHERE pr.status = 'completed'
        """
    )
    op.execute(
        """
        INSERT INTO pickup_request_events (request_id, actor_id, status, note, created_at)
        SELECT id, user_id, 'cancelled', 'Citizen cancelled the pickup request.', created_at
        FROM pickup_requests
        WHERE status = 'cancelled'
        """
    )


def downgrade() -> None:
    old_pickup_status = sa.Enum("pending", "accepted", "completed", "cancelled", name="pickupstatus", native_enum=False)
    new_pickup_status = sa.Enum(
        "pending",
        "accepted",
        "on_the_way",
        "collected",
        "completed",
        "cancelled",
        name="pickupstatus",
        native_enum=False,
    )

    op.drop_index(op.f("ix_pickup_request_events_status"), table_name="pickup_request_events")
    op.drop_index(op.f("ix_pickup_request_events_actor_id"), table_name="pickup_request_events")
    op.drop_index(op.f("ix_pickup_request_events_request_id"), table_name="pickup_request_events")
    op.drop_index(op.f("ix_pickup_request_events_id"), table_name="pickup_request_events")
    op.drop_table("pickup_request_events")

    op.execute("UPDATE pickup_requests SET status = 'accepted' WHERE status IN ('on_the_way', 'collected')")

    with op.batch_alter_table("pickup_requests") as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=new_pickup_status,
            type_=old_pickup_status,
            existing_nullable=False,
            existing_server_default="pending",
        )
