"""
보안 및 인증 관련 유틸리티
JWT 토큰 생성/검증, 비밀번호 해싱
"""

import os
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple
from passlib.context import CryptContext
import jwt
from dotenv import load_dotenv

load_dotenv()

# JWT 설정
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-very-long-and-secure")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24시간
REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7일

# 비밀번호 해싱
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 로그인 시도 제한 (메모리 기반 - 실무에서는 Redis 권장)
login_attempts = {}
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """비밀번호 해싱"""
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    비밀번호 복잡성 검증
    - 최소 8자
    - 영문 포함
    - 숫자 포함
    """
    if len(password) < 8:
        return False, "비밀번호는 최소 8자 이상이어야 합니다."
    
    if not re.search(r'[A-Za-z]', password):
        return False, "비밀번호에 영문자가 포함되어야 합니다."
    
    if not re.search(r'\d', password):
        return False, "비밀번호에 숫자가 포함되어야 합니다."
    
    return True, "OK"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """JWT 액세스 토큰 생성"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "type": "access",
        "iat": datetime.utcnow(),
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """JWT 리프레시 토큰 생성"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "iat": datetime.utcnow(),
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """JWT 토큰 디코드"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def check_login_attempts(email: str) -> Tuple[bool, int]:
    """
    로그인 시도 횟수 확인
    Returns: (is_allowed, remaining_seconds)
    """
    if email not in login_attempts:
        return True, 0
    
    attempts, locked_until = login_attempts[email]
    
    # 잠금 해제 시간이 지났으면 초기화
    if locked_until and datetime.utcnow() > locked_until:
        del login_attempts[email]
        return True, 0
    
    # 잠금 상태 확인
    if locked_until:
        remaining = int((locked_until - datetime.utcnow()).total_seconds())
        return False, remaining
    
    return True, 0


def record_login_attempt(email: str, success: bool):
    """로그인 시도 기록"""
    if success:
        # 성공 시 기록 삭제
        if email in login_attempts:
            del login_attempts[email]
        return
    
    # 실패 시 기록
    if email not in login_attempts:
        login_attempts[email] = [1, None]
    else:
        attempts, _ = login_attempts[email]
        attempts += 1
        
        # 최대 시도 횟수 초과 시 잠금
        if attempts >= MAX_LOGIN_ATTEMPTS:
            locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            login_attempts[email] = [attempts, locked_until]
        else:
            login_attempts[email] = [attempts, None]


def get_remaining_attempts(email: str) -> int:
    """남은 로그인 시도 횟수 반환"""
    if email not in login_attempts:
        return MAX_LOGIN_ATTEMPTS
    
    attempts, _ = login_attempts[email]
    return max(0, MAX_LOGIN_ATTEMPTS - attempts)
