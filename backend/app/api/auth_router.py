"""
인증 API 라우터
- 로그인/로그아웃
- 토큰 갱신
- 소셜 로그인 (Google, Kakao)
- 권한 관리
"""

import os
import re
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, field_validator
import httpx
from dotenv import load_dotenv

from app.db.database import get_db
from app.models.user import User
from app.schemas.common import ResponseDTO
from app.core.auth import (
    TokenService, UserRole, TokenPayload, Permission,
    get_current_user_required, RBACChecker, AdminOnly
)
from app.core.security import get_password_hash, verify_password

load_dotenv()

router = APIRouter(prefix="/api/auth", tags=["Auth"])

# 환경 변수
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
KAKAO_CLIENT_ID = os.getenv("KAKAO_CLIENT_ID")
KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# 로그인 시도 제한
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


# =========================================================
# Pydantic 스키마
# =========================================================

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("비밀번호는 최소 8자 이상이어야 합니다.")
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("비밀번호에 영문자가 포함되어야 합니다.")
        if not re.search(r"\d", v):
            raise ValueError("비밀번호에 숫자가 포함되어야 합니다.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangeRoleRequest(BaseModel):
    user_id: str
    role: UserRole


# =========================================================
# 유틸리티 함수
# =========================================================

def check_account_locked(user: User) -> bool:
    """계정 잠금 상태 확인"""
    if user.locked_until and user.locked_until > datetime.now():
        return True
    return False


def increment_login_attempts(user: User, db: Session):
    """로그인 시도 횟수 증가"""
    user.login_attempts += 1
    if user.login_attempts >= MAX_LOGIN_ATTEMPTS:
        user.locked_until = datetime.now() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
    db.commit()


def reset_login_attempts(user: User, db: Session):
    """로그인 시도 횟수 초기화"""
    user.login_attempts = 0
    user.locked_until = None
    db.commit()


# =========================================================
# 인증 API
# =========================================================

@router.post("/register", response_model=ResponseDTO)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """
    회원가입
    - 이메일 중복 확인
    - 비밀번호 강도 검증
    - 기본 역할: user
    """
    # 이메일 중복 확인
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        return ResponseDTO(status=400, message="이미 사용 중인 이메일입니다.", data=None)
    
    # 새 사용자 생성
    new_user = User(
        email=req.email,
        password=get_password_hash(req.password),
        role=UserRole.USER.value,
        create_at=datetime.now(),
        update_at=datetime.now()
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # 토큰 발급
    tokens = TokenService.create_token_pair(
        new_user.user_id, new_user.email, UserRole(new_user.role)
    )
    
    # 리프레시 토큰 저장
    new_user.refresh_token = tokens["refresh_token"]
    db.commit()
    
    return ResponseDTO(
        status=200,
        message="회원가입이 완료되었습니다.",
        data={
            "user_id": new_user.user_id,
            "email": new_user.email,
            "role": new_user.role,
            **tokens
        }
    )


@router.post("/login", response_model=ResponseDTO)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """
    로그인
    - 로그인 시도 횟수 제한
    - 계정 잠금 기능
    - JWT 토큰 발급
    """
    user = db.query(User).filter(User.email == req.email).first()
    
    if not user:
        return ResponseDTO(status=401, message="이메일 또는 비밀번호가 올바르지 않습니다.", data=None)
    
    # 계정 잠금 확인
    if check_account_locked(user):
        remaining = (user.locked_until - datetime.now()).seconds // 60
        return ResponseDTO(
            status=403, 
            message=f"계정이 잠겼습니다. {remaining}분 후에 다시 시도해주세요.",
            data=None
        )
    
    # 비밀번호 검증
    if not verify_password(req.password, user.password):
        increment_login_attempts(user, db)
        remaining_attempts = MAX_LOGIN_ATTEMPTS - user.login_attempts
        
        if remaining_attempts <= 0:
            return ResponseDTO(
                status=403, 
                message=f"로그인 시도 횟수를 초과했습니다. {LOCKOUT_DURATION_MINUTES}분 후에 다시 시도해주세요.",
                data=None
            )
        
        return ResponseDTO(
            status=401, 
            message=f"이메일 또는 비밀번호가 올바르지 않습니다. (남은 시도: {remaining_attempts}회)",
            data=None
        )
    
    # 로그인 성공
    reset_login_attempts(user, db)
    
    # 토큰 발급
    tokens = TokenService.create_token_pair(
        user.user_id, user.email, UserRole(user.role)
    )
    
    # 리프레시 토큰 저장
    user.refresh_token = tokens["refresh_token"]
    user.update_at = datetime.now()
    db.commit()
    
    return ResponseDTO(
        status=200,
        message="로그인에 성공했습니다.",
        data={
            "user_id": user.user_id,
            "email": user.email,
            "role": user.role,
            **tokens
        }
    )


@router.post("/refresh", response_model=ResponseDTO)
def refresh_token(req: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    토큰 갱신
    - 리프레시 토큰으로 새 액세스 토큰 발급
    """
    try:
        new_tokens = TokenService.refresh_access_token(req.refresh_token)
        return ResponseDTO(
            status=200,
            message="토큰이 갱신되었습니다.",
            data=new_tokens
        )
    except HTTPException as e:
        return ResponseDTO(status=e.status_code, message=e.detail, data=None)


@router.post("/logout", response_model=ResponseDTO)
def logout(
    current_user: TokenPayload = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """
    로그아웃
    - 리프레시 토큰 무효화
    """
    user = db.query(User).filter(User.user_id == current_user.user_id).first()
    if user:
        user.refresh_token = None
        db.commit()
    
    return ResponseDTO(status=200, message="로그아웃되었습니다.", data=None)


@router.get("/me", response_model=ResponseDTO)
def get_me(current_user: TokenPayload = Depends(get_current_user_required)):
    """현재 사용자 정보 조회"""
    return ResponseDTO(
        status=200,
        message="사용자 정보 조회 성공",
        data={
            "user_id": current_user.user_id,
            "email": current_user.email,
            "role": current_user.role.value,
            "permissions": [p.value for p in current_user.permissions]
        }
    )


# =========================================================
# OAuth2.0 소셜 로그인
# =========================================================

@router.get("/google")
def google_login():
    """Google OAuth 로그인 시작"""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google OAuth가 설정되지 않았습니다.")
    
    redirect_uri = f"{FRONTEND_URL}/auth/google/callback"
    scope = "openid email profile"
    
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope={scope}"
        f"&access_type=offline"
        f"&prompt=consent"
    )
    
    return ResponseDTO(
        status=200,
        message="Google 로그인 URL 생성 성공",
        data={"auth_url": auth_url}
    )


@router.post("/google/callback", response_model=ResponseDTO)
async def google_callback(
    code: str,
    db: Session = Depends(get_db)
):
    """Google OAuth 콜백 처리"""
    redirect_uri = f"{FRONTEND_URL}/auth/google/callback"
    
    # 토큰 교환
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code"
            }
        )
        
        if token_response.status_code != 200:
            return ResponseDTO(status=400, message="Google 인증에 실패했습니다.", data=None)
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        # 사용자 정보 조회
        user_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if user_response.status_code != 200:
            return ResponseDTO(status=400, message="사용자 정보 조회에 실패했습니다.", data=None)
        
        user_info = user_response.json()
    
    email = user_info.get("email")
    google_id = user_info.get("id")
    
    # 기존 사용자 확인
    user = db.query(User).filter(
        (User.email == email) | 
        ((User.oauth_provider == "google") & (User.oauth_id == google_id))
    ).first()
    
    if user:
        # 기존 사용자 업데이트
        user.oauth_provider = "google"
        user.oauth_id = google_id
        user.update_at = datetime.now()
    else:
        # 새 사용자 생성
        user = User(
            email=email,
            password=get_password_hash(secrets.token_urlsafe(32)),  # 랜덤 비밀번호
            role=UserRole.USER.value,
            oauth_provider="google",
            oauth_id=google_id,
            create_at=datetime.now(),
            update_at=datetime.now()
        )
        db.add(user)
    
    # 토큰 발급
    tokens = TokenService.create_token_pair(
        user.user_id, user.email, UserRole(user.role)
    )
    user.refresh_token = tokens["refresh_token"]
    db.commit()
    
    return ResponseDTO(
        status=200,
        message="Google 로그인 성공",
        data={
            "user_id": user.user_id,
            "email": user.email,
            "role": user.role,
            **tokens
        }
    )


@router.get("/kakao")
def kakao_login():
    """Kakao OAuth 로그인 시작"""
    if not KAKAO_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Kakao OAuth가 설정되지 않았습니다.")
    
    redirect_uri = f"{FRONTEND_URL}/auth/kakao/callback"
    
    auth_url = (
        "https://kauth.kakao.com/oauth/authorize"
        f"?client_id={KAKAO_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
    )
    
    return ResponseDTO(
        status=200,
        message="Kakao 로그인 URL 생성 성공",
        data={"auth_url": auth_url}
    )


@router.post("/kakao/callback", response_model=ResponseDTO)
async def kakao_callback(
    code: str,
    db: Session = Depends(get_db)
):
    """Kakao OAuth 콜백 처리"""
    redirect_uri = f"{FRONTEND_URL}/auth/kakao/callback"
    
    async with httpx.AsyncClient() as client:
        # 토큰 교환
        token_response = await client.post(
            "https://kauth.kakao.com/oauth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": KAKAO_CLIENT_ID,
                "client_secret": KAKAO_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "code": code
            }
        )
        
        if token_response.status_code != 200:
            return ResponseDTO(status=400, message="Kakao 인증에 실패했습니다.", data=None)
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        # 사용자 정보 조회
        user_response = await client.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if user_response.status_code != 200:
            return ResponseDTO(status=400, message="사용자 정보 조회에 실패했습니다.", data=None)
        
        user_info = user_response.json()
    
    kakao_id = str(user_info.get("id"))
    kakao_account = user_info.get("kakao_account", {})
    email = kakao_account.get("email", f"kakao_{kakao_id}@kakao.local")
    
    # 기존 사용자 확인
    user = db.query(User).filter(
        (User.email == email) | 
        ((User.oauth_provider == "kakao") & (User.oauth_id == kakao_id))
    ).first()
    
    if user:
        user.oauth_provider = "kakao"
        user.oauth_id = kakao_id
        user.update_at = datetime.now()
    else:
        user = User(
            email=email,
            password=get_password_hash(secrets.token_urlsafe(32)),
            role=UserRole.USER.value,
            oauth_provider="kakao",
            oauth_id=kakao_id,
            create_at=datetime.now(),
            update_at=datetime.now()
        )
        db.add(user)
    
    tokens = TokenService.create_token_pair(
        user.user_id, user.email, UserRole(user.role)
    )
    user.refresh_token = tokens["refresh_token"]
    db.commit()
    
    return ResponseDTO(
        status=200,
        message="Kakao 로그인 성공",
        data={
            "user_id": user.user_id,
            "email": user.email,
            "role": user.role,
            **tokens
        }
    )


# =========================================================
# 관리자 전용 API
# =========================================================

@router.put("/role", response_model=ResponseDTO)
async def change_user_role(
    req: ChangeRoleRequest,
    current_user: TokenPayload = Depends(AdminOnly),
    db: Session = Depends(get_db)
):
    """
    사용자 역할 변경 (관리자 전용)
    """
    user = db.query(User).filter(User.user_id == req.user_id).first()
    if not user:
        return ResponseDTO(status=404, message="사용자를 찾을 수 없습니다.", data=None)
    
    user.role = req.role.value
    user.update_at = datetime.now()
    db.commit()
    
    return ResponseDTO(
        status=200,
        message=f"사용자 역할이 {req.role.value}(으)로 변경되었습니다.",
        data={
            "user_id": user.user_id,
            "email": user.email,
            "role": user.role
        }
    )


@router.get("/users", response_model=ResponseDTO)
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: TokenPayload = Depends(AdminOnly),
    db: Session = Depends(get_db)
):
    """
    사용자 목록 조회 (관리자 전용)
    """
    offset = (page - 1) * limit
    users = db.query(User).offset(offset).limit(limit).all()
    total = db.query(User).count()
    
    return ResponseDTO(
        status=200,
        message="사용자 목록 조회 성공",
        data={
            "users": [
                {
                    "user_id": u.user_id,
                    "email": u.email,
                    "role": u.role,
                    "oauth_provider": u.oauth_provider,
                    "create_at": u.create_at.isoformat() if u.create_at else None,
                    "login_attempts": u.login_attempts
                }
                for u in users
            ],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit
            }
        }
    )
