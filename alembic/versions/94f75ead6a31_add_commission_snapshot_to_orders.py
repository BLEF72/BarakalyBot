"""add commission snapshot to orders

Revision ID: 94f75ead6a31
Revises: 7cb966428596
Create Date: 2026-08-02 22:02:02.371138

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '94f75ead6a31'
down_revision: Union[str, Sequence[str], None] = '7cb966428596'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('orders', sa.Column('commission', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('orders', 'commission')