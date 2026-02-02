"""Add is_recurring to income and expenses

Revision ID: 5f3a0c10d3e5
Revises: a87508b6f04d
Create Date: 2026-01-06 23:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f3a0c10d3e5'
down_revision: Union[str, Sequence[str], None] = 'a87508b6f04d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_recurring to income_entries
    op.add_column('income_entries', sa.Column('is_recurring', sa.Boolean(), server_default='false', nullable=False))
    # Add is_recurring to expense_items
    op.add_column('expense_items', sa.Column('is_recurring', sa.Boolean(), server_default='false', nullable=False))


def downgrade() -> None:
    op.drop_column('expense_items', 'is_recurring')
    op.drop_column('income_entries', 'is_recurring')
