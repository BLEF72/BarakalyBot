"""add available_date to packages

Revision ID: ac1342c19af3
Revises: 793a755d4cd2
Create Date: 2026-08-01 17:39:09.677177

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ac1342c19af3'
down_revision: Union[str, Sequence[str], None] = '793a755d4cd2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('packages', sa.Column('available_date', sa.Date(), nullable=True))
    op.create_index(op.f('ix_packages_available_date'), 'packages', ['available_date'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_packages_available_date'), table_name='packages')
    op.drop_column('packages', 'available_date')