from pydantic import BaseModel, Field
import datetime
from typing import Optional, List, Union


# 할 일 저장 요청 스키마
class SaveSubTaskRequest(BaseModel):
    schedule_id: str = Field(..., example="3fa85f64-5717-4562-b3fc-2c963f66afa6")
    title: str = Field(..., example="참고 문헌 리스트 정리")
    date: datetime.date = Field(..., example="2026-06-10")
    estimated_minute: int = Field(..., example=45)
    ai_reason: Optional[str] = Field(None, example="최종 발표의 품질을 높이기 위해 필요한 단계입니다.") # [추가]

# 할 일 수정 요청 스키마
class UpdateSubTaskRequest(BaseModel):
    title: Optional[str] = Field(None, example="참고 문헌 리스트 정리")
    date: Optional[datetime.date] = Field(None, example="2026-06-10")
    estimated_minute: Optional[int] = Field(None, example=45)
    is_done: Optional[bool] = Field(None, example=True)
    update_text: Optional[str] = None
    ai_reason: Optional[str] = None # [추가]

# 할 일 응답 스키마
class SubTaskResponse(BaseModel):
    sub_task_id: str
    schedule_id: str
    user_id: Optional[str] = None
    title: str
    date: datetime.date
    estimated_minute: int
    is_done: bool
    update_text: Optional[str] = None
    ai_reason: Optional[str] = None # [추가]

    class Config:
        from_attributes = True