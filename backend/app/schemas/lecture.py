from pydantic import BaseModel, Field
from datetime import date, time
from typing import Optional, List, Any


# 강의 생성 요청 스키마
class CreateLectureRequest(BaseModel):
    title: str = Field(..., example="데이터베이스 실습")
    start_time: time = Field(..., example="14:00:00")
    end_time: time = Field(..., example="15:30:00")
    start_day: date = Field(..., example="2026-03-02")
    end_day: date = Field(..., example="2026-06-15")
    week: List[int] = Field(..., example=[1, 3])    # 0(월) ~ 6(일)

# 강의 수정 요청 스키마
class UpdateLectureRequest(BaseModel):
    title: Optional[str] = Field(None, example="데이터베이스 실습")
    start_time: Optional[time] = Field(None, example="14:00:00")
    end_time: Optional[time] = Field(None, example="15:30:00")
    start_day: Optional[date] = Field(None, example="2026-03-02")
    end_day: Optional[date] = Field(None, example="2026-06-15")
    week: Optional[List[int]] = Field(None, example=[1, 5])
    update_text: Optional[str] = Field(None, example="데이터베이스 실습 강의 요일 화, 금으로 수정해줘")

# 강의 응답 스키마
class LectureResponse(BaseModel):
    lecture_id: str
    user_id: str
    title: str
    start_time: time
    end_time: time
    start_day: date
    end_day: date
    week: List[int]
    update_text: Optional[str]

    class Config:
        orm_mode = True
        from_attributes = True

    # DB에 문자열로 저장된 week를 리스트로 변환
    @classmethod
    def from_orm_custom(cls, obj):
        week_list = [int(w) for w in obj.week.split(",")] if obj.week else []
        return cls(
            lecture_id=obj.lecture_id,
            user_id=obj.user_id,
            title=obj.title,
            start_time=obj.start_time,
            end_time=obj.end_time,
            start_day=obj.start_day,
            end_day=obj.end_day,
            week=week_list,
            update_text=obj.update_text
        )