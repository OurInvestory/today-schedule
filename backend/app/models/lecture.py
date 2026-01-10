from app.db.database import Base

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Boolean, Date, Time, Text
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship

import uuid


class Lecture(Base):
    __tablename__ = "lecture"

    lecture_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("user.user_id"), nullable=False)
    title = Column(String(255), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    start_day = Column(Date, nullable=False)
    end_day = Column(Date, nullable=False)  # default = start_day로부터 16주 이후
    week = Column(String(50), nullable=False)     # 0 (월) - 6 (일)
    update_text = Column(Text, nullable=True)

    # 관계 설정
    user = relationship("User", back_populates="lectures")