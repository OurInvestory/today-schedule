import os
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Union
from datetime import datetime, timedelta

from app.db.database import get_db
from app.models.schedule import Schedule
from app.schemas.schedule import SaveScheduleRequest, UpdateScheduleRequest, ScheduleResponse
from app.schemas.common import ResponseDTO

from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build


router = APIRouter(prefix="/api/schedules", tags=["Schedule"])


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


# 일정 저장
@router.post("", response_model=ResponseDTO)
def save_schedules(
    obj_in: Union[SaveScheduleRequest, List[SaveScheduleRequest]], 
    db: Session = Depends(get_db)
):
    test_user_id = "7822a162-788d-4f36-9366-c956a68393e1" 

    items = obj_in if isinstance(obj_in, list) else [obj_in]
    saved_schedules = []

    try:
        for item in items:
            new_schedule = Schedule(
                user_id=test_user_id,
                title=item.title,
                type=item.type,
                category=item.category,
                start_at=item.start_at,
                end_at=item.end_at,
                priority_score=item.priority_score,
                original_text=item.original_text,
                update_text=None,
                estimated_minute=item.estimated_minute,
                source='manual'  # 수동 추가 일정
            )
            db.add(new_schedule)
            saved_schedules.append(new_schedule)
        
        db.commit()
        for schedule in saved_schedules:
            db.refresh(schedule)

        return ResponseDTO(
            status=200,
            message="일정 저장에 성공했습니다.",
            data=[ScheduleResponse.from_orm(s) for s in saved_schedules]
        )
    except Exception as e:
        db.rollback()
        return ResponseDTO(status=500, message=f"일정 저장에 실패했습니다 : {str(e)}", data=None)


# 일정 수정
@router.put("/{schedule_id}", response_model=ResponseDTO)
def update_schedule(
    schedule_id: str, 
    obj_in: UpdateScheduleRequest, 
    db: Session = Depends(get_db)
):
    try:
        schedule = db.query(Schedule).filter(Schedule.schedule_id == schedule_id).first()
        
        if not schedule:
            return ResponseDTO(status=404, message="해당 일정을 찾을 수 없습니다.", data=None)

        # Pydantic v1/v2 호환 처리
        update_data = obj_in.dict(exclude_unset=True) if hasattr(obj_in, 'dict') else obj_in.model_dump(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(schedule, key, value)
        
        db.commit()
        db.refresh(schedule)

        return ResponseDTO(
            status=200,
            message="일정 수정에 성공했습니다.",
            data=ScheduleResponse.from_orm(schedule)
        )
    except Exception as e:
        db.rollback()
        return ResponseDTO(status=500, message=f"일정 수정에 실패했습니다 : {str(e)}", data=None)
    
    
# 일정 삭제
@router.delete("/{schedule_id}", response_model=ResponseDTO)
def delete_schedule(schedule_id: str, db: Session = Depends(get_db)):
    try:
        schedule = db.query(Schedule).filter(Schedule.schedule_id == schedule_id).first()
        
        if not schedule:
            return ResponseDTO(status=404, message="해당 일정을 찾을 수 없습니다.", data=None)

        db.delete(schedule)
        db.commit()

        return ResponseDTO(status=200, message="일정 삭제에 성공했습니다.", data=None)
    except Exception as e:
        db.rollback()
        return ResponseDTO(status=500, message=f"일정 삭제에 실패했습니다 : {str(e)}", data=None)


# 일정 조회
@router.get("", response_model=ResponseDTO)
def get_schedules(
    from_date: datetime = Query(..., alias="from", example="2026-06-01"),
    to_date: datetime = Query(..., alias="to", example="2026-06-30"),
    db: Session = Depends(get_db)
):
    try:
        test_user_id = "7822a162-788d-4f36-9366-c956a68393e1"

        schedules = db.query(Schedule).filter(
            and_(
                Schedule.user_id == test_user_id,
                Schedule.end_at >= from_date,
                Schedule.end_at <= to_date
            )
        ).order_by(Schedule.end_at.asc()).all()

        return ResponseDTO(
            status=200,
            message="일정 조회에 성공했습니다.",
            data=[ScheduleResponse.from_orm(s) for s in schedules]
        )
    except Exception as e:
        return ResponseDTO(status=500, message=f"일정 조회에 실패했습니다 : {str(e)}", data=None)
    
    
# Google Calendar에서 현재 과거 1달부터 미래 2달간의 일정을 가져와 저장
@router.get("/google-calendar", response_model=ResponseDTO)
def sync_google_calendar(
    code: str = Query(..., description="Google OAuth authorization code"), 
    db: Session = Depends(get_db)
):
    test_user_id = "7822a162-788d-4f36-9366-c956a68393e1"
    
    try:
        # 인증 코드로 구글 토큰 획득 및 서비스 빌드
        flow = Flow.from_client_config(CLIENT_CONFIG, scopes=SCOPES)
        flow.redirect_uri = REDIRECT_URI
        flow.fetch_token(code=code)
        credentials = flow.credentials
        service = build('calendar', 'v3', credentials=credentials)

        # 시간 범위 설정 (과거 1달 - 미래 2달)
        now = datetime.utcnow()
        time_min = (now - timedelta(days=30)).isoformat() + 'Z'  
        time_max = (now + timedelta(days=60)).isoformat() + 'Z'

        # 구글 캘린더에서 일정 목록 호출
        events_result = service.events().list(
            calendarId='primary', 
            timeMin=time_min, 
            timeMax=time_max,
            singleEvents=True, 
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        saved_schedules = []
        for event in events:
            # 시작/종료 시간 데이터 파싱 (dateTime 우선. 없으면 date 사용)
            start_raw = event['start'].get('dateTime', event['start'].get('date'))
            end_raw = event['end'].get('dateTime', event['end'].get('date'))
            # 파이썬 datetime 객체로 변환
            start_at = datetime.fromisoformat(start_raw.replace('Z', '+00:00'))
            end_at = datetime.fromisoformat(end_raw.replace('Z', '+00:00'))

            # 중복 저장 방지
            exists = db.query(Schedule).filter(
                and_(
                    Schedule.user_id == test_user_id,
                    Schedule.title == event.get('summary'),
                    Schedule.start_at == start_at
                )
            ).first()

            # 일정 데이터 구성 및 저장
            if not exists:
                new_schedule = Schedule(
                    user_id=test_user_id,
                    title=event.get('summary', '제목 없음'),
                    type="event",
                    category="기타",
                    start_at=start_at,
                    end_at=end_at,
                    priority_score=5,   
                    original_text=None,
                    update_text=None,
                    estimated_minute=None,
                    source='google'  # 구글 캘린더 연동 식별
                )
                db.add(new_schedule)
                saved_schedules.append(new_schedule)

        db.commit()
        for s in saved_schedules:
            db.refresh(s)

        return ResponseDTO(
            status=200,
            message="Google Calendar에서 일정 가져오기에 성공했습니다.",
            data=[ScheduleResponse.from_orm(s) for s in saved_schedules]
        )

    except Exception as e:
        db.rollback()
        return ResponseDTO(
            status=500, 
            message=f"Google Calendar 일정 저장에 실패했습니다 : {str(e)}", 
            data=None
        )
