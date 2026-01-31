"""
시드 데이터 - 해커톤 데모용 테스트 데이터
1월 5일~16일 해커톤 기간 동안의 일정/할 일 데이터
- 1월 5~8일: IBM 오프라인 수업
- 1월 9~15일: 온라인 멘토링
- 1월 16일: 해커톤 발표 및 수상
"""

from datetime import datetime, timedelta, date
import uuid
from app.core.security import get_password_hash

# 테스트 사용자 ID (고정)
TEST_USER_ID = "7822a162-788d-4f36-9366-c956a68393e1"
TEST_USER_EMAIL = "demo@five-today.com"
TEST_USER_PASSWORD = "demo1234"

# 고정 schedule_id (sub_task에서 참조용)
SCHEDULE_IDS = {
    "ibm_day1": "sch-001-ibm-offline-day1",
    "ibm_day2": "sch-002-ibm-offline-day2",
    "ibm_day3": "sch-003-ibm-offline-day3",
    "ibm_day4": "sch-004-ibm-offline-day4",
    "mentoring_1": "sch-005-mentoring-1",
    "mentoring_2": "sch-006-mentoring-2",
    "mentoring_3": "sch-007-mentoring-3",
    "hackathon_final": "sch-008-hackathon-final",
    "google_standup": "sch-009-google-standup",
    "google_meeting": "sch-010-google-meeting",
}

def get_seed_user():
    """테스트 사용자 데이터"""
    now = datetime.now()
    return {
        "user_id": TEST_USER_ID,
        "email": TEST_USER_EMAIL,
        "password": get_password_hash(TEST_USER_PASSWORD),  # bcrypt 해시 적용
        "create_at": now,
        "update_at": now,
    }

def get_seed_schedules():
    """해커톤 일정 데이터"""
    base_year = 2026
    base_month = 1
    
    schedules = [
        # === 1월 5~8일: IBM 오프라인 수업 ===
        {
            "schedule_id": SCHEDULE_IDS["ibm_day1"],
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "IBM 오프라인 수업 Day 1",
            "category": "class",
            "start_at": datetime(base_year, base_month, 5, 9, 0),
            "end_at": datetime(base_year, base_month, 5, 18, 0),
            "priority_score": 9,
            "estimated_minute": 540,
            "source": "manual",
        },
        {
            "schedule_id": SCHEDULE_IDS["ibm_day2"],
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "IBM 오프라인 수업 Day 2",
            "category": "class",
            "start_at": datetime(base_year, base_month, 6, 9, 0),
            "end_at": datetime(base_year, base_month, 6, 18, 0),
            "priority_score": 9,
            "estimated_minute": 540,
            "source": "manual",
        },
        {
            "schedule_id": SCHEDULE_IDS["ibm_day3"],
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "IBM 오프라인 수업 Day 3",
            "category": "class",
            "start_at": datetime(base_year, base_month, 7, 9, 0),
            "end_at": datetime(base_year, base_month, 7, 18, 0),
            "priority_score": 9,
            "estimated_minute": 540,
            "source": "manual",
        },
        {
            "schedule_id": SCHEDULE_IDS["ibm_day4"],
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "IBM 오프라인 수업 Day 4",
            "category": "class",
            "start_at": datetime(base_year, base_month, 8, 9, 0),
            "end_at": datetime(base_year, base_month, 8, 18, 0),
            "priority_score": 9,
            "estimated_minute": 540,
            "source": "manual",
        },
        
        # === 1월 9~15일: 온라인 멘토링 ===
        {
            "schedule_id": SCHEDULE_IDS["mentoring_1"],
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "온라인 멘토링 1차",
            "category": "activity",
            "start_at": datetime(base_year, base_month, 10, 14, 0),
            "end_at": datetime(base_year, base_month, 10, 16, 0),
            "priority_score": 8,
            "estimated_minute": 120,
            "source": "manual",
        },
        {
            "schedule_id": SCHEDULE_IDS["mentoring_2"],
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "온라인 멘토링 2차",
            "category": "activity",
            "start_at": datetime(base_year, base_month, 13, 14, 0),
            "end_at": datetime(base_year, base_month, 13, 16, 0),
            "priority_score": 8,
            "estimated_minute": 120,
            "source": "manual",
        },
        {
            "schedule_id": SCHEDULE_IDS["mentoring_3"],
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "온라인 멘토링 3차 (최종)",
            "category": "activity",
            "start_at": datetime(base_year, base_month, 15, 14, 0),
            "end_at": datetime(base_year, base_month, 15, 16, 0),
            "priority_score": 9,
            "estimated_minute": 120,
            "source": "manual",
        },
        
        # === 1월 16일: 해커톤 발표 및 수상 ===
        {
            "schedule_id": SCHEDULE_IDS["hackathon_final"],
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "🔥 캡스톤 해커톤 발표 및 수상",
            "category": "activity",
            "start_at": datetime(base_year, base_month, 16, 14, 0),
            "end_at": datetime(base_year, base_month, 16, 18, 0),
            "priority_score": 10,
            "estimated_minute": 240,
            "source": "manual",
        },
        
        # === 구글 캘린더 연동 일정 ===
        {
            "schedule_id": SCHEDULE_IDS["google_standup"],
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "📅 팀 스탠드업 미팅",
            "category": "team",
            "start_at": datetime(base_year, base_month, 9, 10, 0),
            "end_at": datetime(base_year, base_month, 9, 10, 30),
            "priority_score": 6,
            "estimated_minute": 30,
            "source": "google",
        },
        {
            "schedule_id": SCHEDULE_IDS["google_meeting"],
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "📅 Google Meet: 프로젝트 리뷰",
            "category": "team",
            "start_at": datetime(base_year, base_month, 14, 15, 0),
            "end_at": datetime(base_year, base_month, 14, 16, 0),
            "priority_score": 7,
            "estimated_minute": 60,
            "source": "google",
        },
    ]
    
    return schedules

