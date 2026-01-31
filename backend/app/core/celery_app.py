"""
Celery 애플리케이션 설정
비동기 작업 큐 처리를 위한 Celery 워커 설정
"""

import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Celery 브로커 및 결과 백엔드 설정
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

# Celery 앱 생성
celery_app = Celery(
    "five_schedule",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.ai_tasks",
        "app.tasks.notification_tasks",
    ]
)

# Celery 설정
celery_app.conf.update(
    # 작업 직렬화 형식
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # 타임존 설정
    timezone="Asia/Seoul",
    enable_utc=True,
    
    # 작업 결과 만료 시간 (1시간)
    result_expires=3600,
    
    # 작업 재시도 설정
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # 동시 실행 워커 수 (프로세스 당)
    worker_concurrency=4,
    
    # 작업 시간 제한 (5분)
    task_time_limit=300,
    task_soft_time_limit=240,
    
    # 작업 우선순위 큐
    task_queues={
        "high_priority": {"exchange": "high_priority", "routing_key": "high"},
        "default": {"exchange": "default", "routing_key": "default"},
        "low_priority": {"exchange": "low_priority", "routing_key": "low"},
    },
    task_default_queue="default",
    
    # 작업 라우팅
    task_routes={
        "app.tasks.ai_tasks.*": {"queue": "default"},
        "app.tasks.notification_tasks.*": {"queue": "high_priority"},
    },
)

# 주기적 작업 (Celery Beat) - 필요시 활성화
# celery_app.conf.beat_schedule = {
#     "check-pending-notifications": {
#         "task": "app.tasks.notification_tasks.check_pending_notifications",
#         "schedule": 60.0,  # 1분마다 실행
#     },
# }
