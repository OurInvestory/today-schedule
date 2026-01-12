from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models import user, lecture, schedule, sub_task, notification
from app.db.database import engine, Base
from app.schemas.ai_chat import ChatRequest, APIResponse, ChatResponseData
from app.api import chat_router, user_router, schedule_router, vision_router


# model 설정
Base.metadata.create_all(bind=engine)

# 앱 인스턴스 새성
app = FastAPI(
    title = "5늘의 일정",
    description= "watsonx.ai 기반 대학생 맞춤형 AI 학업 스케줄 도우미",
    version="1.0.0"
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
# 서버 확인 테스트 용도 (추후 삭제 예정)
@app.get("/")
def server_test():
    return {"message": "서버 확인 테스트 용도입니다."}