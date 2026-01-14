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

# 고정 schedule_id (sub_task에서 참조용)
SCHEDULE_IDS = {
    "hackathon_ot": "sch-001-hackathon-ot",
    "data_structure": "sch-002-data-structure", 
    "capstone_mid": "sch-003-capstone-mid",
    "algo_study": "sch-004-algo-study",
    "team_meeting": "sch-005-team-meeting",
    "db_exam": "sch-006-db-exam",
    "hackathon_final": "sch-007-hackathon-final",
    "dentist": "sch-008-dentist",
    "gym_pt": "sch-009-gym-pt",
    "standup": "sch-010-standup",
}

def get_seed_schedules():
    """1월 5일~16일 해커톤 기간 일정 데이터 (10개 - 띄엄띄엄)"""
    base_year = 2026
    base_month = 1
    
    schedules = [
        # === 1월 5일 (일) - 해커톤 시작 ===
        {
            "schedule_id": SCHEDULE_IDS["hackathon_ot"],
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
            "schedule_id": SCHEDULE_IDS["data_structure"],
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
            "schedule_id": SCHEDULE_IDS["capstone_mid"],
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
            "schedule_id": SCHEDULE_IDS["algo_study"],
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
            "schedule_id": SCHEDULE_IDS["team_meeting"],
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
            "schedule_id": SCHEDULE_IDS["db_exam"],
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
            "schedule_id": SCHEDULE_IDS["hackathon_final"],
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
            "schedule_id": SCHEDULE_IDS["dentist"],
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
            "schedule_id": SCHEDULE_IDS["gym_pt"],
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
            "schedule_id": SCHEDULE_IDS["standup"],
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
    """1월 5일~16일 해커톤 기간 할 일(SubTask) 데이터 - 모두 일정에 연결됨"""
    base_year = 2026
    base_month = 1
    
    sub_tasks = [
        # === 해커톤 OT (1/5) 관련 할 일 ===
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": SCHEDULE_IDS["hackathon_ot"], "title": "해커톤 팀 역할 분담", "date": date(base_year, base_month, 5), "estimated_minute": 30, "is_done": True, "priority": "high", "category": "대외활동", "tip": "각자 강점 기반으로 분담! 💪"},
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": SCHEDULE_IDS["hackathon_ot"], "title": "프로젝트 초기 설정", "date": date(base_year, base_month, 5), "estimated_minute": 60, "is_done": True, "priority": "high", "category": "대외활동", "tip": "README 먼저 작성하세요 📝"},
        
        # === 자료구조 수업 (1/7) 관련 할 일 ===
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": SCHEDULE_IDS["data_structure"], "title": "이진트리 복습", "date": date(base_year, base_month, 7), "estimated_minute": 45, "is_done": True, "priority": "medium", "category": "수업", "tip": "재귀 호출 흐름 따라가보세요 🌳"},
        
        # === 치과 예약 (1/8) 관련 할 일 ===
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": SCHEDULE_IDS["dentist"], "title": "치과 서류 준비", "date": date(base_year, base_month, 8), "estimated_minute": 15, "is_done": True, "priority": "low", "category": "개인", "tip": "신분증 챙기세요! 🪪"},
        
        # === 캡스톤 중간 발표 (1/9) 관련 할 일 ===
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": SCHEDULE_IDS["capstone_mid"], "title": "DB 스키마 설계", "date": date(base_year, base_month, 9), "estimated_minute": 90, "is_done": True, "priority": "high", "category": "과제", "tip": "ERD 먼저 그려보세요! 📊"},
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": SCHEDULE_IDS["capstone_mid"], "title": "API 개발 완료", "date": date(base_year, base_month, 9), "estimated_minute": 180, "is_done": True, "priority": "high", "category": "과제", "tip": "Swagger 문서화 필수! 📄"},
        
        # === 알고리즘 스터디 (1/11) 관련 할 일 ===
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": SCHEDULE_IDS["algo_study"], "title": "DP 문제 3개 풀기", "date": date(base_year, base_month, 11), "estimated_minute": 90, "is_done": True, "priority": "medium", "category": "스터디", "tip": "점화식부터 세우세요! 🧮"},
        
        # === 헬스장 PT (1/12) 관련 할 일 ===
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": SCHEDULE_IDS["gym_pt"], "title": "운동복 챙기기", "date": date(base_year, base_month, 12), "estimated_minute": 10, "is_done": True, "priority": "low", "category": "운동", "tip": "물도 꼭 가져가세요! 💧"},
        
        # === 해커톤 팀 미팅 (1/13) 관련 할 일 ===
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": SCHEDULE_IDS["team_meeting"], "title": "AI 챗봇 연동", "date": date(base_year, base_month, 13), "estimated_minute": 150, "is_done": True, "priority": "high", "category": "대외활동", "tip": "에러 핸들링 꼼꼼히! 🔧"},
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": SCHEDULE_IDS["team_meeting"], "title": "UI 컴포넌트 개발", "date": date(base_year, base_month, 13), "estimated_minute": 120, "is_done": True, "priority": "medium", "category": "대외활동", "tip": "재사용 가능하게 만드세요 ♻️"},
        
        # === 데이터베이스 기말고사 (1/14) - 오늘 관련 할 일 ===
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": SCHEDULE_IDS["db_exam"], "title": "DB 정규화 복습", "date": date(base_year, base_month, 14), "estimated_minute": 60, "is_done": False, "priority": "high", "category": "시험", "tip": "1NF~3NF 개념 정리! 📚"},
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": SCHEDULE_IDS["db_exam"], "title": "트랜잭션 개념 정리", "date": date(base_year, base_month, 14), "estimated_minute": 45, "is_done": False, "priority": "high", "category": "시험", "tip": "ACID 특성 암기하세요! 🔒"},
        
        # === Google Meet 스탠드업 (1/15) 관련 할 일 ===
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": SCHEDULE_IDS["standup"], "title": "발표 자료 준비", "date": date(base_year, base_month, 15), "estimated_minute": 120, "is_done": False, "priority": "high", "category": "미팅", "tip": "슬라이드당 1분 기준 ⏱️"},
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": SCHEDULE_IDS["standup"], "title": "버그 수정", "date": date(base_year, base_month, 15), "estimated_minute": 60, "is_done": False, "priority": "medium", "category": "미팅", "tip": "콘솔 로그로 추적하세요! 🔍"},
        
        # === 해커톤 발표 (1/16) 관련 할 일 ===
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": SCHEDULE_IDS["hackathon_final"], "title": "🔥 해커톤 데모 시연", "date": date(base_year, base_month, 16), "estimated_minute": 90, "is_done": False, "priority": "high", "category": "팀프로젝트", "tip": "예외 상황 대비하세요! 🚨"},
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": SCHEDULE_IDS["hackathon_final"], "title": "발표 대본 리허설", "date": date(base_year, base_month, 16), "estimated_minute": 30, "is_done": False, "priority": "high", "category": "팀프로젝트", "tip": "타이머 켜고 연습! ⏰"},
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
