from pydantic import BaseModel, Field
import datetime
from typing import Optional, List, Union, Dict, Any


# 할 일 저장 요청 스키마
class SaveSubTaskRequest(BaseModel):
    schedule_id: Optional[str] = Field(None, example="3fa85f64-5717-4562-b3fc-2c963f66afa6")
    title: str = Field(..., example="참고 문헌 리스트 정리")
    date: datetime.date = Field(..., example="2026-06-10")
    estimated_minute: Optional[int] = Field(default=60, example=45)
    priority: Optional[str] = Field(default='medium', example='high')  # high, medium, low
    category: Optional[str] = Field(default='other', example='assignment')  # class, assignment, exam, team, activity, other
    tip: Optional[str] = Field(None, example="핵심 개념 위주로 1회독")

# 할 일 수정 요청 스키마
class UpdateSubTaskRequest(BaseModel):
    title: Optional[str] = Field(None, example="참고 문헌 리스트 정리")
    date: Optional[datetime.date] = Field(None, example="2026-06-10")
    estimated_minute: Optional[int] = Field(None, example=45)
    is_done: Optional[bool] = Field(None, example=True)
    update_text: Optional[str] = None
    priority: Optional[str] = Field(None, example='high')
    category: Optional[str] = Field(None, example='assignment')
    tip: Optional[str] = None

# 할 일 응답 스키마
class SubTaskResponse(BaseModel):
    sub_task_id: str
    schedule_id: Optional[str] = None
    user_id: Optional[str] = None
    title: str
    date: datetime.date
    estimated_minute: Optional[int] = None
    is_done: bool
    update_text: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    tip: Optional[str] = None
    schedule: Optional[Dict[str, Any]] = None  # 일정 정보 (색상 등)

    class Config:
        from_attributes = True