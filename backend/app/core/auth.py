"""
RBAC (Role-Based Access Control) - 역할 기반 권한 관리 시스템
"""

from enum import Enum
from typing import List, Optional
from functools import wraps
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# JWT 설정
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


class UserRole(str, Enum):
    """사용자 역할 정의"""
    GUEST = "guest"          # 게스트 (읽기만 가능)
    USER = "user"            # 일반 사용자
    PREMIUM = "premium"      # 프리미엄 사용자 (AI 기능 무제한)
    ADMIN = "admin"          # 관리자


class Permission(str, Enum):
    """권한 정의"""
    # 일정 관련
    SCHEDULE_READ = "schedule:read"
    SCHEDULE_WRITE = "schedule:write"
    SCHEDULE_DELETE = "schedule:delete"
    
    # 강의 관련
    LECTURE_READ = "lecture:read"
    LECTURE_WRITE = "lecture:write"
    LECTURE_DELETE = "lecture:delete"
    
    # AI 기능
    AI_CHAT = "ai:chat"
    AI_VISION = "ai:vision"
    AI_ANALYSIS = "ai:analysis"
    
    # 알림 관련
    NOTIFICATION_READ = "notification:read"
    NOTIFICATION_WRITE = "notification:write"
    
    # 관리자 전용
    ADMIN_USER_MANAGE = "admin:user_manage"
    ADMIN_SYSTEM = "admin:system"


# 역할별 권한 매핑
ROLE_PERMISSIONS = {
    UserRole.GUEST: [
        Permission.SCHEDULE_READ,
        Permission.LECTURE_READ,
        Permission.NOTIFICATION_READ,
    ],
    UserRole.USER: [
        Permission.SCHEDULE_READ,
        Permission.SCHEDULE_WRITE,
        Permission.SCHEDULE_DELETE,
        Permission.LECTURE_READ,
        Permission.LECTURE_WRITE,
        Permission.LECTURE_DELETE,
        Permission.AI_CHAT,
        Permission.NOTIFICATION_READ,
        Permission.NOTIFICATION_WRITE,
    ],
    UserRole.PREMIUM: [
        Permission.SCHEDULE_READ,
        Permission.SCHEDULE_WRITE,
        Permission.SCHEDULE_DELETE,
        Permission.LECTURE_READ,
        Permission.LECTURE_WRITE,
        Permission.LECTURE_DELETE,
        Permission.AI_CHAT,
        Permission.AI_VISION,
        Permission.AI_ANALYSIS,
        Permission.NOTIFICATION_READ,
        Permission.NOTIFICATION_WRITE,
    ],
    UserRole.ADMIN: [
        # 관리자는 모든 권한
        Permission.SCHEDULE_READ,
        Permission.SCHEDULE_WRITE,
        Permission.SCHEDULE_DELETE,
        Permission.LECTURE_READ,
        Permission.LECTURE_WRITE,
        Permission.LECTURE_DELETE,
        Permission.AI_CHAT,
        Permission.AI_VISION,
        Permission.AI_ANALYSIS,
        Permission.NOTIFICATION_READ,
        Permission.NOTIFICATION_WRITE,
        Permission.ADMIN_USER_MANAGE,
        Permission.ADMIN_SYSTEM,
    ],
}


class TokenPayload:
    """JWT 토큰 페이로드"""
    
    def __init__(
        self,
        user_id: str,
        email: str,
        role: UserRole,
        permissions: List[Permission] = None,
        exp: datetime = None,
        token_type: str = "access"
    ):
        self.user_id = user_id
        self.email = email
        self.role = role
        self.permissions = permissions or ROLE_PERMISSIONS.get(role, [])
        self.exp = exp
        self.token_type = token_type
    
    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "email": self.email,
            "role": self.role.value,
            "permissions": [p.value for p in self.permissions],
            "exp": self.exp.timestamp() if self.exp else None,
            "token_type": self.token_type
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "TokenPayload":
        return cls(
            user_id=data["user_id"],
            email=data["email"],
            role=UserRole(data["role"]),
            permissions=[Permission(p) for p in data.get("permissions", [])],
            exp=datetime.fromtimestamp(data["exp"]) if data.get("exp") else None,
            token_type=data.get("token_type", "access")
        )


