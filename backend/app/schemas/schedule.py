from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any


# 일정 생성 요청 스키마
class CreateScheduleRequest(BaseModel):
    title: str = Field(..., example="캡스톤 디자인 최종 발표")
    type: Optional[str] = Field(example="task")
    category: Optional[str] = Field(example="과제")
    start_at: Optional[datetime] = None
    end_at: datetime
    priority_score: int = Field(1, ge=0, le=2)
    original_text: Optional[str] = None

# 일정 생성 응답 스키마
class ScheduleResponse(BaseModel):
    schedule_id: str
    user_id: str
    title: str
    type: Optional[str]
    category: Optional[str]
    start_at: Optional[datetime]
    end_at: datetime
    priority_score: int
    original_text: Optional[str]
    update_text: Optional[str]

    class Config:
        from_attributes = True
        
# 일정 수정 요청 스키마
class UpdateScheduleRequest(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = None
    category: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    priority_score: Optional[int] = Field(None, ge=0, le=2)
    original_text: Optional[str] = None
    update_text: Optional[str] = None