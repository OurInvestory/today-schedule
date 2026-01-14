"""
시드 데이터 - 해커톤 데모용 테스트 데이터
1월 5일~16일 해커톤 기간 동안의 간소화된 일정/할 일 데이터
다른 팀원이 Docker 실행 시 동일한 환경으로 시작할 수 있습니다.
"""

from datetime import datetime, timedelta, date
import uuid

# 테스트 사용자 ID (고정)
TEST_USER_ID = "7822a162-788d-4f36-9366-c956a68393e1"
TEST_USER_EMAIL = "demo@five-today.com"
TEST_USER_PASSWORD = "demo1234"

def get_seed_user():
    """테스트 사용자 데이터"""
    now = datetime.now()
    return {
        "user_id": TEST_USER_ID,
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
        "create_at": now,
        "update_at": now,
    }

def get_seed_schedules():
    """1월 5일~16일 해커톤 기간 일정 데이터 (10개 - 띄엄띄엄)"""
    base_year = 2026
    base_month = 1
    
    schedules = [
        # === 1월 5일 (일) - 해커톤 시작 ===
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "해커톤 OT",
            "category": "대외활동",
            "start_at": datetime(base_year, base_month, 5, 14, 0),
            "end_at": datetime(base_year, base_month, 5, 16, 0),
            "priority_score": 8,
            "estimated_minute": 120,
            "source": "manual",
        },
        
        # === 1월 7일 (화) ===
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "자료구조 수업",
            "category": "수업",
            "start_at": datetime(base_year, base_month, 7, 10, 0),
            "end_at": datetime(base_year, base_month, 7, 12, 0),
            "priority_score": 5,
            "estimated_minute": 120,
            "source": "manual",
        },
        
        # === 1월 9일 (목) ===
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "task",
            "title": "캡스톤 중간 발표",
            "category": "과제",
            "start_at": datetime(base_year, base_month, 9, 14, 0),
            "end_at": datetime(base_year, base_month, 9, 16, 0),
            "priority_score": 9,
            "estimated_minute": 120,
            "source": "manual",
        },
        
        # === 1월 11일 (토) ===
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "알고리즘 스터디",
            "category": "스터디",
            "start_at": datetime(base_year, base_month, 11, 15, 0),
            "end_at": datetime(base_year, base_month, 11, 17, 0),
            "priority_score": 6,
            "estimated_minute": 120,
            "source": "manual",
        },
        
        # === 1월 13일 (월) ===
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "해커톤 팀 미팅",
            "category": "대외활동",
            "start_at": datetime(base_year, base_month, 13, 19, 0),
            "end_at": datetime(base_year, base_month, 13, 21, 0),
            "priority_score": 9,
            "estimated_minute": 120,
            "source": "manual",
        },
        
        # === 1월 14일 (화) ===
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "데이터베이스 기말고사",
            "category": "시험",
            "start_at": datetime(base_year, base_month, 14, 10, 0),
            "end_at": datetime(base_year, base_month, 14, 12, 0),
            "priority_score": 10,
            "estimated_minute": 120,
            "source": "manual",
        },
        
        # === 1월 16일 (목) - 해커톤 발표일 ===
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "task",
            "title": "🔥 캡스톤 해커톤 발표",
            "category": "팀프로젝트",
            "start_at": datetime(base_year, base_month, 16, 14, 0),
            "end_at": datetime(base_year, base_month, 16, 17, 0),
            "priority_score": 10,
            "estimated_minute": 180,
            "source": "manual",
        },
        
        # === 구글 캘린더 연동 일정 (source: 'google') ===
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "📅 치과 예약",
            "category": "개인",
            "start_at": datetime(base_year, base_month, 8, 17, 0),
            "end_at": datetime(base_year, base_month, 8, 18, 0),
            "priority_score": 5,
            "estimated_minute": 60,
            "source": "google",
        },
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "📅 헬스장 PT",
            "category": "운동",
            "start_at": datetime(base_year, base_month, 12, 7, 0),
            "end_at": datetime(base_year, base_month, 12, 8, 0),
            "priority_score": 4,
            "estimated_minute": 60,
            "source": "google",
        },
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "📅 Google Meet: 팀 스탠드업",
            "category": "미팅",
            "start_at": datetime(base_year, base_month, 15, 9, 0),
            "end_at": datetime(base_year, base_month, 15, 9, 30),
            "priority_score": 6,
            "estimated_minute": 30,
            "source": "google",
        },
    ]
    
    return schedules

