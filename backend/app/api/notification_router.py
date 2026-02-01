from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from typing import List, Optional

from app.db.database import get_db
from app.models.notification import Notification
from app.models.schedule import Schedule
from app.schemas.notification import CreateNotificationRequest, NotificationResponse, CheckNotificationRequest
from app.schemas.common import ResponseDTO
from app.core.cache import cache_service
from app.core.auth import get_current_user_optional, TokenPayload


router = APIRouter(prefix="/api/notifications", tags=["Notification"])


# 알림 생성
@router.post("", response_model=ResponseDTO)
async def create_notification(
    req: CreateNotificationRequest,
    db: Session = Depends(get_db),
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional)
):
    try:
        if not current_user:
            return ResponseDTO(status=401, message="로그인이 필요합니다.", data=None)
        
        user_id = current_user.sub
        schedule_id = req.schedule_id
        notify_at = req.notify_at
        
        # schedule_title로 검색해서 schedule_id 찾기
        if not schedule_id and req.schedule_title:
            schedule = db.query(Schedule).filter(
                and_(
                    Schedule.user_id == user_id,
                    Schedule.title.ilike(f"%{req.schedule_title}%")
                )
            ).first()
            
            if schedule:
                schedule_id = schedule.schedule_id
                
                # minutes_before가 있으면 notify_at 계산
                if req.minutes_before and schedule.start_at:
                    notify_at = schedule.start_at - timedelta(minutes=req.minutes_before)
        
        new_notification = Notification(
            user_id=user_id,
            schedule_id=schedule_id,
            message=req.message,
            notify_at=notify_at,
            is_sent=False,
            is_checked=False
        )
        
        db.add(new_notification)
        db.commit()
        db.refresh(new_notification)
        
        # 알림 캐시 무효화
        cache_service.invalidate_notifications(user_id)
        
        return ResponseDTO(
            status=200,
            message="알림이 등록되었습니다.",
            data=NotificationResponse.model_validate(new_notification)
        )
    except Exception as e:
        db.rollback()
        return ResponseDTO(status=500, message=f"알림 등록에 실패했습니다: {str(e)}", data=None)


# 대기 중인 알림 조회 (발송할 알림들) - 캐싱 적용
@router.get("/pending", response_model=ResponseDTO)
async def get_pending_notifications(
    db: Session = Depends(get_db),
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional)
):
    """
    현재 시간 기준으로 발송해야 할 알림 조회 (is_sent=False, notify_at <= now)
    프론트에서 폴링으로 호출 - Redis 캐싱으로 DB 부하 감소
    """
    try:
        if not current_user:
            return ResponseDTO(status=200, message="0건의 알림이 있습니다.", data=[])
        
        user_id = current_user.sub
        
        # 캐시 먼저 확인 (30초 TTL)
        cached = cache_service.get_pending_notifications(user_id)
        if cached is not None:
            return ResponseDTO(
                status=200,
                message=f"{len(cached)}건의 알림이 있습니다. (cached)",
                data=cached
            )
        
        now = datetime.now()
        
        notifications = db.query(Notification).filter(
            and_(
                Notification.user_id == user_id,
                Notification.is_sent == False,
                Notification.notify_at <= now
            )
        ).all()
        
        # 조회된 알림들을 is_sent=True로 업데이트
        for n in notifications:
            n.is_sent = True
        db.commit()
        
        # 결과를 캐시에 저장 (빈 리스트도 캐싱하여 DB 호출 방지)
        result = [NotificationResponse.model_validate(n).model_dump() for n in notifications]
        cache_service.set_pending_notifications(user_id, result)
        
        return ResponseDTO(
            status=200,
            message=f"{len(notifications)}건의 알림이 있습니다.",
            data=result
        )
    except Exception as e:
        return ResponseDTO(status=500, message=f"알림 조회에 실패했습니다: {str(e)}", data=None)


# 내 알림 목록 조회
@router.get("", response_model=ResponseDTO)
async def get_my_notifications(
    limit: int = Query(20, description="조회 개수"),
    include_checked: bool = Query(False, description="확인된 알림도 포함"),
    db: Session = Depends(get_db),
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional)
):
    try:
        if not current_user:
            return ResponseDTO(status=200, message="알림 목록을 조회했습니다.", data=[])
        
        user_id = current_user.sub
        
        query = db.query(Notification).filter(
            Notification.user_id == user_id
        )
        
        if not include_checked:
            query = query.filter(Notification.is_checked == False)
        
        notifications = query.order_by(Notification.notify_at.desc()).limit(limit).all()
        
        return ResponseDTO(
            status=200,
            message="알림 목록을 조회했습니다.",
            data=[NotificationResponse.model_validate(n) for n in notifications]
        )
    except Exception as e:
        return ResponseDTO(status=500, message=f"알림 조회에 실패했습니다: {str(e)}", data=None)


# 알림 확인 처리
@router.post("/check", response_model=ResponseDTO)
async def check_notifications(
    req: CheckNotificationRequest,
    db: Session = Depends(get_db),
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional)
):
    try:
        if not current_user:
            return ResponseDTO(status=401, message="로그인이 필요합니다.", data=None)
        
        user_id = current_user.sub
        
        updated_count = db.query(Notification).filter(
            and_(
                Notification.user_id == user_id,
                Notification.notification_id.in_(req.notification_ids)
            )
        ).update({"is_checked": True}, synchronize_session=False)
        
        db.commit()
        
        return ResponseDTO(
            status=200,
            message=f"{updated_count}건의 알림을 확인 처리했습니다.",
            data=None
        )
    except Exception as e:
        db.rollback()
        return ResponseDTO(status=500, message=f"알림 확인에 실패했습니다: {str(e)}", data=None)


# 알림 삭제
@router.delete("/{notification_id}", response_model=ResponseDTO)
async def delete_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional)
):
    try:
        if not current_user:
            return ResponseDTO(status=401, message="로그인이 필요합니다.", data=None)
        
        user_id = current_user.sub
        
        notification = db.query(Notification).filter(
            and_(
                Notification.notification_id == notification_id,
                Notification.user_id == user_id
            )
        ).first()
        
        if not notification:
            return ResponseDTO(status=404, message="알림을 찾을 수 없습니다.", data=None)
        
        db.delete(notification)
        db.commit()
        
        return ResponseDTO(status=200, message="알림이 삭제되었습니다.", data=None)
    except Exception as e:
        db.rollback()
        return ResponseDTO(status=500, message=f"알림 삭제에 실패했습니다: {str(e)}", data=None)
