from pydantic import BaseModel
from typing import List
from app.schemas.schedule import ScheduleResponse
from app.schemas.lecture import LectureResponse


class CalendarDataResponse(BaseModel):
    schedule: List[ScheduleResponse]
    lecture: List[LectureResponse]

    class Config:
        from_attributes = True