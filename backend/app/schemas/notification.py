from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


# 알림 생성 요청
class CreateNotificationRequest(BaseModel):
    schedule_id: Optional[str] = Field(None, description="연결된 일정 ID (없으면 독립 알림)")
    schedule_title: Optional[str] = Field(None, description="일정 제목 (schedule_id 없을 때 검색용)")
    message: str = Field(..., description="알림 메시지")
    notify_at: datetime = Field(..., description="알림 발송 시간")
    minutes_before: Optional[int] = Field(None, description="일정 시작 N분 전 (notify_at 자동 계산용)")


# 알림 응답
class NotificationResponse(BaseModel):
    notification_id: str
    user_id: str
    schedule_id: Optional[str]
    message: str
    notify_at: datetime
    is_sent: bool
    is_checked: bool

    class Config:
        from_attributes = True


# 알림 확인 요청
class CheckNotificationRequest(BaseModel):
    notification_ids: list[str] = Field(..., description="확인할 알림 ID 목록")
