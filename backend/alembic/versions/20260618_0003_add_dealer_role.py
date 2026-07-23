"""Add dealer role to users."""

from alembic import op
import sqlalchemy as sa

revision = "20260618_0003"
down_revision = "20260616_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    old_user_role = sa.Enum("citizen", "collector", "admin", name="userrole", native_enum=False)
    new_user_role = sa.Enum(
        "citizen", "collector", "dealer", "admin", name="userrole", native_enum=False
    )

    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "role",
            existing_type=old_user_role,
            type_=new_user_role,
            existing_nullable=False,
        )


def downgrade() -> None:
    old_user_role = sa.Enum("citizen", "collector", "admin", name="userrole", native_enum=False)
    new_user_role = sa.Enum(
        "citizen", "collector", "dealer", "admin", name="userrole", native_enum=False
    )

    op.execute("DELETE FROM users WHERE role = 'dealer'")

    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "role",
            existing_type=new_user_role,
            type_=old_user_role,
            existing_nullable=False,
        )
