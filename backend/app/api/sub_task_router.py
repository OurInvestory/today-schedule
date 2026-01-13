from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Union
from datetime import date, datetime

from app.db.database import get_db
from app.models.sub_task import SubTask
from app.models.schedule import Schedule
from app.schemas.sub_task import SaveSubTaskRequest, UpdateSubTaskRequest, SubTaskResponse
from app.schemas.common import ResponseDTO


router = APIRouter(prefix="/api/sub-tasks", tags=["SubTask"])


# 할 일 저장
@router.post("", response_model=ResponseDTO)
def create_sub_tasks(
    obj_in: Union[SaveSubTaskRequest, List[SaveSubTaskRequest]], 
    db: Session = Depends(get_db)
):
    test_user_id = "7822a162-788d-4f36-9366-c956a68393e1"
    items = obj_in if isinstance(obj_in, list) else [obj_in]
    saved_items = []

    try:
        for item in items:
            new_task = SubTask(
                schedule_id=item.schedule_id,
                user_id=test_user_id,
                title=item.title,
                date=item.date,
                estimated_minute=item.estimated_minute,
                is_done=False,
                update_text=None,
                priority=item.priority if hasattr(item, 'priority') else 'medium',
                category=item.category if hasattr(item, 'category') else 'other'
            )
            db.add(new_task)
            saved_items.append(new_task)
        
        db.commit()
        for t in saved_items:
            db.refresh(t)

        return ResponseDTO(
            status=200,
            message="할 일 저장에 성공했습니다.",
            data=[SubTaskResponse.from_orm(t) for t in saved_items]
        )
    except Exception as e:
        db.rollback()
        return ResponseDTO(status=500, message=f"할 일 저장에 실패했습니다 : {str(e)}", data=None)


# 할 일 수정
@router.put("/{sub_task_id}", response_model=ResponseDTO)
def update_sub_task(
    sub_task_id: str, 
    obj_in: UpdateSubTaskRequest, 
    db: Session = Depends(get_db)
):
    try:
        task = db.query(SubTask).filter(SubTask.sub_task_id == sub_task_id).first()
        if not task:
            return ResponseDTO(status=404, message="해당 할 일을 찾을 수 없습니다.", data=None)

        update_data = obj_in.model_dump(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(task, key, value)
        
        db.commit()
        db.refresh(task)

        return ResponseDTO(
            status=200,
            message="할 일 수정에 성공했습니다.",
            data=SubTaskResponse.from_orm(task)
        )
    except Exception as e:
        db.rollback()
        return ResponseDTO(status=500, message=f"할 일 수정에 실패했습니다 : {str(e)}", data=None)


# 할 일 삭제
@router.delete("/{sub_task_id}", response_model=ResponseDTO)
def delete_sub_task(sub_task_id: str, db: Session = Depends(get_db)):
    try:
        task = db.query(SubTask).filter(SubTask.sub_task_id == sub_task_id).first()
        if not task:
            return ResponseDTO(status=404, message="해당 할 일을 찾을 수 없습니다.", data=None)

        db.delete(task)
        db.commit()
        return ResponseDTO(status=200, message="할 일 삭제에 성공했습니다.", data=None)
    except Exception as e:
        db.rollback()
        return ResponseDTO(status=500, message=f"할 일 삭제에 실패했습니다 : {str(e)}", data=None)


# 할 일 조회
@router.get("", response_model=ResponseDTO)
def get_sub_tasks(
    from_date: date = Query(..., alias="from", example="2026-06-01"),
    to_date: date = Query(..., alias="to", example="2026-06-30"),
    db: Session = Depends(get_db)
):
    try:
        test_user_id = "7822a162-788d-4f36-9366-c956a68393e1"
        
        tasks = db.query(SubTask).filter(
            and_(
                SubTask.user_id == test_user_id,
                SubTask.date >= from_date,
                SubTask.date <= to_date
            )
        ).order_by(SubTask.date.asc()).all()

        # 응답 데이터 생성 - schedule 정보를 포함하여 ai_reason과 category 추가
        response_data = []
        for task in tasks:
            task_dict = {
                "sub_task_id": task.sub_task_id,
                "schedule_id": task.schedule_id,
                "user_id": task.user_id,
                "title": task.title,
                "date": task.date,
                "estimated_minute": task.estimated_minute,
                "is_done": task.is_done,
                "update_text": task.update_text,
                "ai_reason": None,
                "category": "other"  # 기본값
            }
            
            # schedule_id가 있으면 schedule 정보 조회
            if task.schedule_id:
                schedule = db.query(Schedule).filter(Schedule.schedule_id == task.schedule_id).first()
                if schedule:
                    task_dict["ai_reason"] = schedule.ai_reason
                    task_dict["category"] = schedule.category if schedule.category else "other"
                    
                    # AI reason 자동 생성 (없는 경우)
                    if not task_dict["ai_reason"] and schedule.end_at:
                        days_until = (schedule.end_at.date() - datetime.now().date()).days
                        if days_until < 0:
                            task_dict["ai_reason"] = f"이미 마감된 일정입니다."
                        elif days_until == 0:
                            task_dict["ai_reason"] = f"오늘 마감되는 일정이므로 우선적으로 처리하세요."
                        elif days_until == 1:
                            task_dict["ai_reason"] = f"내일 마감되는 일정이므로 서둘러 처리하세요."
                        else:
                            task_dict["ai_reason"] = f"{days_until}일 후 마감됩니다. 여유를 가지고 처리하세요."
            else:
                # schedule_id가 없는 경우 독립 할일 - 날짜 기반으로 AI reason 생성
                days_until = (task.date - datetime.now().date()).days
                if days_until < 0:
                    task_dict["ai_reason"] = f"이미 지난 할 일입니다."
                elif days_until == 0:
                    task_dict["ai_reason"] = f"오늘까지 처리해야 하는 할 일입니다."
                elif days_until == 1:
                    task_dict["ai_reason"] = f"내일까지 처리해야 합니다."
                else:
                    task_dict["ai_reason"] = f"{days_until}일 후까지 처리하세요."
            
            response_data.append(SubTaskResponse(**task_dict))

        return ResponseDTO(
            status=200,
            message="할 일 조회에 성공했습니다.",
            data=response_data
        )
    except Exception as e:
        return ResponseDTO(status=500, message=f"할 일 조회에 실패했습니다 : {str(e)}", data=None)