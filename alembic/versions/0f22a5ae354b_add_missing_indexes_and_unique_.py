"""add missing indexes and unique constraints

Revision ID: 0f22a5ae354b
Revises: ac1342c19af3
Create Date: 2026-08-02 15:21:11.344949

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0f22a5ae354b'
down_revision: Union[str, Sequence[str], None] = 'ac1342c19af3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('Favorites', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_favorite_user_rest', ['user_id', 'restaurant_id'])
    op.create_index(op.f('ix_packages_restaurant_id'), 'packages', ['restaurant_id'], unique=False)
    op.create_index(op.f('ix_restaurants_owner_id'), 'restaurants', ['owner_id'], unique=False)
    op.create_index(op.f('ix_subscriptions_user_id'), 'subscriptions', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_subscriptions_user_id'), table_name='subscriptions')
    op.drop_index(op.f('ix_restaurants_owner_id'), table_name='restaurants')
    op.drop_index(op.f('ix_packages_restaurant_id'), table_name='packages')
    with op.batch_alter_table('Favorites', schema=None) as batch_op:
        batch_op.drop_constraint('uq_favorite_user_rest', type_='unique')
    op.drop_index(op.f('ix_Favorites_user_id'), table_name='Favorites')