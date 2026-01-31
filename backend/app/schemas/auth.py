"""
인증 관련 스키마 (회원가입, 로그인, 토큰)
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# ====== 회원가입 ======
class SignupRequest(BaseModel):
    """회원가입 요청"""
    email: EmailStr = Field(..., description="이메일 주소")
    password: str = Field(..., min_length=6, max_length=100, description="비밀번호 (6자 이상)")
    password_confirm: str = Field(..., description="비밀번호 확인")


class SignupResponse(BaseModel):
    """회원가입 응답"""
    user_id: str
    email: str
    created_at: datetime


# ====== 로그인 ======
class LoginRequest(BaseModel):
    """로그인 요청"""
    email: EmailStr = Field(..., description="이메일 주소")
    password: str = Field(..., description="비밀번호")


class TokenResponse(BaseModel):
    """토큰 응답"""
    access_token: str
    token_type: str = "bearer"
    user: "UserInfo"


class UserInfo(BaseModel):
    """사용자 정보"""
    user_id: str
    email: str
    created_at: Optional[datetime] = None


# ====== 사용자 정보 ======
class UserResponse(BaseModel):
    """사용자 정보 응답"""
    user_id: str
    email: str
    created_at: datetime
    updated_at: datetime


# ====== 비밀번호 변경 ======
class ChangePasswordRequest(BaseModel):
    """비밀번호 변경 요청"""
    current_password: str = Field(..., description="현재 비밀번호")
    new_password: str = Field(..., min_length=6, max_length=100, description="새 비밀번호 (6자 이상)")
    new_password_confirm: str = Field(..., description="새 비밀번호 확인")


# Forward reference 해결
TokenResponse.model_rebuild()
