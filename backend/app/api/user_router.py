import os
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.db.database import db_session
from app.models.user import User
from app.schemas.common import ResponseDTO

from google_auth_oauthlib.flow import Flow


router = APIRouter(prefix="/api/users", tags=["User"])


# ===== Profile Schemas =====
class ProfileUpdateRequest(BaseModel):
    """프로필 업데이트 요청 스키마"""
    name: Optional[str] = None
    school: Optional[str] = None
    department: Optional[str] = None
    grade: Optional[int] = None


class ProfileResponse(BaseModel):
    """프로필 응답 스키마"""
    user_id: str
    email: str
    name: Optional[str]
    school: Optional[str]
    department: Optional[str]
    grade: Optional[int]
    role: str
    created_at: datetime
    updated_at: datetime


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


# ===== 프로필 관리 API =====
@router.get("/{user_id}/profile", response_model=ResponseDTO)
def get_user_profile(user_id: str):
    """사용자 프로필 조회"""
    db = db_session()
    
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            return ResponseDTO(
                status=404,
                message="사용자를 찾을 수 없습니다.",
                data=None
            )
        
        profile_data = {
            "user_id": user.user_id,
            "email": user.email,
            "name": getattr(user, 'name', None),
            "school": getattr(user, 'school', None),
            "department": getattr(user, 'department', None),
            "grade": getattr(user, 'grade', None),
            "role": getattr(user, 'role', 'user'),
            "created_at": user.create_at.isoformat() if user.create_at else None,
            "updated_at": user.update_at.isoformat() if user.update_at else None
        }
        
        return ResponseDTO(
            status=200,
            message="프로필 조회에 성공했습니다.",
            data=profile_data
        )
    except Exception as e:
        return ResponseDTO(
            status=500,
            message=f"프로필 조회에 실패했습니다: {str(e)}",
            data=None
        )
    finally:
        db.close()


@router.put("/{user_id}/profile", response_model=ResponseDTO)
def update_user_profile(user_id: str, profile: ProfileUpdateRequest):
    """사용자 프로필 업데이트"""
    db = db_session()
    
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            return ResponseDTO(
                status=404,
                message="사용자를 찾을 수 없습니다.",
                data=None
            )
        
        # 프로필 필드 업데이트 (제공된 값만)
        if profile.name is not None:
            user.name = profile.name
        if profile.school is not None:
            user.school = profile.school
        if profile.department is not None:
            user.department = profile.department
        if profile.grade is not None:
            user.grade = profile.grade
        
        user.update_at = datetime.now()
        
        db.commit()
        db.refresh(user)
        
        profile_data = {
            "user_id": user.user_id,
            "email": user.email,
            "name": getattr(user, 'name', None),
            "school": getattr(user, 'school', None),
            "department": getattr(user, 'department', None),
            "grade": getattr(user, 'grade', None),
            "role": getattr(user, 'role', 'user'),
            "updated_at": user.update_at.isoformat()
        }
        
        return ResponseDTO(
            status=200,
            message="프로필 업데이트에 성공했습니다.",
            data=profile_data
        )
    except Exception as e:
        db.rollback()
        return ResponseDTO(
            status=500,
            message=f"프로필 업데이트에 실패했습니다: {str(e)}",
            data=None
        )
    finally:
        db.close()


@router.delete("/{user_id}", response_model=ResponseDTO)
def delete_user(user_id: str):
    """사용자 계정 삭제 (탈퇴)"""
    db = db_session()
    
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            return ResponseDTO(
                status=404,
                message="사용자를 찾을 수 없습니다.",
                data=None
            )
        
        db.delete(user)
        db.commit()
        
        return ResponseDTO(
            status=200,
            message="계정이 성공적으로 삭제되었습니다.",
            data={"user_id": user_id}
        )
    except Exception as e:
        db.rollback()
        return ResponseDTO(
            status=500,
            message=f"계정 삭제에 실패했습니다: {str(e)}",
            data=None
        )
    finally:
        db.close()