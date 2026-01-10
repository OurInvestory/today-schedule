from app.db.database import Base

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Boolean, Date, Time, Text
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship

import uuid


class SubTask(Base):
    __tablename__ = "sub_task"

    sub_task_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("user.user_id"), nullable=False)
    schedule_id = Column(String(36), ForeignKey("schedule.schedule_id"), nullable=False)
    title = Column(String(255), nullable=False)
    date = Column(Date, nullable=False)
    estimated_time = Column(Integer, nullable=False)    # 분 단위
    is_done = Column(Boolean, default=False, nullable=False)
    update_text = Column(Text, nullable=True)

    # 관계 설정
    user = relationship("User", back_populates="sub_tasks")
    schedule = relationship("Schedule", back_populates="sub_tasks")