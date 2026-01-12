from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Union
from datetime import date

from app.db.database import get_db
from app.models.sub_task import SubTask
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
                update_text=None
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

        return ResponseDTO(
            status=200,
            message="할 일 조회에 성공했습니다.",
            data=[SubTaskResponse.from_orm(t) for t in tasks]
        )
    except Exception as e:
        return ResponseDTO(status=500, message=f"할 일 조회에 실패했습니다 : {str(e)}", data=None)