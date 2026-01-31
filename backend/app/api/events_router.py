"""
SSE (Server-Sent Events) 라우터
프론트엔드에서 실시간 알림을 받을 수 있도록 지원
"""

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from datetime import datetime
import asyncio
import json

from app.core.event_bus import sse_manager, event_bus, EventType, EventPayload


router = APIRouter(prefix="/api/events", tags=["Events"])

TEST_USER_ID = "7822a162-788d-4f36-9366-c956a68393e1"


# 이벤트 핸들러 등록 (SSE로 전달)
def _setup_event_handlers():
    """이벤트 핸들러 설정"""
    
    async def forward_to_sse(payload: EventPayload):
        """이벤트를 SSE로 전달"""
        await sse_manager.send_event(
            payload.user_id,
            payload.event_type.value,
            payload.data
        )
    
    # 모든 알림 관련 이벤트 구독
    for event_type in [
        EventType.NOTIFICATION_CREATED,
        EventType.NOTIFICATION_SENT,
        EventType.SCHEDULE_REMINDER,
        EventType.DEADLINE_ALERT,
        EventType.DAILY_SUMMARY,
    ]:
        def create_handler(et):
            def handler(payload: EventPayload):
                asyncio.create_task(forward_to_sse(payload))
            return handler
        event_bus.subscribe(event_type, create_handler(event_type))


# 서버 시작 시 핸들러 설정
_setup_event_handlers()


@router.get("/stream")
async def event_stream(request: Request):
    """
    SSE 스트림 엔드포인트
    
    프론트엔드에서 EventSource로 연결:
    const eventSource = new EventSource('/api/events/stream');
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        // 이벤트 처리
    };
    """
    
    user_id = TEST_USER_ID  # TODO: JWT에서 user_id 추출
    queue = sse_manager.connect(user_id)
    
    async def event_generator():
        try:
            # 초기 연결 확인 이벤트
            yield f"event: connected\ndata: {json.dumps({'user_id': user_id, 'timestamp': datetime.now().isoformat()})}\n\n"
            
            while True:
                # 연결 종료 확인
                if await request.is_disconnected():
                    break
                
                try:
                    # 이벤트 대기 (30초 타임아웃 후 heartbeat)
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    
                    event_type = event.get("event", "message")
                    event_data = json.dumps(event.get("data", {}))
                    
                    yield f"event: {event_type}\ndata: {event_data}\n\n"
                except asyncio.TimeoutError:
                    # Heartbeat 전송 (연결 유지)
                    yield f"event: heartbeat\ndata: {json.dumps({'timestamp': datetime.now().isoformat()})}\n\n"
        finally:
            sse_manager.disconnect(user_id, queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # nginx 버퍼링 비활성화
        }
    )


@router.post("/test")
async def test_event():
    """테스트용 이벤트 발행"""
    from app.core.event_bus import emit_notification_created
    
    emit_notification_created(
        TEST_USER_ID,
        "test-notification-id",
        "테스트 알림 메시지입니다.",
        datetime.now()
    )
    
    return {"status": "success", "message": "Test event published"}


@router.get("/status")
async def event_bus_status():
    """이벤트 버스 상태 확인"""
    return {
        "event_bus": {
            "available": event_bus.is_available,
            "running": event_bus._running,
            "handlers_count": {
                et.value: len(handlers)
                for et, handlers in event_bus._handlers.items()
            }
        },
        "sse_manager": {
            "connections_count": sum(
                len(queues) for queues in sse_manager._connections.values()
            )
        }
    }
