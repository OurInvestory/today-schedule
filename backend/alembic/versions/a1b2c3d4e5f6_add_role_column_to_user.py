"""Add role column to user table

Revision ID: a1b2c3d4e5f6
Revises: 8df204b49245
Create Date: 2026-01-31 12:00:00.000000

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
    # role 컬럼 추가 (기본값: 'user')
    op.add_column('user', sa.Column('role', sa.String(20), nullable=False, server_default='user'))
    
    # refresh_token 컬럼 추가 (JWT 리프레시 토큰 저장)
    op.add_column('user', sa.Column('refresh_token', sa.String(500), nullable=True))
    
    # oauth_provider 컬럼 추가 (소셜 로그인 제공자)
    op.add_column('user', sa.Column('oauth_provider', sa.String(50), nullable=True))
    
    # oauth_id 컬럼 추가 (소셜 로그인 ID)
    op.add_column('user', sa.Column('oauth_id', sa.String(255), nullable=True))
    
    # login_attempts 컬럼 추가 (로그인 시도 횟수)
    op.add_column('user', sa.Column('login_attempts', sa.Integer, nullable=False, server_default='0'))
    
    # locked_until 컬럼 추가 (계정 잠금 시간)
    op.add_column('user', sa.Column('locked_until', sa.DateTime, nullable=True))


def downgrade() -> None:
    op.drop_column('user', 'locked_until')
    op.drop_column('user', 'login_attempts')
    op.drop_column('user', 'oauth_id')
    op.drop_column('user', 'oauth_provider')
    op.drop_column('user', 'refresh_token')
    op.drop_column('user', 'role')
