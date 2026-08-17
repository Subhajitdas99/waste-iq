"""Add the created_at server default to notifications.

Revision 20260803_0013 created the notifications table with a NOT NULL
created_at column but forgot the server_default that the Notification
model declares (server_default=func.now()). On PostgreSQL this raises
"null value in column created_at violates not-null constraint" and on
SQLite "NOT NULL constraint failed: notifications.created_at" because
SQLAlchemy correctly treats the column as server-generated and omits it
from INSERT statements.

This migration repairs existing databases so the database generates
created_at, matching the model and fresh-database schema. Fresh databases
already receive the fixed schema directly from the edited 20260803_0013.
"""

from alembic import op
import sqlalchemy as sa

revision = "20260804_0014"
down_revision = "20260803_0013"
branch_labels = None
depends_on = None


def _cleanup_sqlite_batch_table(table_name: str) -> None:
    if op.get_bind().dialect.name != "sqlite":
        return

    op.execute(sa.text(f'DROP TABLE IF EXISTS "_alembic_tmp_{table_name}"'))


def upgrade() -> None:
    if op.get_bind().dialect.name == "sqlite":
        _cleanup_sqlite_batch_table("notifications")
        with op.batch_alter_table("notifications") as batch_op:
            batch_op.alter_column(
                "created_at",
                existing_type=sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                existing_nullable=False,
            )
    else:
        op.alter_column(
            "notifications",
            "created_at",
            existing_type=sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            existing_nullable=False,
        )


def downgrade() -> None:
    if op.get_bind().dialect.name == "sqlite":
        _cleanup_sqlite_batch_table("notifications")
        with op.batch_alter_table("notifications") as batch_op:
            batch_op.alter_column(
                "created_at",
                existing_type=sa.DateTime(timezone=True),
                server_default=None,
                existing_nullable=False,
            )
    else:
        op.alter_column(
            "notifications",
            "created_at",
            existing_type=sa.DateTime(timezone=True),
            server_default=None,
            existing_nullable=False,
        )