class TokenService:
    """JWT 토큰 서비스"""
    
    @staticmethod
    def create_access_token(user_id: str, email: str, role: UserRole) -> str:
        """액세스 토큰 생성"""
        exp = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = TokenPayload(
            user_id=user_id,
            email=email,
            role=role,
            exp=exp,
            token_type="access"
        )
        return jwt.encode(payload.to_dict(), SECRET_KEY, algorithm=ALGORITHM)
    
    @staticmethod
    def create_refresh_token(user_id: str, email: str, role: UserRole) -> str:
        """리프레시 토큰 생성"""
        exp = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        payload = TokenPayload(
            user_id=user_id,
            email=email,
            role=role,
            exp=exp,
            token_type="refresh"
        )
        return jwt.encode(payload.to_dict(), SECRET_KEY, algorithm=ALGORITHM)
    
    @staticmethod
    def create_token_pair(user_id: str, email: str, role: UserRole) -> dict:
        """액세스 토큰 + 리프레시 토큰 쌍 생성"""
        return {
            "access_token": TokenService.create_access_token(user_id, email, role),
            "refresh_token": TokenService.create_refresh_token(user_id, email, role),
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # 초 단위
        }
    
    @staticmethod
    def decode_token(token: str) -> Optional[TokenPayload]:
        """토큰 디코딩 및 검증"""
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return TokenPayload.from_dict(data)
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="토큰이 만료되었습니다.")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
    
    @staticmethod
    def refresh_access_token(refresh_token: str) -> dict:
        """리프레시 토큰으로 새 액세스 토큰 발급"""
        payload = TokenService.decode_token(refresh_token)
        
        if payload.token_type != "refresh":
            raise HTTPException(status_code=401, detail="리프레시 토큰이 아닙니다.")
        
        return {
            "access_token": TokenService.create_access_token(
                payload.user_id, payload.email, payload.role
            ),
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }


# HTTP Bearer 인증
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[TokenPayload]:
    """
    현재 사용자 정보 추출 (토큰이 없으면 None)
    """
    if credentials is None:
        return None
    
    return TokenService.decode_token(credentials.credentials)


async def get_current_user_required(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenPayload:
    """
    현재 사용자 정보 추출 (필수 - 토큰 없으면 401)
    """
    if credentials is None:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    
    return TokenService.decode_token(credentials.credentials)


def require_role(roles: List[UserRole]):
    """
    역할 기반 접근 제어 데코레이터
    
    사용법:
    @router.get("/admin")
    @require_role([UserRole.ADMIN])
    async def admin_only(current_user: TokenPayload = Depends(get_current_user_required)):
        ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # current_user 찾기
            current_user = kwargs.get("current_user")
            if current_user is None:
                for arg in args:
                    if isinstance(arg, TokenPayload):
                        current_user = arg
                        break
            
            if current_user is None:
                raise HTTPException(status_code=401, detail="인증이 필요합니다.")
            
            if current_user.role not in roles:
                raise HTTPException(
                    status_code=403, 
                    detail=f"권한이 없습니다. 필요한 역할: {[r.value for r in roles]}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_permission(permissions: List[Permission]):
    """
    권한 기반 접근 제어 데코레이터
    
    사용법:
    @router.post("/ai/analyze")
    @require_permission([Permission.AI_ANALYSIS])
    async def ai_analysis(current_user: TokenPayload = Depends(get_current_user_required)):
        ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if current_user is None:
                for arg in args:
                    if isinstance(arg, TokenPayload):
                        current_user = arg
                        break
            
            if current_user is None:
                raise HTTPException(status_code=401, detail="인증이 필요합니다.")
            
            # 필요한 권한 확인
            user_permissions = set(current_user.permissions)
            required_permissions = set(permissions)
            
            if not required_permissions.issubset(user_permissions):
                missing = required_permissions - user_permissions
                raise HTTPException(
                    status_code=403, 
                    detail=f"권한이 부족합니다. 필요한 권한: {[p.value for p in missing]}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


class RBACChecker:
    """
    FastAPI Depends용 RBAC 체커
    
    사용법:
    @router.get("/admin")
    async def admin_route(
        current_user: TokenPayload = Depends(RBACChecker(roles=[UserRole.ADMIN]))
    ):
        ...
    """
    
    def __init__(
        self, 
        roles: List[UserRole] = None, 
        permissions: List[Permission] = None
    ):
        self.roles = roles or []
        self.permissions = permissions or []
    
    async def __call__(
        self, 
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> TokenPayload:
        if credentials is None:
            raise HTTPException(status_code=401, detail="인증이 필요합니다.")
        
        payload = TokenService.decode_token(credentials.credentials)
        
        # 역할 확인
        if self.roles and payload.role not in self.roles:
            raise HTTPException(
                status_code=403,
                detail=f"권한이 없습니다. 필요한 역할: {[r.value for r in self.roles]}"
            )
        
        # 권한 확인
        if self.permissions:
            user_permissions = set(payload.permissions)
            required = set(self.permissions)
            if not required.issubset(user_permissions):
                missing = required - user_permissions
                raise HTTPException(
                    status_code=403,
                    detail=f"권한이 부족합니다. 필요한 권한: {[p.value for p in missing]}"
                )
        
        return payload


# 편의 함수: 관리자만 접근 가능
AdminOnly = RBACChecker(roles=[UserRole.ADMIN])

# 편의 함수: 프리미엄 이상만 접근 가능
PremiumOnly = RBACChecker(roles=[UserRole.PREMIUM, UserRole.ADMIN])

# 편의 함수: 일반 사용자 이상
UserOnly = RBACChecker(roles=[UserRole.USER, UserRole.PREMIUM, UserRole.ADMIN])

# 별칭: get_current_user_optional (토큰이 없어도 None 반환)
get_current_user_optional = get_current_user