def get_seed_sub_tasks():
    """1월 5일~16일 해커톤 기간 할 일(SubTask) 데이터 (12개 - 띄엄띄엄)"""
    base_year = 2026
    base_month = 1
    
    sub_tasks = [
        # === 1월 5일 (일) - 해커톤 시작 (완료) ===
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "해커톤 팀 역할 분담", "date": date(base_year, base_month, 5), "estimated_minute": 30, "is_done": True, "priority": "high", "category": "대외활동", "tip": "각자 강점 기반으로 분담하세요!"},
        
        # === 1월 6일 (월) (완료) ===
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "프로젝트 초기 설정", "date": date(base_year, base_month, 6), "estimated_minute": 60, "is_done": True, "priority": "high", "category": "과제", "tip": "README 먼저 작성하면 방향이 명확해져요"},
        
        # === 1월 8일 (수) (완료) ===
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "DB 스키마 설계", "date": date(base_year, base_month, 8), "estimated_minute": 90, "is_done": True, "priority": "high", "category": "과제", "tip": "ERD 먼저 그려보면 실수 줄어요!"},
        
        # === 1월 10일 (금) (완료) ===
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "API 개발 완료", "date": date(base_year, base_month, 10), "estimated_minute": 180, "is_done": True, "priority": "high", "category": "과제", "tip": "Swagger 문서화도 함께 하세요"},
        
        # === 1월 12일 (일) (완료) ===
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "UI 컴포넌트 개발", "date": date(base_year, base_month, 12), "estimated_minute": 120, "is_done": True, "priority": "medium", "category": "과제", "tip": "재사용 가능한 컴포넌트로 만드세요"},
        
        # === 1월 13일 (월) (완료) ===
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "AI 챗봇 연동", "date": date(base_year, base_month, 13), "estimated_minute": 150, "is_done": True, "priority": "high", "category": "과제", "tip": "에러 핸들링 꼼꼼히 하세요"},
        
        # === 1월 14일 (화) - 오늘 (진행 중) ===
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "DB 정규화 복습", "date": date(base_year, base_month, 14), "estimated_minute": 60, "is_done": False, "priority": "high", "category": "시험", "tip": "1NF~3NF 개념 정리가 핵심!"},
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "버그 수정", "date": date(base_year, base_month, 14), "estimated_minute": 60, "is_done": False, "priority": "medium", "category": "과제", "tip": "콘솔 로그로 원인 추적하세요"},
        
        # === 1월 15일 (수) ===
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "발표 자료 준비", "date": date(base_year, base_month, 15), "estimated_minute": 120, "is_done": False, "priority": "high", "category": "팀프로젝트", "tip": "슬라이드당 1분 기준으로 준비"},
        
        # === 1월 16일 (목) - 발표일 ===
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "🔥 해커톤 데모 시연", "date": date(base_year, base_month, 16), "estimated_minute": 90, "is_done": False, "priority": "high", "category": "대외활동", "tip": "시연 중 예외 상황 대비하세요!"},
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "발표 대본 리허설", "date": date(base_year, base_month, 16), "estimated_minute": 30, "is_done": False, "priority": "high", "category": "대외활동", "tip": "타이머 켜고 연습하세요"},
    ]
    
    return sub_tasks


def seed_database(db):
    """데이터베이스에 시드 데이터 삽입"""
    from app.models.user import User
    from app.models.schedule import Schedule
    from app.models.sub_task import SubTask
    
    # 테스트 사용자가 이미 있는지 확인
    existing_user = db.query(User).filter(User.user_id == TEST_USER_ID).first()
    
    if existing_user:
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
        
        db.commit()
        print("🎉 시드 데이터 삽입 완료!")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ 시드 데이터 삽입 실패: {e}")
        raise e
