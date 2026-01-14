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
import random


router = APIRouter(prefix="/api/sub-tasks", tags=["SubTask"])

# 응원 문구 15개 (AI 연동이 안 될 때 랜덤 표시)
ENCOURAGEMENT_TIPS = [
    "💪 조금만 더 하면 됩니다! 파이팅!",
    "🌟 한 걸음씩 나아가면 목표에 도달해요!",
    "✨ 오늘의 노력이 내일의 성과가 됩니다!",
    "🎯 집중하면 금방 끝나요! 할 수 있어요!",
    "🚀 시작이 반이에요! 이미 반은 했네요!",
    "💡 잠깐 쉬었다 해도 괜찮아요, 다시 시작하면 돼요!",
    "🏃 꾸준히 하면 분명 좋은 결과가 있을 거예요!",
    "🌈 힘들 때 조금만 버티면 무지개가 뜹니다!",
    "⭐ 당신은 할 수 있어요! 믿어요!",
    "🔥 열정을 불태워요! 완료까지 얼마 안 남았어요!",
    "🎉 완료하면 뿌듯할 거예요! 조금만 더!",
    "💎 작은 노력이 모여 큰 성과가 됩니다!",
    "🌻 오늘 하루도 수고 많으셨어요!",
    "📚 천천히 하나씩 해결해 나가요!",
    "🏆 끝까지 포기하지 않는 당신이 멋져요!",
]

def get_random_encouragement():
    """랜덤 응원 문구 반환"""
    return random.choice(ENCOURAGEMENT_TIPS)


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
                category=item.category if hasattr(item, 'category') else 'other',
                tip=item.tip if hasattr(item, 'tip') else None
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
    from_date: date = Query(..., alias="from", examples=["2026-06-01"]),
    to_date: date = Query(..., alias="to", examples=["2026-06-30"]),
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

        # 응답 데이터 생성 - schedule 정보를 포함하여 tip과 category 추가
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
                "tip": None,
                "category": "other"  # 기본값
            }
            
            # DB에 저장된 tip이 있으면 사용
            if task.tip:
                task_dict["tip"] = task.tip
            # schedule_id가 있으면 schedule 정보 조회
            elif task.schedule_id:
                schedule = db.query(Schedule).filter(Schedule.schedule_id == task.schedule_id).first()
                if schedule:
                    task_dict["category"] = schedule.category if schedule.category else "other"
                    # schedule에 tip이 있으면 사용
                    if hasattr(schedule, 'tip') and schedule.tip:
                        task_dict["tip"] = schedule.tip
                    else:
                        # AI tip이 없으면 랜덤 응원 문구
                        task_dict["tip"] = get_random_encouragement()
            else:
                # schedule_id가 없는 독립 할일 - 랜덤 응원 문구
                task_dict["tip"] = get_random_encouragement()
            
            response_data.append(SubTaskResponse(**task_dict))

        return ResponseDTO(
            status=200,
            message="할 일 조회에 성공했습니다.",
            data=response_data
        )
    except Exception as e:
        return ResponseDTO(status=500, message=f"할 일 조회에 실패했습니다 : {str(e)}", data=None)