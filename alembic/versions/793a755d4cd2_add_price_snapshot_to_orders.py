"""add price snapshot to orders

Revision ID: 793a755d4cd2
Revises: 0ea90d4d4014
Create Date: 2026-08-01 16:22:47.348094

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '793a755d4cd2'
down_revision: Union[str, Sequence[str], None] = '0ea90d4d4014'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('orders', sa.Column('price', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('orders', 'price')