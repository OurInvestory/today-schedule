from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date, datetime
import os
import re
import random

from dotenv import load_dotenv
import google.generativeai as genai  # IBM 제거 -> Google 추가

from app.db.database import get_db
from app.models.sub_task import SubTask
from app.models.schedule import Schedule
from app.schemas.sub_task import SaveSubTaskRequest, UpdateSubTaskRequest, SubTaskResponse
from app.schemas.common import ResponseDTO
from app.core.auth import get_current_user_optional, TokenPayload
from typing import List, Union, Optional

load_dotenv()

router = APIRouter(prefix="/api/sub-tasks", tags=["SubTask"])

# --- Google Gemini 설정 ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")

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

def generate_ai_tip(title: str, category: str = None) -> str:
    """Gemini를 사용하여 할 일에 대한 실용적인 팁 생성"""
    try:
        if not GOOGLE_API_KEY:
            return get_random_encouragement()
        
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        
        category_hint = f" (카테고리: {category})" if category else ""
        prompt = f"""당신은 학업 일정 관리 AI입니다. 할 일에 대해 짧고 실용적인 팁을 한 줄로 제공하세요.

할 일: {title}{category_hint}

팁 (15자 이내, 이모지 포함, 명언 스타일 말고 실천적인 팁):"""
        
        # Gemini 호출
        response = model.generate_content(prompt)
        tip = response.text.strip()
        
        # 후처리: 응답이 너무 길면 자르기
        if len(tip) > 30:
            tip = tip[:27] + "..."
        
        # 후처리: 이모지가 없으면 강제 추가
        if not any(ord(c) > 127 for c in tip[:2]):
            emojis = ["💡", "✨", "📝", "🎯", "⭐"]
            tip = random.choice(emojis) + " " + tip
        
        return tip if tip else get_random_encouragement()
        
    except Exception as e:
        print(f"AI tip 생성 실패: {e}")
        return get_random_encouragement()


# 할 일 저장
@router.post("", response_model=ResponseDTO)
async def create_sub_tasks(
    obj_in: Union[SaveSubTaskRequest, List[SaveSubTaskRequest]], 
    db: Session = Depends(get_db),
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional)
):
    if not current_user:
        return ResponseDTO(status=401, message="로그인이 필요합니다.", data=None)
    
    user_id = current_user.sub
    items = obj_in if isinstance(obj_in, list) else [obj_in]
    saved_items = []

    try:
        for item in items:
            # tip이 없으면 AI가 생성
            tip = item.tip if hasattr(item, 'tip') and item.tip else None
            if not tip:
                category = item.category if hasattr(item, 'category') else 'other'
                tip = generate_ai_tip(item.title, category)
            
            new_task = SubTask(
                schedule_id=item.schedule_id,
                user_id=user_id,
                title=item.title,
                date=item.date,
                estimated_minute=item.estimated_minute,
                is_done=False,
                update_text=None,
                priority=item.priority if hasattr(item, 'priority') else 'medium',
                category=item.category if hasattr(item, 'category') else 'other',
                tip=tip
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
async def get_sub_tasks(
    from_date: date = Query(..., alias="from", examples=["2026-06-01"]),
    to_date: date = Query(..., alias="to", examples=["2026-06-30"]),
    db: Session = Depends(get_db),
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional)
):
    try:
        if not current_user:
            return ResponseDTO(status=200, message="할 일 조회에 성공했습니다.", data=[])
        
        user_id = current_user.user_id
        
        tasks = db.query(SubTask).filter(
            and_(
                SubTask.user_id == user_id,
                SubTask.date >= from_date,
                SubTask.date <= to_date
            )
        ).order_by(SubTask.date.asc()).all()

        # 응답 데이터 생성
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
                "priority": task.priority if task.priority else "medium",
                "category": task.category if task.category else "other",
                "tip": task.tip if task.tip else None,
                "schedule": None  # 일정 정보 추가용
            }
            
            # 일정 정보 조회 및 추가
            if task.schedule_id:
                schedule = db.query(Schedule).filter(Schedule.schedule_id == task.schedule_id).first()
                if schedule:
                    task_dict["schedule"] = {
                        "schedule_id": schedule.schedule_id,
                        "title": schedule.title,
                        "color": schedule.color,
                        "category": schedule.category,
                        "start_at": schedule.start_at.isoformat() if schedule.start_at else None,
                        "end_at": schedule.end_at.isoformat() if schedule.end_at else None,
                    }
                    # tip이 없는 경우 일정에서 가져오기
                    if not task_dict["tip"] and hasattr(schedule, 'tip') and schedule.tip:
                        task_dict["tip"] = schedule.tip
            
            # tip이 여전히 없는 경우 랜덤 응원 메시지
            if not task_dict["tip"]:
                task_dict["tip"] = get_random_encouragement()
            
            response_data.append(SubTaskResponse(**task_dict))

        return ResponseDTO(
            status=200,
            message="할 일 조회에 성공했습니다.",
            data=response_data
        )
    except Exception as e:
        return ResponseDTO(status=500, message=f"할 일 조회에 실패했습니다 : {str(e)}", data=None)