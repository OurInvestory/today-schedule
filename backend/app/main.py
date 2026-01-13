from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models import user, lecture, schedule, sub_task, notification
from app.models.user import User
from app.db.database import engine, Base, db_session
from app.schemas.ai_chat import ChatRequest, APIResponse, ChatResponseData

from app.api import user_router, schedule_router, chat_router, lecture_router, sub_task_router, calendar_router, vision_router
from contextlib import asynccontextmanager
from datetime import datetime



# model 설정
Base.metadata.create_all(bind=engine)


# 테스트 유저를 자동 생성하는 Lifespan 설정
@asynccontextmanager
async def lifespan(app: FastAPI):
    # [Startup] 서버 시작 시 실행
    db = db_session()
    try:
        user_id = "7822a162-788d-4f36-9366-c956a68393e1"   # 테스트용 고정 UUID
        
        existing_user = db.query(User).filter(User.user_id == user_id).first()     # 유저 존재 여부 확인
        
        if not existing_user:
            test_user = User(
            user_id=user_id,
            email="test@example.com",
            password="test_password",
            create_at=datetime.now(),
            update_at=datetime.now()
            )
            db.add(test_user)
            db.commit()
            print("테스트 유저 생성에 성공했습니다.")   # TEST CODE
        else:
            print("테스트 유저가 이미 존재합니다.")   # TEST CODE

    except Exception as e:
        db.rollback()
    finally:
        db.close()
    
    yield


# 앱 인스턴스 생성
app = FastAPI(
    title = "5늘의 일정",
    description= "watsonx.ai 기반 대학생 맞춤형 AI 학업 스케줄 도우미",
    version="1.0.0",
    lifespan=lifespan
)


# CORS 설정
origins = [
    "http://localhost:3000",    # React 기본 포트
    "http://127.0.0.1:3000",
    "http://localhost:5173"    # Vite/Vue 기본 포트
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # 허용할 도메인 리스트
    allow_credentials=True,           # 쿠키 포함 여부
    allow_methods=["*"],              # 모든 HTTP Method 허용
    allow_headers=["*"],              # 모든 HTTP Header 허용
)


# 라우터 등록
app.include_router(user_router.router)
app.include_router(schedule_router.router)


app.include_router(chat_router.router, prefix="/api/ai", tags=["AI"])
app.include_router(vision_router.router, prefix="/api/ai/vision", tags=["Vision"])
app.include_router(lecture_router.router)
app.include_router(sub_task_router.router)
app.include_router(calendar_router.router)

# 서버 확인 테스트 용도 (추후 삭제 예정)
@app.get("/")
def server_test():
    return {"message": "서버 확인 테스트 용도입니다."}