def get_seed_sub_tasks():
    """할 일(SubTask) 데이터 - 모두 일정에 연결됨 (schedule_id 필수)"""
    base_year = 2026
    base_month = 1
    
    sub_tasks = [
        # === IBM 오프라인 수업 Day 1 (1/5) - 완료 ===
        {"schedule_id": SCHEDULE_IDS["ibm_day1"], "title": "Watsonx.ai 환경 설정", "date": date(base_year, base_month, 5), "estimated_minute": 60, "is_done": True, "priority": "high", "category": "class", "tip": "API 키 미리 발급받으세요! 🔑"},
        {"schedule_id": SCHEDULE_IDS["ibm_day1"], "title": "LLM 기초 실습", "date": date(base_year, base_month, 5), "estimated_minute": 90, "is_done": True, "priority": "high", "category": "class", "tip": "프롬프트 엔지니어링 핵심! ✨"},
        
        # === IBM 오프라인 수업 Day 2 (1/6) - 완료 ===
        {"schedule_id": SCHEDULE_IDS["ibm_day2"], "title": "RAG 아키텍처 학습", "date": date(base_year, base_month, 6), "estimated_minute": 120, "is_done": True, "priority": "high", "category": "class", "tip": "벡터 DB 개념 정리! 📚"},
        {"schedule_id": SCHEDULE_IDS["ibm_day2"], "title": "팀 프로젝트 기획", "date": date(base_year, base_month, 6), "estimated_minute": 60, "is_done": True, "priority": "medium", "category": "class", "tip": "역할 분담 명확하게! 👥"},
        
        # === IBM 오프라인 수업 Day 3 (1/7) - 완료 ===
        {"schedule_id": SCHEDULE_IDS["ibm_day3"], "title": "백엔드 API 개발", "date": date(base_year, base_month, 7), "estimated_minute": 180, "is_done": True, "priority": "high", "category": "class", "tip": "FastAPI 문서화 필수! 📝"},
        {"schedule_id": SCHEDULE_IDS["ibm_day3"], "title": "프론트엔드 UI 구현", "date": date(base_year, base_month, 7), "estimated_minute": 150, "is_done": True, "priority": "high", "category": "class", "tip": "컴포넌트 재사용하세요! ♻️"},
        
        # === IBM 오프라인 수업 Day 4 (1/8) - 완료 ===
        {"schedule_id": SCHEDULE_IDS["ibm_day4"], "title": "AI 챗봇 연동", "date": date(base_year, base_month, 8), "estimated_minute": 120, "is_done": True, "priority": "high", "category": "class", "tip": "에러 핸들링 꼼꼼히! 🔧"},
        {"schedule_id": SCHEDULE_IDS["ibm_day4"], "title": "시연 데모 준비", "date": date(base_year, base_month, 8), "estimated_minute": 60, "is_done": True, "priority": "medium", "category": "class", "tip": "시나리오 미리 작성! 🎬"},
        
        # === 팀 스탠드업 (1/9 구글) - 완료 ===
        {"schedule_id": SCHEDULE_IDS["google_standup"], "title": "진행 상황 정리", "date": date(base_year, base_month, 9), "estimated_minute": 15, "is_done": True, "priority": "medium", "category": "team", "tip": "간단명료하게! 📋"},
        
        # === 온라인 멘토링 1차 (1/10) - 완료 ===
        {"schedule_id": SCHEDULE_IDS["mentoring_1"], "title": "멘토 피드백 정리", "date": date(base_year, base_month, 10), "estimated_minute": 30, "is_done": True, "priority": "high", "category": "activity", "tip": "핵심 피드백 메모! 📝"},
        {"schedule_id": SCHEDULE_IDS["mentoring_1"], "title": "개선점 반영", "date": date(base_year, base_month, 10), "estimated_minute": 90, "is_done": True, "priority": "high", "category": "activity", "tip": "우선순위 높은 것부터! 🎯"},
        
        # === 온라인 멘토링 2차 (1/13) - 완료 ===
        {"schedule_id": SCHEDULE_IDS["mentoring_2"], "title": "중간 발표 자료 준비", "date": date(base_year, base_month, 13), "estimated_minute": 120, "is_done": True, "priority": "high", "category": "activity", "tip": "슬라이드 10장 이내! 📊"},
        {"schedule_id": SCHEDULE_IDS["mentoring_2"], "title": "데모 시연 연습", "date": date(base_year, base_month, 13), "estimated_minute": 60, "is_done": True, "priority": "medium", "category": "activity", "tip": "타이머 켜고 연습! ⏱️"},
        
        # === 구글 프로젝트 리뷰 (1/14) - 오늘 ===
        {"schedule_id": SCHEDULE_IDS["google_meeting"], "title": "리뷰 준비 자료 작성", "date": date(base_year, base_month, 14), "estimated_minute": 45, "is_done": False, "priority": "high", "category": "team", "tip": "핵심 성과 위주로! 🏆"},
        {"schedule_id": SCHEDULE_IDS["google_meeting"], "title": "버그 수정", "date": date(base_year, base_month, 14), "estimated_minute": 60, "is_done": False, "priority": "medium", "category": "team", "tip": "콘솔 로그 확인! 🔍"},
        
        # === 온라인 멘토링 3차 최종 (1/15) ===
        {"schedule_id": SCHEDULE_IDS["mentoring_3"], "title": "최종 발표 자료 완성", "date": date(base_year, base_month, 15), "estimated_minute": 120, "is_done": False, "priority": "high", "category": "activity", "tip": "15분 발표 기준! 📽️"},
        {"schedule_id": SCHEDULE_IDS["mentoring_3"], "title": "발표 대본 작성", "date": date(base_year, base_month, 15), "estimated_minute": 60, "is_done": False, "priority": "high", "category": "activity", "tip": "키워드만 메모! 🗒️"},
        
        # === 해커톤 발표 및 수상 (1/16) ===
        {"schedule_id": SCHEDULE_IDS["hackathon_final"], "title": "🔥 해커톤 데모 시연", "date": date(base_year, base_month, 16), "estimated_minute": 90, "is_done": False, "priority": "high", "category": "activity", "tip": "예외 상황 대비하세요! 🚨"},
        {"schedule_id": SCHEDULE_IDS["hackathon_final"], "title": "발표 리허설", "date": date(base_year, base_month, 16), "estimated_minute": 30, "is_done": False, "priority": "high", "category": "activity", "tip": "목소리 크게! 📢"},
        {"schedule_id": SCHEDULE_IDS["hackathon_final"], "title": "시상식 참석", "date": date(base_year, base_month, 16), "estimated_minute": 60, "is_done": False, "priority": "medium", "category": "activity", "tip": "수상 소감 준비! 🎉"},
    ]
    
    # user_id와 sub_task_id 자동 추가
    for task in sub_tasks:
        task["sub_task_id"] = str(uuid.uuid4())
        task["user_id"] = TEST_USER_ID
    
    return sub_tasks


