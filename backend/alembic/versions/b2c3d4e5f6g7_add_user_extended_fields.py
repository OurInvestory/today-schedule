"""
User 모델 통합 마이그레이션 - 프로필 + RBAC + OAuth 필드 추가

Revision ID: b2c3d4e5f6g7
Revises: 8df204b49245
Create Date: 2026-01-31
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, None] = '8df204b49245'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 프로필 정보 필드
    op.add_column('user', sa.Column('name', sa.String(100), nullable=True))
    op.add_column('user', sa.Column('school', sa.String(200), nullable=True))
    op.add_column('user', sa.Column('department', sa.String(200), nullable=True))
    op.add_column('user', sa.Column('grade', sa.String(20), nullable=True))
    
    # RBAC 관련 필드
    op.add_column('user', sa.Column('role', sa.String(20), nullable=False, server_default='user'))
    
    # JWT 리프레시 토큰
    op.add_column('user', sa.Column('refresh_token', sa.String(500), nullable=True))
    
    # OAuth2.0 소셜 로그인
    op.add_column('user', sa.Column('oauth_provider', sa.String(50), nullable=True))
    op.add_column('user', sa.Column('oauth_id', sa.String(255), nullable=True))
    
    # 보안 관련
    op.add_column('user', sa.Column('login_attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('user', sa.Column('locked_until', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('user', 'locked_until')
    op.drop_column('user', 'login_attempts')
    op.drop_column('user', 'oauth_id')
    op.drop_column('user', 'oauth_provider')
    op.drop_column('user', 'refresh_token')
    op.drop_column('user', 'role')
    op.drop_column('user', 'grade')
    op.drop_column('user', 'department')
    op.drop_column('user', 'school')
    op.drop_column('user', 'name')
