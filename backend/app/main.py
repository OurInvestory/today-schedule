from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models import user, lecture, schedule, sub_task, notification
from app.models.user import User
from app.db.database import engine, Base, db_session
from app.db.seed_data import seed_database
from app.schemas.ai_chat import ChatRequest, APIResponse, ChatResponseData
from app.api import user_router, schedule_router, chat_router, lecture_router, sub_task_router, calendar_router, vision_router, notification_router, tasks_router, auth_router, events_router, advanced_router
from app.core.event_bus import event_bus
from app.core.monitoring import setup_prometheus
from sqlalchemy import text
from contextlib import asynccontextmanager
from datetime import datetime


# model 설정
Base.metadata.create_all(bind=engine)


# 테스트 유저 및 시드 데이터를 자동 생성하는 Lifespan 설정
@asynccontextmanager
async def lifespan(app: FastAPI):
    # [Startup] 서버 시작 시 실행
    db = db_session()
    try:
        # 시드 데이터 삽입 (사용자, 일정, 할 일)
        seed_database(db)
        print(" 데이터베이스 초기화 완료")
        
        # 이벤트 버스 시작 (Redis Pub/Sub)
        if event_bus.is_available:
            event_bus.start_listening()
            print(" 이벤트 버스 시작 완료")

    except Exception as e:
        db.rollback()
        print(f" 데이터베이스 초기화 실패: {e}")
    finally:
        db.close()
    
    yield
    
    # [Shutdown] 서버 종료 시 실행
    event_bus.stop_listening()
    print(" 이벤트 버스 종료")


# 앱 인스턴스 생성
app = FastAPI(
    title="5늘의 일정",
    description="Gemini AI 기반 대학생 맞춤형 AI 학업 스케줄 도우미",
    version="1.0.0",
    lifespan=lifespan
)


# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins temporarily
    allow_credentials=True,           # 쿠키 포함 여부
    allow_methods=["*"],              # 모든 HTTP Method 허용
    allow_headers=["*"],              # 모든 HTTP Header 허용
)


# 라우터 등록
app.include_router(auth_router.router)  # 인증/권한 API
app.include_router(user_router.router)
app.include_router(schedule_router.router)
app.include_router(chat_router.router, prefix="/api", tags=["AI"])
app.include_router(lecture_router.router)
app.include_router(sub_task_router.router)
app.include_router(calendar_router.router)
app.include_router(vision_router.router, prefix="/api", tags=["Vision"])
app.include_router(notification_router.router)
app.include_router(tasks_router.router)  # 비동기 작업 API
app.include_router(events_router.router)  # SSE 이벤트 스트림
app.include_router(advanced_router.router)  # 고급 기능 API

# Prometheus 메트릭 설정
setup_prometheus(app)


# ===== Health Check API =====
@app.get("/health", tags=["System"])
def health_check():
    """
    시스템 헬스체크 API
    - 데이터베이스 연결 상태
    - Redis 연결 상태
    - 이벤트 버스 상태
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "components": {}
    }
    
    # 데이터베이스 연결 확인
    try:
        db = db_session()
        db.execute(text("SELECT 1"))
        health_status["components"]["database"] = {"status": "healthy"}
        db.close()
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # 이벤트 버스 (Redis) 상태 확인
    health_status["components"]["event_bus"] = {
        "status": "healthy" if event_bus.is_available else "unavailable",
        "listening": event_bus.listening if hasattr(event_bus, 'listening') else False
    }
    
    return health_status


@app.get("/health/live", tags=["System"])
def liveness_check():
    """Kubernetes liveness probe용 간단한 체크"""
    return {"status": "alive", "timestamp": datetime.now().isoformat()}


@app.get("/health/ready", tags=["System"])
def readiness_check():
    """Kubernetes readiness probe용 체크 (DB 연결 포함)"""
    try:
        db = db_session()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "ready", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"status": "not_ready", "error": str(e), "timestamp": datetime.now().isoformat()}


# 서버 확인 테스트 용도 (추후 삭제 예정)
@app.get("/")
def server_test():
    return {"message": "서버 확인 테스트 용도입니다."}


# Ensure the server runs on 0.0.0.0 for external access
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
