from pydantic import BaseModel, Field, model_validator
from datetime import datetime
from typing import Optional


# 일정 저장 요청 스키마
class SaveScheduleRequest(BaseModel):
    title: str = Field(..., example="캡스톤 디자인 최종 발표")
    type: Optional[str] = Field("task", example="task")
    category: Optional[str] = Field("assignment", example="assignment")
    start_at: Optional[datetime] = Field(None, example="2026-06-20T00:00:00")
    end_at: datetime = Field(..., example="2026-06-20T23:59:59")
    priority_score: int = Field(1, ge=0, le=10, example=8)
    original_text: Optional[str] = Field(None, example="6월 20일에 캡스톤 디자인 최종 발표 일정이 있어")
    estimated_minute: Optional[int] = Field(None, example=120)
    source: Optional[str] = Field('manual', example='manual')  # manual or google

# 일정 응답 스키마
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
    estimated_minute: Optional[int]
    source: Optional[str]
    is_ai_generated: bool = False

    class Config:
        from_attributes = True
        
    @model_validator(mode='after')
    def set_is_ai_generated(self) -> 'ScheduleResponse':
        self.is_ai_generated = self.original_text is not None
        return self

# 일정 수정 요청 스키마
class UpdateScheduleRequest(BaseModel):
    title: Optional[str] = Field(None, example="캡스톤 디자인 최종 발표")
    type: Optional[str] = Field(None, example="task")
    category: Optional[str] = Field(None, example="assignment")
    start_at: Optional[datetime] = Field(None, example="2026-06-21T00:00:00")
    end_at: Optional[datetime] = Field(None, example="2026-06-21T23:59:59")
    priority_score: Optional[int] = Field(None, ge=0, le=10, example=2)
    original_text: Optional[str] = None
    update_text: Optional[str] = Field(None, example="6월 20일에 있는 캡스톤 일정 내일로 수정해줘")
    estimated_minute: Optional[int] = None