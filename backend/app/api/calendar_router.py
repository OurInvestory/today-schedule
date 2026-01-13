from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date, datetime

from app.db.database import get_db
from app.models.schedule import Schedule
from app.models.lecture import Lecture
from app.schemas.schedule import ScheduleResponse
from app.schemas.lecture import LectureResponse 
from app.schemas.common import ResponseDTO


router = APIRouter(prefix="/api/calendar", tags=["Calendar"])


# 강의 및 일정 조회
@router.get("", response_model=ResponseDTO)
def get_calendar_combined(
    from_date: date = Query(..., alias="from", example="2026-06-01"),
    to_date: date = Query(..., alias="to", example="2026-06-30"),
    db: Session = Depends(get_db)
):
    try:
        test_user_id = "7822a162-788d-4f36-9366-c956a68393e1"

        # 일정 조회
        start_dt = datetime.combine(from_date, datetime.min.time())
        end_dt = datetime.combine(to_date, datetime.max.time())

        schedules = db.query(Schedule).filter(
            and_(
                Schedule.user_id == test_user_id,
                Schedule.end_at >= start_dt,
                Schedule.end_at <= end_dt
            )
        ).order_by(Schedule.end_at.asc()).all()

        # 강의 조회
        lectures = db.query(Lecture).filter(
            and_(
                Lecture.user_id == test_user_id,
                Lecture.start_day <= to_date,
                Lecture.end_day >= from_date
            )
        ).all()

        # 데이터 변환
        lecture_data = [LectureResponse.from_orm_custom(l) for l in lectures]

        # 결과 통합
        return ResponseDTO(
            status=200,
            message="일정 및 강의 조회에 성공했습니다.",
            data={
                "schedule": [ScheduleResponse.model_validate(s) for s in schedules],
                "lecture": [LectureResponse.from_orm_custom(l) for l in lectures]
            }
        )

    except Exception as e:
        return ResponseDTO(
            status=500, 
            message=f"일정 및 강의 조회에 실패했습니다 : {str(e)}", 
            data=None
        )