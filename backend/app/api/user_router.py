from fastapi import APIRouter
import uuid
from datetime import datetime
from app.db.database import db_session
from app.models.user import User
from app.schemas.common import ResponseDTO


router = APIRouter(prefix="/api/users", tags=["User"])


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