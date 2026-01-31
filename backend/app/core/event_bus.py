"""
이벤트 기반 알림 아키텍처 (Redis Pub/Sub)
1분 단위 폴링 방식에서 실시간 이벤트 기반으로 전환
DB 부하 감소 및 즉시 알림 전달
"""

import os
import json
import asyncio
import threading
from datetime import datetime
from typing import Optional, Callable, Dict, Any, List
from enum import Enum
import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


class EventType(str, Enum):
    """이벤트 타입 정의"""
    # 알림 관련
    NOTIFICATION_CREATED = "notification:created"
    NOTIFICATION_SENT = "notification:sent"
    NOTIFICATION_CHECKED = "notification:checked"
    
    # 일정 관련
    SCHEDULE_CREATED = "schedule:created"
    SCHEDULE_UPDATED = "schedule:updated"
    SCHEDULE_DELETED = "schedule:deleted"
    SCHEDULE_REMINDER = "schedule:reminder"
    
    # 강의 관련
    LECTURE_CREATED = "lecture:created"
    LECTURE_UPDATED = "lecture:updated"
    LECTURE_DELETED = "lecture:deleted"
    
    # 사용자 관련
    USER_LOGIN = "user:login"
    USER_LOGOUT = "user:logout"
    
    # 시스템 관련
    DAILY_SUMMARY = "system:daily_summary"
    DEADLINE_ALERT = "system:deadline_alert"


class EventPayload:
    """이벤트 페이로드 구조"""
    
    def __init__(
        self,
        event_type: EventType,
        user_id: str,
        data: Dict[str, Any],
        timestamp: datetime = None
    ):
        self.event_type = event_type
        self.user_id = user_id
        self.data = data
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> dict:
        return {
            "event_type": self.event_type.value,
            "user_id": self.user_id,
            "data": self.data,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "EventPayload":
        return cls(
            event_type=EventType(data["event_type"]),
            user_id=data["user_id"],
            data=data["data"],
            timestamp=datetime.fromisoformat(data["timestamp"])
        )


class EventBus:
    """
    Redis Pub/Sub 기반 이벤트 버스
    
    사용법:
    # 이벤트 발행
    event_bus.publish(EventType.NOTIFICATION_CREATED, user_id, {"notification_id": "..."})
    
    # 이벤트 구독
    event_bus.subscribe(EventType.NOTIFICATION_CREATED, handler_function)
    """
    
    _instance: Optional["EventBus"] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """싱글톤 패턴"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._handlers: Dict[EventType, List[Callable]] = {}
        self._pubsub = None
        self._listener_thread = None
        self._running = False
        
        # Redis 연결
        try:
            self._redis = redis.from_url(
                REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            self._redis.ping()
            print("✅ EventBus: Redis 연결 성공")
        except redis.ConnectionError:
            print("⚠️ EventBus: Redis 연결 실패")
            self._redis = None
    
    @property
    def is_available(self) -> bool:
        """Redis 사용 가능 여부"""
        if self._redis is None:
            return False
        try:
            self._redis.ping()
            return True
        except:
            return False
    
    def publish(self, event_type: EventType, user_id: str, data: Dict[str, Any]) -> bool:
        """
        이벤트 발행
        
        Args:
            event_type: 이벤트 타입
            user_id: 대상 사용자 ID
            data: 이벤트 데이터
        
        Returns:
            발행 성공 여부
        """
        if not self.is_available:
            return False
        
        try:
            payload = EventPayload(event_type, user_id, data)
            
            # 글로벌 채널에 발행
            channel = f"events:{event_type.value}"
            self._redis.publish(channel, json.dumps(payload.to_dict()))
            
            # 사용자별 채널에도 발행 (개인화된 알림용)
            user_channel = f"events:user:{user_id}"
            self._redis.publish(user_channel, json.dumps(payload.to_dict()))
            
            print(f"📤 Event published: {event_type.value} -> user:{user_id}")
            return True
        except Exception as e:
            print(f"❌ Event publish error: {e}")
            return False
    
    def subscribe(self, event_type: EventType, handler: Callable[[EventPayload], None]):
        """
        이벤트 구독 (핸들러 등록)
        
        Args:
            event_type: 구독할 이벤트 타입
            handler: 이벤트 처리 함수
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        print(f"📥 Handler registered for: {event_type.value}")
    
    def unsubscribe(self, event_type: EventType, handler: Callable):
        """이벤트 구독 해제"""
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)
    
    def start_listening(self):
        """백그라운드에서 이벤트 리스닝 시작"""
        if not self.is_available or self._running:
            return
        
        self._running = True
        self._pubsub = self._redis.pubsub()
        
        # 모든 등록된 이벤트 타입에 대해 구독
        channels = [f"events:{et.value}" for et in EventType]
        self._pubsub.subscribe(*channels)
        
        # 백그라운드 스레드에서 리스닝
        self._listener_thread = threading.Thread(target=self._listen, daemon=True)
        self._listener_thread.start()
        print("🎧 EventBus: Started listening...")
    
    def stop_listening(self):
        """이벤트 리스닝 중지"""
        self._running = False
        if self._pubsub:
            self._pubsub.unsubscribe()
            self._pubsub.close()
        print("🛑 EventBus: Stopped listening")
    
    def _listen(self):
        """이벤트 리스닝 루프"""
        while self._running:
            try:
                message = self._pubsub.get_message(timeout=1.0)
                if message and message["type"] == "message":
                    self._handle_message(message)
            except Exception as e:
                print(f"❌ EventBus listen error: {e}")
    
    def _handle_message(self, message: dict):
        """수신된 메시지 처리"""
        try:
            data = json.loads(message["data"])
            payload = EventPayload.from_dict(data)
            
            # 등록된 핸들러 호출
            handlers = self._handlers.get(payload.event_type, [])
            for handler in handlers:
                try:
                    handler(payload)
                except Exception as e:
                    print(f"❌ Handler error: {e}")
        except Exception as e:
            print(f"❌ Message parse error: {e}")


