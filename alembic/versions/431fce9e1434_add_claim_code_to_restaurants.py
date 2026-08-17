"""add claim_code to restaurants

Revision ID: 431fce9e1434
Revises: 0afd327e7491
Create Date: 2026-08-15 15:51:45.805307

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '431fce9e1434'
down_revision: Union[str, Sequence[str], None] = '0afd327e7491'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('restaurants', sa.Column('claim_code', sa.String(length=10), nullable=True))
    with op.batch_alter_table('restaurants', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_restaurants_claim_code', ['claim_code'])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('restaurants', schema=None) as batch_op:
        batch_op.drop_constraint('uq_restaurants_claim_code', type_='unique')
    op.drop_column('restaurants', 'claim_code')