def get_seed_notifications():
    """알림 시드 데이터"""
    base_year = 2026
    base_month = 1
    now = datetime.now()
    
    notifications = [
        {
            "notification_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "schedule_id": SCHEDULE_IDS["hackathon_final"],
            "message": "🔥 해커톤 발표가 30분 후에 시작됩니다! 최종 점검하세요!",
            "notify_at": now - timedelta(hours=2),
            "is_sent": True,
            "is_checked": False,
        },
        {
            "notification_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "schedule_id": SCHEDULE_IDS["mentoring_3"],
            "message": "📹 멘토링 세션이 1시간 후에 시작됩니다. 질문 목록 준비하세요!",
            "notify_at": now - timedelta(hours=5),
            "is_sent": True,
            "is_checked": False,
        },
        {
            "notification_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "schedule_id": None,
            "message": "🌅 오늘 일정 3개, 긴급 1개! 화이팅하세요! 💪",
            "notify_at": now - timedelta(days=1),
            "is_sent": True,
            "is_checked": True,
        },
    ]
    
    return notifications


def seed_database(db):
    """데이터베이스에 시드 데이터 삽입"""
    from app.models.user import User
    from app.models.schedule import Schedule
    from app.models.sub_task import SubTask
    from app.models.notification import Notification
    
    # 테스트 사용자가 이미 있는지 확인
    existing_user = db.query(User).filter(User.user_id == TEST_USER_ID).first()
    
    if existing_user:
        # 알림 데이터가 없으면 알림만 추가
        existing_notifications = db.query(Notification).filter(Notification.user_id == TEST_USER_ID).count()
        if existing_notifications == 0:
            print("🔔 알림 시드 데이터를 추가합니다...")
            try:
                notifications = get_seed_notifications()
                for n_data in notifications:
                    notification = Notification(**n_data)
                    db.add(notification)
                db.commit()
                print(f"  ✓ 알림 {len(notifications)}개 생성")
                return True
            except Exception as e:
                db.rollback()
                print(f"❌ 알림 시드 데이터 삽입 실패: {e}")
                return False
        else:
            print("✅ 시드 데이터가 이미 존재합니다. 건너뜁니다.")
            return False
    
    print("🌱 시드 데이터 삽입을 시작합니다...")
    
    try:
        # 1. 사용자 생성
        user_data = get_seed_user()
        user = User(**user_data)
        db.add(user)
        db.flush()
        print(f"  ✓ 사용자 생성: {user.email}")
        
        # 2. 일정 생성
        schedules = get_seed_schedules()
        for s_data in schedules:
            schedule = Schedule(**s_data)
            db.add(schedule)
        print(f"  ✓ 일정 {len(schedules)}개 생성")
        
        # 3. 할 일 생성
        sub_tasks = get_seed_sub_tasks()
        for t_data in sub_tasks:
            sub_task = SubTask(**t_data)
            db.add(sub_task)
        print(f"  ✓ 할 일 {len(sub_tasks)}개 생성")
        
        # 4. 알림 생성
        notifications = get_seed_notifications()
        for n_data in notifications:
            notification = Notification(**n_data)
            db.add(notification)
        print(f"  ✓ 알림 {len(notifications)}개 생성")
        
        db.commit()
        print("🎉 시드 데이터 삽입 완료!")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ 시드 데이터 삽입 실패: {e}")
        raise e
