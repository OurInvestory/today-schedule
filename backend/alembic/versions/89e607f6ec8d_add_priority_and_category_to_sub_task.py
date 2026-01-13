"""add_priority_and_category_to_sub_task

Revision ID: 89e607f6ec8d
Revises: 2233a32004a5
Create Date: 2026-01-13 15:54:30.317259

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '89e607f6ec8d'
down_revision: Union[str, Sequence[str], None] = '2233a32004a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add priority and category columns to sub_task table."""
    # Make schedule_id nullable first (if not already done)
    op.alter_column('sub_task', 'schedule_id',
                    existing_type=sa.String(36),
                    nullable=True)
    
    # Add priority column
    op.add_column('sub_task', sa.Column('priority', sa.String(20), nullable=True, server_default='medium'))
    
    # Add category column  
    op.add_column('sub_task', sa.Column('category', sa.String(50), nullable=True, server_default='other'))


def downgrade() -> None:
    """Remove priority and category columns from sub_task table."""
    op.drop_column('sub_task', 'category')
    op.drop_column('sub_task', 'priority')
    
    # Revert schedule_id to not nullable
    op.alter_column('sub_task', 'schedule_id',
                    existing_type=sa.String(36),
                    nullable=False)
