"""
인증 API 라우터 (회원가입, 로그인, 사용자 정보)
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
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
    ProfileUpdateRequest,
    DeleteAccountRequest,
)
from app.schemas.common import ResponseDTO
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    validate_password_strength,
    check_login_attempts,
    record_login_attempt,
    get_remaining_attempts,
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
    
    # 비밀번호 복잡성 검증
    is_valid, message = validate_password_strength(request.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
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
    # 로그인 시도 제한 확인
    is_allowed, remaining_seconds = check_login_attempts(request.email)
    if not is_allowed:
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"로그인 시도 횟수를 초과했습니다. {minutes}분 {seconds}초 후에 다시 시도해주세요.",
        )
    
    db = db_session()
    try:
        # 사용자 조회
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            record_login_attempt(request.email, False)
            remaining = get_remaining_attempts(request.email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"이메일 또는 비밀번호가 올바르지 않습니다. (남은 시도: {remaining}회)",
            )
        
        # 비밀번호 검증 (해시 또는 평문 둘 다 지원 - 마이그레이션 호환)
        password_valid = False
        try:
            password_valid = verify_password(request.password, user.password)
        except Exception:
            # bcrypt 해시가 아닌 경우 평문 비교 (레거시 지원)
            password_valid = (request.password == user.password)
        
        if not password_valid:
            record_login_attempt(request.email, False)
            remaining = get_remaining_attempts(request.email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"이메일 또는 비밀번호가 올바르지 않습니다. (남은 시도: {remaining}회)",
            )
        
        # 로그인 성공 기록
        record_login_attempt(request.email, True)
        
        # 토큰 생성
        access_token = create_access_token(data={"sub": user.user_id})
        refresh_token = create_refresh_token(data={"sub": user.user_id})
        
        return ResponseDTO(
            status=200,
            message="로그인 성공",
            data=TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                user=UserInfo(
                    user_id=user.user_id,
                    email=user.email,
                    name=user.name,
                    school=user.school,
                    department=user.department,
                    grade=user.grade,
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
            name=current_user.name,
            school=current_user.school,
            department=current_user.department,
            grade=current_user.grade,
            created_at=current_user.create_at,
            updated_at=current_user.update_at,
        ).model_dump(),
    )


@router.put("/profile", response_model=ResponseDTO)
def update_profile(
    request: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
):
    """프로필 업데이트"""
    db = db_session()
    try:
        user = db.query(User).filter(User.user_id == current_user.user_id).first()
        
        if request.name is not None:
            user.name = request.name
        if request.school is not None:
            user.school = request.school
        if request.department is not None:
            user.department = request.department
        if request.grade is not None:
            user.grade = request.grade
        
        user.update_at = datetime.now()
        db.commit()
        db.refresh(user)
        
        return ResponseDTO(
            status=200,
            message="프로필이 업데이트되었습니다.",
            data=UserResponse(
                user_id=user.user_id,
                email=user.email,
                name=user.name,
                school=user.school,
                department=user.department,
                grade=user.grade,
                created_at=user.create_at,
                updated_at=user.update_at,
            ).model_dump(),
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"프로필 업데이트 중 오류가 발생했습니다: {str(e)}",
        )
    finally:
        db.close()


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
    
    # 비밀번호 복잡성 검증
    is_valid, message = validate_password_strength(request.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
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


@router.post("/refresh", response_model=ResponseDTO)
def refresh_token(refresh_token: str = Query(..., description="리프레시 토큰")):
    """토큰 갱신"""
    payload = decode_access_token(refresh_token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않거나 만료된 리프레시 토큰입니다.",
        )
    
    # 리프레시 토큰인지 확인
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효한 리프레시 토큰이 아닙니다.",
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰에 사용자 정보가 없습니다.",
        )
    
    db = db_session()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="사용자를 찾을 수 없습니다.",
            )
        
        # 새 토큰 생성
        new_access_token = create_access_token(data={"sub": user.user_id})
        new_refresh_token = create_refresh_token(data={"sub": user.user_id})
        
        return ResponseDTO(
            status=200,
            message="토큰이 갱신되었습니다.",
            data={
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
            },
        )
    finally:
        db.close()


@router.delete("/account", response_model=ResponseDTO)
def delete_account(
    request: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
):
    """계정 삭제"""
    # 비밀번호 확인
    password_valid = False
    try:
        password_valid = verify_password(request.password, current_user.password)
    except Exception:
        # 레거시 평문 비밀번호 지원
        password_valid = (request.password == current_user.password)
    
    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비밀번호가 올바르지 않습니다.",
        )
    
    db = db_session()
    try:
        user = db.query(User).filter(User.user_id == current_user.user_id).first()
        db.delete(user)
        db.commit()
        
        return ResponseDTO(
            status=200,
            message="계정이 삭제되었습니다.",
            data=None,
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"계정 삭제 중 오류가 발생했습니다: {str(e)}",
        )
    finally:
        db.close()
