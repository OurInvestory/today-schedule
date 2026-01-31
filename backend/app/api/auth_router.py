"""
인증 API 라우터 (회원가입, 로그인, 사용자 정보)
"""

from fastapi import APIRouter, HTTPException, Depends, status
from datetime import datetime
import uuid

from app.db.database import db_session
from app.models.user import User
from app.schemas.auth import (
    SignupRequest,
    SignupResponse,
    LoginRequest,
    TokenResponse,
    UserInfo,
    UserResponse,
    ChangePasswordRequest,
)
from app.schemas.common import ResponseDTO
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
)
from app.core.auth import get_current_user


router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/signup", response_model=ResponseDTO)
def signup(request: SignupRequest):
    """회원가입"""
    # 비밀번호 확인 체크
    if request.password != request.password_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비밀번호가 일치하지 않습니다.",
        )
    
    db = db_session()
    try:
        # 이메일 중복 체크
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 가입된 이메일입니다.",
            )
        
        # 새 사용자 생성
        now = datetime.now()
        new_user = User(
            user_id=str(uuid.uuid4()),
            email=request.email,
            password=get_password_hash(request.password),
            create_at=now,
            update_at=now,
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return ResponseDTO(
            status=201,
            message="회원가입이 완료되었습니다.",
            data=SignupResponse(
                user_id=new_user.user_id,
                email=new_user.email,
                created_at=new_user.create_at,
            ).model_dump(),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"회원가입 중 오류가 발생했습니다: {str(e)}",
        )
    finally:
        db.close()


@router.post("/login", response_model=ResponseDTO)
def login(request: LoginRequest):
    """로그인"""
    db = db_session()
    try:
        # 사용자 조회
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 올바르지 않습니다.",
            )
        
        # 비밀번호 검증
        if not verify_password(request.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 올바르지 않습니다.",
            )
        
        # 토큰 생성
        access_token = create_access_token(data={"sub": user.user_id})
        
        return ResponseDTO(
            status=200,
            message="로그인 성공",
            data=TokenResponse(
                access_token=access_token,
                token_type="bearer",
                user=UserInfo(
                    user_id=user.user_id,
                    email=user.email,
                    created_at=user.create_at,
                ),
            ).model_dump(),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"로그인 중 오류가 발생했습니다: {str(e)}",
        )
    finally:
        db.close()


@router.get("/me", response_model=ResponseDTO)
def get_me(current_user: User = Depends(get_current_user)):
    """현재 로그인한 사용자 정보 조회"""
    return ResponseDTO(
        status=200,
        message="사용자 정보 조회 성공",
        data=UserResponse(
            user_id=current_user.user_id,
            email=current_user.email,
            created_at=current_user.create_at,
            updated_at=current_user.update_at,
        ).model_dump(),
    )


@router.put("/password", response_model=ResponseDTO)
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
):
    """비밀번호 변경"""
    # 새 비밀번호 확인
    if request.new_password != request.new_password_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="새 비밀번호가 일치하지 않습니다.",
        )
    
    # 현재 비밀번호 확인
    if not verify_password(request.current_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="현재 비밀번호가 올바르지 않습니다.",
        )
    
    db = db_session()
    try:
        user = db.query(User).filter(User.user_id == current_user.user_id).first()
        user.password = get_password_hash(request.new_password)
        user.update_at = datetime.now()
        db.commit()
        
        return ResponseDTO(
            status=200,
            message="비밀번호가 변경되었습니다.",
            data=None,
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"비밀번호 변경 중 오류가 발생했습니다: {str(e)}",
        )
    finally:
        db.close()


@router.post("/logout", response_model=ResponseDTO)
def logout(current_user: User = Depends(get_current_user)):
    """로그아웃 (클라이언트에서 토큰 삭제)"""
    return ResponseDTO(
        status=200,
        message="로그아웃 되었습니다.",
        data=None,
    )
