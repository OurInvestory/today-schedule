from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models import user, lecture, schedule, sub_task, notification
from app.db.database import engine, Base
from app.schemas.ai_chat import ChatRequest, APIResponse, ChatResponseData
from app.api import user_router, schedule_router, ai_chat, lecture_router, sub_task_router, calendar_router


# model 설정
Base.metadata.create_all(bind=engine)

# 앱 인스턴스 생성
app = FastAPI(
    title="5늘의 일정",
    description="watsonx.ai 기반 대학생 맞춤형 AI 학업 스케줄 도우미",
    version="1.0.0"
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
app.include_router(user_router.router)
app.include_router(schedule_router.router)
app.include_router(ai_chat.router, prefix="/api", tags=["AI"])
app.include_router(lecture_router.router)
app.include_router(sub_task_router.router)
app.include_router(calendar_router.router)


# 서버 확인 테스트 용도 (추후 삭제 예정)
@app.get("/")
def server_test():
    return {"message": "서버 확인 테스트 용도입니다."}


# Ensure the server runs on 0.0.0.0 for external access
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)