"""
알림 관련 비동기 태스크
- 알림 발송
- 대기 알림 확인
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

from app.core.celery_app import celery_app
from app.core.cache import cache_service
from app.db.database import db_session
from app.models.notification import Notification
from app.models.schedule import Schedule
from sqlalchemy import and_

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def check_pending_notifications(self) -> Dict[str, Any]:
    """
    대기 중인 알림 확인 및 발송 처리
    
    Celery Beat으로 주기적으로 실행 가능
    """
    try:
        db = db_session()
        try:
            now = datetime.now()
            
            # 발송할 알림 조회
            notifications = db.query(Notification).filter(
                and_(
                    Notification.is_sent == False,
                    Notification.notify_at <= now
                )
            ).all()
            
            sent_count = 0
            for notification in notifications:
                # 알림 발송 처리 (실제로는 푸시 알림, 이메일 등)
                notification.is_sent = True
                sent_count += 1
                
                # 사용자별 캐시 무효화
                cache_service.invalidate_notifications(notification.user_id)
            
            db.commit()
            
            return {
                "status": "completed",
                "sent_count": sent_count,
                "checked_at": now.isoformat(),
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Notification Check Error: {e}")
        return {
            "status": "failed",
            "error": str(e),
        }


@celery_app.task(bind=True)
def send_schedule_reminder(self, user_id: str, schedule_id: str, minutes_before: int = 30) -> Dict[str, Any]:
    """
    특정 일정에 대한 리마인더 알림 생성
    """
    task_id = self.request.id
    
    try:
        db = db_session()
        try:
            # 일정 조회
            schedule = db.query(Schedule).filter(
                Schedule.schedule_id == schedule_id
            ).first()
            
            if not schedule:
                return {
                    "status": "failed",
                    "message": "일정을 찾을 수 없습니다.",
                }
            
            # 알림 시간 계산
            if schedule.start_at:
                notify_at = schedule.start_at - timedelta(minutes=minutes_before)
            else:
                notify_at = schedule.end_at - timedelta(minutes=minutes_before)
            
            # 알림 생성
            notification = Notification(
                user_id=user_id,
                schedule_id=schedule_id,
                message=f"'{schedule.title}' {minutes_before}분 전입니다!",
                notify_at=notify_at,
                is_sent=False,
                is_checked=False,
            )
            
            db.add(notification)
            db.commit()
            
            # 캐시 무효화
            cache_service.invalidate_notifications(user_id)
            
            return {
                "status": "completed",
                "message": f"알림이 {notify_at.strftime('%Y-%m-%d %H:%M')}에 설정되었습니다.",
                "notification_id": notification.notification_id,
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Schedule Reminder Error: {e}")
        return {
            "status": "failed",
            "error": str(e),
        }


@celery_app.task(bind=True)
def batch_create_notifications(self, user_id: str, notification_data: List[Dict]) -> Dict[str, Any]:
    """
    여러 알림 일괄 생성 (비동기)
    """
    task_id = self.request.id
    
    try:
        cache_service.set_task_status(task_id, {
            "status": "processing",
            "message": f"{len(notification_data)}건의 알림을 생성 중...",
            "started_at": datetime.now().isoformat(),
        })
        
        db = db_session()
        try:
            created_count = 0
            
            for data in notification_data:
                notification = Notification(
                    user_id=user_id,
                    schedule_id=data.get("schedule_id"),
                    message=data.get("message", "알림"),
                    notify_at=datetime.fromisoformat(data["notify_at"]) if isinstance(data["notify_at"], str) else data["notify_at"],
                    is_sent=False,
                    is_checked=False,
                )
                db.add(notification)
                created_count += 1
            
            db.commit()
            
            # 캐시 무효화
            cache_service.invalidate_notifications(user_id)
            
            result = {
                "status": "completed",
                "message": f"{created_count}건의 알림이 생성되었습니다.",
                "created_count": created_count,
                "completed_at": datetime.now().isoformat(),
            }
            cache_service.set_task_status(task_id, result)
            
            return result
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Batch Notification Error: {e}")
        
        error_result = {
            "status": "failed",
            "message": "알림 생성 중 오류가 발생했습니다.",
            "error": str(e),
            "failed_at": datetime.now().isoformat(),
        }
        cache_service.set_task_status(task_id, error_result)
        return error_result
