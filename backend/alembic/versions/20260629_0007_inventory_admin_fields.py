"""Add admin inventory management fields."""

from alembic import op
import sqlalchemy as sa

revision = "20260629_0007"
down_revision = "20260629_0006"
branch_labels = None
depends_on = None


def _cleanup_sqlite_batch_table(table_name: str) -> None:
    if op.get_bind().dialect.name != "sqlite":
        return

    op.execute(sa.text(f'DROP TABLE IF EXISTS "_alembic_tmp_{table_name}"'))


def upgrade() -> None:
    visibility_enum = sa.Enum("visible", "hidden", name="inventorylotvisibility", native_enum=False)

    _cleanup_sqlite_batch_table("inventory_lots")
    with op.batch_alter_table("inventory_lots") as batch_op:
        batch_op.add_column(sa.Column("quality_grade", sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column("admin_notes", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "visibility",
                visibility_enum,
                nullable=False,
                server_default="visible",
            )
        )
        batch_op.add_column(sa.Column("archive_reason", sa.Text(), nullable=True))
        batch_op.create_index(
            op.f("ix_inventory_lots_quality_grade"), ["quality_grade"], unique=False
        )
        batch_op.create_index(op.f("ix_inventory_lots_visibility"), ["visibility"], unique=False)


def downgrade() -> None:
    _cleanup_sqlite_batch_table("inventory_lots")
    with op.batch_alter_table("inventory_lots") as batch_op:
        batch_op.drop_index(op.f("ix_inventory_lots_visibility"))
        batch_op.drop_index(op.f("ix_inventory_lots_quality_grade"))
        batch_op.drop_column("archive_reason")
        batch_op.drop_column("visibility")
        batch_op.drop_column("admin_notes")
        batch_op.drop_column("quality_grade")
