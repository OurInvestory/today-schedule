import os
from dotenv import load_dotenv
from fastapi import APIRouter
import uuid
from datetime import datetime
from app.db.database import db_session
from app.models.user import User
from app.schemas.common import ResponseDTO

from google_auth_oauthlib.flow import Flow


router = APIRouter(prefix="/api/users", tags=["User"])


# Google OAuth 설정
load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8000/api/schedules/google-calendar"
CLIENT_CONFIG = {
    "web": {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'     # 로컬 테스트용 HTTP 허용


# 테스트용 유저 생성
@router.post("/test-user", response_model=ResponseDTO)
def create_test_user():
    db = db_session()
    
    try:
        user_id = "7822a162-788d-4f36-9366-c956a68393e1"
        
        # 존재 여부 확인
        existing_user = db.query(User).filter(User.user_id == user_id).first()
        if existing_user:
            print(f"유저가 이미 존재합니다: {existing_user.email}")
            return

        # 테스트용 유저 생성
        test_user = User(
            user_id=user_id,
            email="test@example.com",
            password="test_password",
            create_at=datetime.now(),
            update_at=datetime.now()
        )

        # 테스트용 유저 저장
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        # 성공 응답 반환
        return ResponseDTO(
            status=200,
            message="테스트용 유저 생성에 성공했습니다.",
            data={
                "user_id": test_user.user_id,
                "email": test_user.email,
                "create_at": test_user.create_at.isoformat()
            }
        )   
    except Exception as e:
        db.rollback()
        return ResponseDTO(
            status=500,
            message=f"테스트용 유저 생성에 실패했습니다 : {str(e)}",
            data=None
        )
    finally:
        db.close()


# 구글 로그인
@router.get("/google-login")
def google_login():
    try:
        # 구글 인증용 flow 객체
        flow = Flow.from_client_config(CLIENT_CONFIG, scopes=SCOPES) 
        flow.redirect_uri = REDIRECT_URI
        
        # 사용자 승인 허용 URL
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        return ResponseDTO(
            status=200,
            message="구글 로그인 URL 생성에 성공했습니다.",
            data={
                "auth_url": authorization_url
            }
        )
    except Exception as e:
        return ResponseDTO(
            status=500, 
            message=f"구글 로그인 URL 생성에 실패했습니다 : {str(e)}", 
            data=None
        )