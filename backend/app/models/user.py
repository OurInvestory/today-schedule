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
    
    # 프로필 정보
    name = Column(String(100), nullable=True)
    school = Column(String(200), nullable=True)
    department = Column(String(200), nullable=True)
    grade = Column(String(20), nullable=True)
    
    # 관계 설정
    schedules = relationship("Schedule", back_populates="user", cascade="all, delete-orphan")
    lectures = relationship("Lecture", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    sub_tasks = relationship("SubTask", back_populates="user", cascade="all, delete-orphan")