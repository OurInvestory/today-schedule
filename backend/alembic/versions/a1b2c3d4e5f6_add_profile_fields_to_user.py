"""add profile fields to user

Revision ID: a1b2c3d4e5f6
Revises: 8df204b49245
Create Date: 2026-01-31 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '8df204b49245'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 프로필 필드 추가
    op.add_column('user', sa.Column('name', sa.String(100), nullable=True))
    op.add_column('user', sa.Column('school', sa.String(200), nullable=True))
    op.add_column('user', sa.Column('department', sa.String(200), nullable=True))
    op.add_column('user', sa.Column('grade', sa.String(20), nullable=True))


def downgrade() -> None:
    # 프로필 필드 제거
    op.drop_column('user', 'grade')
    op.drop_column('user', 'department')
    op.drop_column('user', 'school')
    op.drop_column('user', 'name')
