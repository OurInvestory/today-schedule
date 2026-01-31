"""
비동기 작업 API 라우터
- 작업 제출
- 작업 상태 조회
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.cache import cache_service
from app.tasks.ai_tasks import process_ai_chat, analyze_schedule_image, recalculate_user_priorities
from app.tasks.notification_tasks import send_schedule_reminder, batch_create_notifications
from app.core.auth import get_current_user
from app.models.user import User


router = APIRouter(prefix="/api/tasks", tags=["Async Tasks"])


# ============================================================
# Request/Response 스키마
# ============================================================

class AsyncTaskResponse(BaseModel):
    """비동기 작업 응답"""
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    """작업 상태 응답"""
    task_id: str
    status: str
    message: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None


class AIAnalysisRequest(BaseModel):
    """AI 분석 요청"""
    message: str = Field(..., description="분석할 메시지")
    context: Optional[Dict] = Field(None, description="추가 컨텍스트")


class ImageAnalysisRequest(BaseModel):
    """이미지 분석 요청"""
    image_data: str = Field(..., description="Base64 인코딩된 이미지")
    image_type: str = Field("timetable", description="이미지 타입 (timetable, schedule)")


class ReminderRequest(BaseModel):
    """리마인더 생성 요청"""
    schedule_id: str = Field(..., description="일정 ID")
    minutes_before: int = Field(30, description="알림 시간 (분 전)")


class BatchNotificationRequest(BaseModel):
    """일괄 알림 생성 요청"""
    notifications: List[Dict] = Field(..., description="알림 데이터 목록")


class APIResponse(BaseModel):
    """공통 API 응답"""
    status: int
    message: str
    data: Optional[Any] = None


# ============================================================
# API 엔드포인트
# ============================================================

@router.post("/ai/analyze", response_model=APIResponse)
async def submit_ai_analysis(
    request: AIAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """
    AI 분석 작업 제출 (비동기)
    
    복잡한 AI 분석 작업을 백그라운드에서 처리합니다.
    반환된 task_id로 상태를 조회할 수 있습니다.
    """
    try:
        # Celery 태스크 제출
        task = process_ai_chat.delay(
            user_id=current_user.user_id,
            message=request.message,
            context=request.context
        )
        
        return APIResponse(
            status=202,
            message="분석 작업이 시작되었습니다. task_id로 상태를 조회하세요.",
            data={
                "task_id": task.id,
                "status": "submitted",
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/image/analyze", response_model=APIResponse)
async def submit_image_analysis(
    request: ImageAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """
    이미지 분석 작업 제출 (비동기)
    
    시간표나 일정 이미지를 백그라운드에서 분석합니다.
    """
    try:
        task = analyze_schedule_image.delay(
            user_id=current_user.user_id,
            image_data=request.image_data,
            image_type=request.image_type
        )
        
        return APIResponse(
            status=202,
            message="이미지 분석이 시작되었습니다.",
            data={
                "task_id": task.id,
                "status": "submitted",
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/priorities/recalculate", response_model=APIResponse)
async def submit_priority_recalculation(
    current_user: User = Depends(get_current_user)
):
    """
    우선순위 재계산 작업 제출 (비동기)
    
    모든 일정의 우선순위를 백그라운드에서 재계산합니다.
    """
    try:
        task = recalculate_user_priorities.delay(
            user_id=current_user.user_id
        )
        
        return APIResponse(
            status=202,
            message="우선순위 재계산이 시작되었습니다.",
            data={
                "task_id": task.id,
                "status": "submitted",
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/reminder", response_model=APIResponse)
async def submit_reminder(
    request: ReminderRequest,
    current_user: User = Depends(get_current_user)
):
    """
    리마인더 알림 생성 (비동기)
    """
    try:
        task = send_schedule_reminder.delay(
            user_id=current_user.user_id,
            schedule_id=request.schedule_id,
            minutes_before=request.minutes_before
        )
        
        return APIResponse(
            status=202,
            message="리마인더 설정이 진행 중입니다.",
            data={
                "task_id": task.id,
                "status": "submitted",
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/batch", response_model=APIResponse)
async def submit_batch_notifications(
    request: BatchNotificationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    일괄 알림 생성 (비동기)
    
    여러 알림을 한 번에 백그라운드에서 생성합니다.
    """
    try:
        task = batch_create_notifications.delay(
            user_id=current_user.user_id,
            notification_data=request.notifications
        )
        
        return APIResponse(
            status=202,
            message=f"{len(request.notifications)}건의 알림 생성이 시작되었습니다.",
            data={
                "task_id": task.id,
                "status": "submitted",
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{task_id}", response_model=APIResponse)
async def get_task_status(task_id: str):
    """
    작업 상태 조회
    
    비동기 작업의 현재 상태를 조회합니다.
    """
    try:
        # 캐시에서 상태 조회
        status = cache_service.get_task_status(task_id)
        
        if status:
            return APIResponse(
                status=200,
                message="작업 상태 조회 성공",
                data={
                    "task_id": task_id,
                    **status
                }
            )
        
        # 캐시에 없으면 Celery에서 직접 조회
        from app.core.celery_app import celery_app
        result = celery_app.AsyncResult(task_id)
        
        celery_status_map = {
            "PENDING": "pending",
            "STARTED": "processing",
            "SUCCESS": "completed",
            "FAILURE": "failed",
            "RETRY": "retrying",
        }
        
        return APIResponse(
            status=200,
            message="작업 상태 조회 성공",
            data={
                "task_id": task_id,
                "status": celery_status_map.get(result.status, result.status),
                "result": result.result if result.ready() else None,
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
