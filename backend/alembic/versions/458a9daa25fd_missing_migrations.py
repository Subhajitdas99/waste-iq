"""missing_migrations"""

revision = '458a9daa25fd'
down_revision = '20260629_0008'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa



def upgrade() -> None:
    # dealer_profiles
    with op.batch_alter_table('dealer_profiles') as batch_op:
        batch_op.drop_index('ix_dealer_profiles_user_id')
        batch_op.create_index('ix_dealer_profiles_user_id', ['user_id'], unique=True)

    # inventory_lot_events
    with op.batch_alter_table('inventory_lot_events') as batch_op:
        batch_op.alter_column('event_type',
               existing_type=sa.VARCHAR(length=14),
               type_=sa.Enum('created', 'updated', 'status_changed', 'archived', 'restored', 'reserved', 'reservation_expired', name='inventoryloteventtype', native_enum=False),
               existing_nullable=False)

    # pickup_requests
    with op.batch_alter_table('pickup_requests') as batch_op:
        batch_op.alter_column('photo_url', new_column_name='image_url', existing_type=sa.Text(), existing_nullable=True)
        batch_op.add_column(sa.Column('category', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('confidence', sa.Float(), nullable=True))
        batch_op.alter_column('status',
               existing_type=sa.VARCHAR(length=9),
               type_=sa.Enum('pending', 'accepted', 'on_the_way', 'collected', 'completed', 'cancelled', name='pickupstatus', native_enum=False),
               existing_nullable=False,
               existing_server_default=sa.text("'pending'"))


def downgrade() -> None:
    # pickup_requests
    with op.batch_alter_table('pickup_requests') as batch_op:
        batch_op.alter_column('status',
               existing_type=sa.Enum('pending', 'accepted', 'on_the_way', 'collected', 'completed', 'cancelled', name='pickupstatus', native_enum=False),
               type_=sa.VARCHAR(length=9),
               existing_nullable=False,
               existing_server_default=sa.text("'pending'"))
        batch_op.drop_column('confidence')
        batch_op.drop_column('category')
        batch_op.alter_column('image_url', new_column_name='photo_url', existing_type=sa.Text(), existing_nullable=True)

    # inventory_lot_events
    with op.batch_alter_table('inventory_lot_events') as batch_op:
        batch_op.alter_column('event_type',
               existing_type=sa.Enum('created', 'updated', 'status_changed', 'archived', 'restored', 'reserved', 'reservation_expired', name='inventoryloteventtype', native_enum=False),
               type_=sa.VARCHAR(length=14),
               existing_nullable=False)

    # dealer_profiles
    with op.batch_alter_table('dealer_profiles') as batch_op:
        batch_op.drop_index('ix_dealer_profiles_user_id')
        batch_op.create_index('ix_dealer_profiles_user_id', ['user_id'], unique=False)
