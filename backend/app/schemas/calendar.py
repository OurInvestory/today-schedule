from pydantic import BaseModel
from typing import List
from app.schemas.schedule import ScheduleResponse
from app.schemas.lecture import LectureResponse


class CalendarDataResponse(BaseModel):
    schedule: List[ScheduleResponse]
    lecture: List[LectureResponse]

    class Config:
        orm_mode = True
        from_attributes = True