# 싱글톤 인스턴스
event_bus = EventBus()


# =========================================================
# 이벤트 발행 헬퍼 함수
# =========================================================

def emit_notification_created(user_id: str, notification_id: str, message: str, notify_at: datetime):
    """알림 생성 이벤트 발행"""
    event_bus.publish(
        EventType.NOTIFICATION_CREATED,
        user_id,
        {
            "notification_id": notification_id,
            "message": message,
            "notify_at": notify_at.isoformat() if notify_at else None
        }
    )


def emit_notification_sent(user_id: str, notification_id: str):
    """알림 발송 이벤트 발행"""
    event_bus.publish(
        EventType.NOTIFICATION_SENT,
        user_id,
        {"notification_id": notification_id}
    )


def emit_schedule_created(user_id: str, schedule_id: str, title: str, start_at: datetime):
    """일정 생성 이벤트 발행"""
    event_bus.publish(
        EventType.SCHEDULE_CREATED,
        user_id,
        {
            "schedule_id": schedule_id,
            "title": title,
            "start_at": start_at.isoformat() if start_at else None
        }
    )


def emit_schedule_updated(user_id: str, schedule_id: str, title: str):
    """일정 수정 이벤트 발행"""
    event_bus.publish(
        EventType.SCHEDULE_UPDATED,
        user_id,
        {"schedule_id": schedule_id, "title": title}
    )


def emit_schedule_deleted(user_id: str, schedule_id: str):
    """일정 삭제 이벤트 발행"""
    event_bus.publish(
        EventType.SCHEDULE_DELETED,
        user_id,
        {"schedule_id": schedule_id}
    )


def emit_schedule_reminder(user_id: str, schedule_id: str, title: str, minutes_before: int):
    """일정 리마인더 이벤트 발행"""
    event_bus.publish(
        EventType.SCHEDULE_REMINDER,
        user_id,
        {
            "schedule_id": schedule_id,
            "title": title,
            "minutes_before": minutes_before
        }
    )


def emit_deadline_alert(user_id: str, schedule_id: str, title: str, deadline: datetime):
    """마감 알림 이벤트 발행"""
    event_bus.publish(
        EventType.DEADLINE_ALERT,
        user_id,
        {
            "schedule_id": schedule_id,
            "title": title,
            "deadline": deadline.isoformat()
        }
    )


def emit_daily_summary(user_id: str, schedule_count: int, task_count: int):
    """일일 요약 이벤트 발행"""
    event_bus.publish(
        EventType.DAILY_SUMMARY,
        user_id,
        {
            "schedule_count": schedule_count,
            "task_count": task_count,
            "date": datetime.now().strftime("%Y-%m-%d")
        }
    )


# =========================================================
# SSE (Server-Sent Events) 지원
# =========================================================

class SSEManager:
    """
    SSE 연결 관리자
    프론트엔드에서 실시간 이벤트를 수신할 수 있도록 지원
    """
    
    def __init__(self):
        self._connections: Dict[str, List[asyncio.Queue]] = {}
    
    def connect(self, user_id: str) -> asyncio.Queue:
        """사용자 SSE 연결"""
        if user_id not in self._connections:
            self._connections[user_id] = []
        
        queue = asyncio.Queue()
        self._connections[user_id].append(queue)
        print(f"🔌 SSE connected: user:{user_id}")
        return queue
    
    def disconnect(self, user_id: str, queue: asyncio.Queue):
        """사용자 SSE 연결 해제"""
        if user_id in self._connections:
            try:
                self._connections[user_id].remove(queue)
                if not self._connections[user_id]:
                    del self._connections[user_id]
            except ValueError:
                pass
        print(f"🔌 SSE disconnected: user:{user_id}")
    
    async def send_event(self, user_id: str, event_type: str, data: dict):
        """특정 사용자에게 이벤트 전송"""
        if user_id not in self._connections:
            return
        
        event = {
            "event": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        for queue in self._connections[user_id]:
            await queue.put(event)
    
    async def broadcast(self, event_type: str, data: dict):
        """모든 연결된 사용자에게 이벤트 브로드캐스트"""
        event = {
            "event": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        for user_id, queues in self._connections.items():
            for queue in queues:
                await queue.put(event)


# SSE 매니저 싱글톤
sse_manager = SSEManager()
