"""add color column to schedule

Revision ID: a1b2c3d4e5f6
Revises: b2c3d4e5f6g7
Create Date: 2026-02-02 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add color column to schedule table
    op.add_column('schedule', sa.Column('color', sa.String(20), nullable=True))


def downgrade() -> None:
    # Remove color column from schedule table
    op.drop_column('schedule', 'color')
