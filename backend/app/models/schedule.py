from app.db.database import Base

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Boolean, Date, Time, Text
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship

import uuid


class Schedule(Base):
    __tablename__ = "schedule"

    schedule_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("user.user_id"), nullable=False)
    type = Column(String(255), nullable=True)   # task (AI로 Sub task가 생성되는 것), evnet (그 외)
    title = Column(String(255), nullable=False)
    category = Column(String(50), nullable=True)    # class, assignment, exam, team, activity, other
    color = Column(String(20), nullable=True)       # 일정 색상 (hex 코드)
    start_at = Column(DateTime, nullable=True)
    end_at = Column(DateTime, nullable=False)
    priority_score = Column(Integer, default=1, nullable=False)     
    original_text = Column(Text, nullable=True)
    update_text = Column(Text, nullable=True)
    estimated_minute = Column(Integer, nullable=True)    # 분 단위
    source = Column(String(50), default='manual', nullable=True)  # manual, google

    # 관계 설정
    user = relationship("User", back_populates="schedules")
    sub_tasks = relationship("SubTask", back_populates="schedule", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="schedule", cascade="all, delete-orphan")