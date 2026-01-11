from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Union
from datetime import datetime

from app.db.database import get_db
from app.models.schedule import Schedule
from app.schemas.schedule import CreateScheduleRequest, UpdateScheduleRequest, ScheduleResponse
from app.schemas.common import ResponseDTO


router = APIRouter(prefix="/api/schedules", tags=["Schedule"])


# 일정 저장
@router.post("", response_model=ResponseDTO)
def create_schedules(
    obj_in: Union[CreateScheduleRequest, List[CreateScheduleRequest]], 
    db: Session = Depends(get_db)
):
    test_user_id = "7822a162-788d-4f36-9366-c956a68393e1" 

    if not isinstance(obj_in, list):
        items = [obj_in]
    else:
        items = obj_in

    saved_schedules = []

    try:
        for item in items:
            new_schedule = Schedule(
                user_id=test_user_id,
                title=item.title,
                type=item.type,
                category=item.category,
                start_at=item.start_at,
                end_at=item.end_at,
                priority_score=item.priority_score,
                original_text=item.original_text,
                update_text=None
            )
            db.add(new_schedule)
            saved_schedules.append(new_schedule)
        
        db.commit()
        for schedule in saved_schedules:
            db.refresh(schedule)

        return ResponseDTO(
            status=200,
            message="일정 저장에 성공했습니다.",
            data=[ScheduleResponse.from_orm(s) for s in saved_schedules]
        )
    except Exception as e:
        db.rollback()
        return ResponseDTO(status=500, message=f"일정 저장에 실패했습니다 : {str(e)}", data=None)


# 일정 수정
@router.put("/{schedule_id}", response_model=ResponseDTO)
def update_schedule(
    schedule_id: str, 
    obj_in: UpdateScheduleRequest, 
    db: Session = Depends(get_db)
):
    try:
        schedule = db.query(Schedule).filter(Schedule.schedule_id == schedule_id).first()
        
        if not schedule:
            return ResponseDTO(status=404, message="해당 일정을 찾을 수 없습니다.", data=None)

        # [참고] Pydantic v1의 경우 model_dump 대신 dict() 사용 권장
        update_data = obj_in.dict(exclude_unset=True) if hasattr(obj_in, 'dict') else obj_in.model_dump(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(schedule, key, value)
        
        db.commit()
        db.refresh(schedule)

        return ResponseDTO(
            status=200,
            message="일정 수정에 성공했습니다.",
            data=ScheduleResponse.from_orm(schedule)
        )
    except Exception as e:
        db.rollback()
        return ResponseDTO(status=500, message=f"일정 수정에 실패했습니다 : {str(e)}", data=None)


# 일정 삭제
@router.delete("/{schedule_id}", response_model=ResponseDTO)
def delete_schedule(schedule_id: str, db: Session = Depends(get_db)):
    try:
        schedule = db.query(Schedule).filter(Schedule.schedule_id == schedule_id).first()
        
        if not schedule:
            return ResponseDTO(status=404, message="해당 일정을 찾을 수 없습니다.", data=None)

        db.delete(schedule)
        db.commit()

        return ResponseDTO(status=200, message="일정 삭제에 성공했습니다.", data=None)
    except Exception as e:
        db.rollback()
        return ResponseDTO(status=500, message=f"일정 삭제에 실패했습니다 : {str(e)}", data=None)

# 일정 조회
@router.get("", response_model=ResponseDTO)
def get_schedules(
    from_date: datetime = Query(..., alias="from"),
    to_date: datetime = Query(..., alias="to"),
    db: Session = Depends(get_db)
):
    try:
        test_user_id = "7822a162-788d-4f36-9366-c956a68393e1"

        schedules = db.query(Schedule).filter(
            and_(
                Schedule.user_id == test_user_id,
                Schedule.end_at >= from_date,
                Schedule.end_at <= to_date
            )
        ).order_by(Schedule.end_at.asc()).all()

        return ResponseDTO(
            status=200,
            message="일정 조회에 성공했습니다.",
            data=[ScheduleResponse.from_orm(s) for s in schedules]
        )
    except Exception as e:
        return ResponseDTO(status=500, message=f"일정 조회에 실패했습니다 : {str(e)}", data=None)