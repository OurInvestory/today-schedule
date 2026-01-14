from app.db.database import Base

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Boolean, Date, Time, Text
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship

import uuid


class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("user.user_id"), nullable=False)
    schedule_id = Column(String(36), ForeignKey("schedule.schedule_id"), nullable=True)  # 독립 알림 가능
    message = Column(String(500), nullable=False)
    notify_at = Column(DateTime, nullable=False)  # 알림 발송 시간
    is_sent = Column(Boolean, default=False, nullable=False)  # 발송 여부
    is_checked = Column(Boolean, default=False, nullable=False)  # 확인 여부

    # 관계 설정
    user = relationship("User", back_populates="notifications")
    schedule = relationship("Schedule", back_populates="notifications")