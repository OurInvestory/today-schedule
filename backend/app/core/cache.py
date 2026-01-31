"""
Redis 캐싱 서비스
자주 조회되는 데이터의 캐싱을 통한 DB 부하 감소
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, Any, List
from functools import wraps
import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Redis 클라이언트 (싱글톤)
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """Redis 클라이언트 인스턴스 반환"""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # 연결 테스트
            _redis_client.ping()
        except redis.ConnectionError:
            print("⚠️ Redis 연결 실패 - 캐싱 비활성화")
            return None
    return _redis_client


class CacheKeys:
    """캐시 키 상수 관리"""
    
    # 오늘의 일정 (user_id별)
    TODAY_SCHEDULES = "schedules:today:{user_id}"
    
    # 이번 주 일정
    WEEK_SCHEDULES = "schedules:week:{user_id}"
    
    # 대기 중인 알림
    PENDING_NOTIFICATIONS = "notifications:pending:{user_id}"
    
    # 강의 시간표
    LECTURES = "lectures:{user_id}"
    
    # 우선순위 높은 일정
    HIGH_PRIORITY = "schedules:high_priority:{user_id}"
    
    # AI 분석 결과 (가용 시간)
    AVAILABLE_TIME = "ai:available_time:{user_id}:{date_range}"
    
    # 작업 상태
    TASK_STATUS = "task:status:{task_id}"


class CacheService:
    """캐싱 서비스 클래스"""
    
    # 기본 TTL (초)
    DEFAULT_TTL = 300  # 5분
    SHORT_TTL = 60     # 1분
    LONG_TTL = 3600    # 1시간
    
    def __init__(self):
        self.client = get_redis_client()
    
    @property
    def is_available(self) -> bool:
        """Redis 사용 가능 여부"""
        if self.client is None:
            return False
        try:
            self.client.ping()
            return True
        except:
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """캐시 조회"""
        if not self.is_available:
            return None
        
        try:
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """캐시 저장"""
        if not self.is_available:
            return False
        
        try:
            ttl = ttl or self.DEFAULT_TTL
            serialized = json.dumps(value, default=str)
            self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """캐시 삭제"""
        if not self.is_available:
            return False
        
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """패턴에 맞는 모든 키 삭제"""
        if not self.is_available:
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache delete pattern error: {e}")
            return 0
    
    def invalidate_user_cache(self, user_id: str):
        """특정 사용자의 모든 캐시 무효화"""
        patterns = [
            f"schedules:*:{user_id}",
            f"notifications:*:{user_id}",
            f"lectures:{user_id}",
            f"ai:*:{user_id}:*",
        ]
        for pattern in patterns:
            self.delete_pattern(pattern)
    
    # =========================================================
    # 일정 관련 캐시
    # =========================================================
    
    def get_today_schedules(self, user_id: str) -> Optional[List]:
        """오늘의 일정 캐시 조회"""
        key = CacheKeys.TODAY_SCHEDULES.format(user_id=user_id)
        return self.get(key)
    
    def set_today_schedules(self, user_id: str, schedules: List) -> bool:
        """오늘의 일정 캐시 저장"""
        key = CacheKeys.TODAY_SCHEDULES.format(user_id=user_id)
        return self.set(key, schedules, self.SHORT_TTL)
    
    def get_week_schedules(self, user_id: str) -> Optional[List]:
        """이번 주 일정 캐시 조회"""
        key = CacheKeys.WEEK_SCHEDULES.format(user_id=user_id)
        return self.get(key)
    
    def set_week_schedules(self, user_id: str, schedules: List) -> bool:
        """이번 주 일정 캐시 저장"""
        key = CacheKeys.WEEK_SCHEDULES.format(user_id=user_id)
        return self.set(key, schedules, self.DEFAULT_TTL)
    
    # =========================================================
    # 알림 관련 캐시
    # =========================================================
    
    def get_pending_notifications(self, user_id: str) -> Optional[List]:
        """대기 중인 알림 캐시 조회"""
        key = CacheKeys.PENDING_NOTIFICATIONS.format(user_id=user_id)
        return self.get(key)
    
    def set_pending_notifications(self, user_id: str, notifications: List) -> bool:
        """대기 중인 알림 캐시 저장 (짧은 TTL)"""
        key = CacheKeys.PENDING_NOTIFICATIONS.format(user_id=user_id)
        return self.set(key, notifications, 30)  # 30초
    
    def invalidate_notifications(self, user_id: str):
        """알림 캐시 무효화"""
        key = CacheKeys.PENDING_NOTIFICATIONS.format(user_id=user_id)
        self.delete(key)
    
    # =========================================================
    # 강의 관련 캐시
    # =========================================================
    
    def get_lectures(self, user_id: str) -> Optional[List]:
        """강의 시간표 캐시 조회"""
        key = CacheKeys.LECTURES.format(user_id=user_id)
        return self.get(key)
    
    def set_lectures(self, user_id: str, lectures: List) -> bool:
        """강의 시간표 캐시 저장 (긴 TTL)"""
        key = CacheKeys.LECTURES.format(user_id=user_id)
        return self.set(key, lectures, self.LONG_TTL)
    
    # =========================================================
    # AI 분석 결과 캐시
    # =========================================================
    
    def get_available_time(self, user_id: str, start_date: str, end_date: str) -> Optional[dict]:
        """가용 시간 분석 결과 캐시 조회"""
        date_range = f"{start_date}_{end_date}"
        key = CacheKeys.AVAILABLE_TIME.format(user_id=user_id, date_range=date_range)
        return self.get(key)
    
    def set_available_time(self, user_id: str, start_date: str, end_date: str, result: dict) -> bool:
        """가용 시간 분석 결과 캐시 저장"""
        date_range = f"{start_date}_{end_date}"
        key = CacheKeys.AVAILABLE_TIME.format(user_id=user_id, date_range=date_range)
        return self.set(key, result, self.DEFAULT_TTL)
    
    # =========================================================
    # 작업 상태 캐시
    # =========================================================
    
    def get_task_status(self, task_id: str) -> Optional[dict]:
        """비동기 작업 상태 조회"""
        key = CacheKeys.TASK_STATUS.format(task_id=task_id)
        return self.get(key)
    
    def set_task_status(self, task_id: str, status: dict) -> bool:
        """비동기 작업 상태 저장"""
        key = CacheKeys.TASK_STATUS.format(task_id=task_id)
        return self.set(key, status, self.LONG_TTL)


# 싱글톤 인스턴스
cache_service = CacheService()


# =========================================================
# 캐시 데코레이터
# =========================================================

def cached(key_template: str, ttl: int = CacheService.DEFAULT_TTL):
    """
    함수 결과를 캐싱하는 데코레이터
    
    사용법:
    @cached("schedules:today:{user_id}", ttl=60)
    def get_today_schedules(user_id: str):
        ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 캐시 키 생성
            cache_key = key_template.format(**kwargs)
            
            # 캐시 조회
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 함수 실행
            result = func(*args, **kwargs)
            
            # 결과 캐싱
            if result is not None:
                cache_service.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator
