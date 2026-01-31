from app.db.database import Base

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Boolean, Date, Time, Text
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship

import uuid


class User(Base):
    __tablename__ = "user"
    
    user_id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    create_at = Column(DateTime, nullable=False)
    update_at = Column(DateTime, nullable=False)
    
    # RBAC 관련 컬럼
    role = Column(String(20), nullable=False, default="user")  # guest, user, premium, admin
    
    # JWT 리프레시 토큰
    refresh_token = Column(String(500), nullable=True)
    
    # OAuth2.0 소셜 로그인
    oauth_provider = Column(String(50), nullable=True)  # google, kakao, naver
    oauth_id = Column(String(255), nullable=True)
    
    # 보안 관련
    login_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime, nullable=True)
    
    # 관계 설정
    schedules = relationship("Schedule", back_populates="user", cascade="all, delete-orphan")
    lectures = relationship("Lecture", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    sub_tasks = relationship("SubTask", back_populates="user", cascade="all, delete-orphan")