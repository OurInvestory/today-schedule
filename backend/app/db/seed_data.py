"""
시드 데이터 - 해커톤 데모용 테스트 데이터
1월 16일 발표를 위한 1월 일정/할 일 데이터
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
    """1월 일정 데이터 (28개)"""
    base_year = 2026
    base_month = 1
    
    schedules = [
        # === 1월 첫째 주 (1-5일) ===
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "새해 목표 설정 미팅",
            "category": "기타",
            "start_at": datetime(base_year, base_month, 2, 10, 0),
            "end_at": datetime(base_year, base_month, 2, 11, 30),
            "priority_score": 7,
            "estimated_minute": 90,
            "source": "manual",
        },
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "알고리즘 복습",
            "category": "수업",
            "start_at": datetime(base_year, base_month, 3, 14, 0),
            "end_at": datetime(base_year, base_month, 3, 16, 0),
            "priority_score": 6,
            "estimated_minute": 120,
            "source": "manual",
        },
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "운동하기",
            "category": "기타",
            "start_at": datetime(base_year, base_month, 4, 18, 0),
            "end_at": datetime(base_year, base_month, 4, 19, 0),
            "priority_score": 3,
            "estimated_minute": 60,
            "source": "manual",
        },
        
        # === 1월 둘째 주 (6-12일) ===
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "프론트엔드 팀 회의",
            "category": "기타",
            "start_at": datetime(base_year, base_month, 6, 10, 0),
            "end_at": datetime(base_year, base_month, 6, 11, 0),
            "priority_score": 6,
            "estimated_minute": 60,
            "source": "manual",
        },
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "자료구조 수업",
            "category": "수업",
            "start_at": datetime(base_year, base_month, 7, 9, 0),
            "end_at": datetime(base_year, base_month, 7, 12, 0),
            "priority_score": 5,
            "estimated_minute": 180,
            "source": "manual",
        },
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "task",
            "title": "캡스톤 디자인 중간 발표",
            "category": "과제",
            "start_at": datetime(base_year, base_month, 8, 13, 0),
            "end_at": datetime(base_year, base_month, 8, 15, 0),
            "priority_score": 9,
            "estimated_minute": 120,
            "source": "manual",
        },
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "task",
            "title": "백엔드 API 개발",
            "category": "과제",
            "start_at": datetime(base_year, base_month, 9, 14, 0),
            "end_at": datetime(base_year, base_month, 9, 18, 0),
            "priority_score": 8,
            "estimated_minute": 240,
            "source": "manual",
        },
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "동아리 정기 모임",
            "category": "대외활동",
            "start_at": datetime(base_year, base_month, 10, 18, 0),
            "end_at": datetime(base_year, base_month, 10, 20, 0),
            "priority_score": 4,
            "estimated_minute": 120,
            "source": "manual",
        },
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "운영체제 과제 마감",
            "category": "과제",
            "start_at": datetime(base_year, base_month, 11, 23, 0),
            "end_at": datetime(base_year, base_month, 11, 23, 59),
            "priority_score": 8,
            "estimated_minute": 180,
            "source": "manual",
        },
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "주말 독서",
            "category": "기타",
            "start_at": datetime(base_year, base_month, 12, 14, 0),
            "end_at": datetime(base_year, base_month, 12, 16, 0),
            "priority_score": 2,
            "estimated_minute": 120,
            "source": "manual",
        },
        
        # === 1월 셋째 주 (13-19일) - 해커톤 주간! ===
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "해커톤 팀 미팅",
            "category": "대외활동",
            "start_at": datetime(base_year, base_month, 13, 14, 0),
            "end_at": datetime(base_year, base_month, 13, 16, 0),
            "priority_score": 9,
            "estimated_minute": 120,
            "source": "manual",
        },
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "알고리즘 스터디",
            "category": "스터디",
            "start_at": datetime(base_year, base_month, 13, 19, 0),
            "end_at": datetime(base_year, base_month, 13, 21, 0),
            "priority_score": 6,
            "estimated_minute": 120,
            "source": "manual",
        },
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
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "프로젝트 팀 회의",
            "category": "팀프로젝트",
            "start_at": datetime(base_year, base_month, 14, 15, 0),
            "end_at": datetime(base_year, base_month, 14, 16, 30),
            "priority_score": 7,
            "estimated_minute": 90,
            "source": "manual",
        },
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "운영체제 과제 제출",
            "category": "과제",
            "start_at": datetime(base_year, base_month, 15, 23, 0),
            "end_at": datetime(base_year, base_month, 15, 23, 59),
            "priority_score": 8,
            "estimated_minute": 180,
            "source": "manual",
        },
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
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "컴퓨터 네트워크 수업",
            "category": "수업",
            "start_at": datetime(base_year, base_month, 16, 9, 0),
            "end_at": datetime(base_year, base_month, 16, 12, 0),
            "priority_score": 5,
            "estimated_minute": 180,
            "source": "manual",
        },
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "프로젝트 회고 미팅",
            "category": "기타",
            "start_at": datetime(base_year, base_month, 17, 15, 0),
            "end_at": datetime(base_year, base_month, 17, 16, 30),
            "priority_score": 6,
            "estimated_minute": 90,
            "source": "manual",
        },
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "IBM 공모전 아이디어 제출",
            "category": "공모전",
            "start_at": datetime(base_year, base_month, 18, 18, 0),
            "end_at": datetime(base_year, base_month, 18, 18, 0),
            "priority_score": 9,
            "estimated_minute": 60,
            "source": "manual",
        },
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "머신러닝 수업",
            "category": "수업",
            "start_at": datetime(base_year, base_month, 19, 13, 0),
            "end_at": datetime(base_year, base_month, 19, 16, 0),
            "priority_score": 6,
            "estimated_minute": 180,
            "source": "manual",
        },
        
        # === 1월 넷째 주 (20-26일) ===
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "소프트웨어 공학 수업",
            "category": "수업",
            "start_at": datetime(base_year, base_month, 20, 9, 0),
            "end_at": datetime(base_year, base_month, 20, 12, 0),
            "priority_score": 5,
            "estimated_minute": 180,
            "source": "manual",
        },
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "웹 개발 동아리 모임",
            "category": "대외활동",
            "start_at": datetime(base_year, base_month, 21, 18, 0),
            "end_at": datetime(base_year, base_month, 21, 20, 0),
            "priority_score": 4,
            "estimated_minute": 120,
            "source": "manual",
        },
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "task",
            "title": "React 프로젝트 리팩토링",
            "category": "과제",
            "start_at": datetime(base_year, base_month, 22, 14, 0),
            "end_at": datetime(base_year, base_month, 22, 18, 0),
            "priority_score": 7,
            "estimated_minute": 240,
            "source": "manual",
        },
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "알고리즘 중간고사",
            "category": "시험",
            "start_at": datetime(base_year, base_month, 24, 10, 0),
            "end_at": datetime(base_year, base_month, 24, 12, 0),
            "priority_score": 10,
            "estimated_minute": 120,
            "source": "manual",
        },
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "팀 프로젝트 코드 리뷰",
            "category": "과제",
            "start_at": datetime(base_year, base_month, 25, 14, 0),
            "end_at": datetime(base_year, base_month, 25, 16, 0),
            "priority_score": 7,
            "estimated_minute": 120,
            "source": "manual",
        },
        
        # === 1월 다섯째 주 (27-31일) ===
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "졸업 프로젝트 멘토링",
            "category": "과제",
            "start_at": datetime(base_year, base_month, 27, 14, 0),
            "end_at": datetime(base_year, base_month, 27, 15, 30),
            "priority_score": 8,
            "estimated_minute": 90,
            "source": "manual",
        },
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "데이터베이스 과제 제출",
            "category": "과제",
            "start_at": datetime(base_year, base_month, 28, 23, 0),
            "end_at": datetime(base_year, base_month, 28, 23, 59),
            "priority_score": 9,
            "estimated_minute": 60,
            "source": "manual",
        },
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "친구 생일 파티",
            "category": "기타",
            "start_at": datetime(base_year, base_month, 29, 18, 0),
            "end_at": datetime(base_year, base_month, 29, 21, 0),
            "priority_score": 3,
            "estimated_minute": 180,
            "source": "manual",
        },
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "1월 마무리 회고",
            "category": "기타",
            "start_at": datetime(base_year, base_month, 31, 20, 0),
            "end_at": datetime(base_year, base_month, 31, 21, 0),
            "priority_score": 5,
            "estimated_minute": 60,
            "source": "manual",
        },
        
        # === 구글 캘린더 연동 일정 (source: 'google') ===
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "📅 Google Meet: 팀 스탠드업",
            "category": "미팅",
            "start_at": datetime(base_year, base_month, 13, 9, 0),
            "end_at": datetime(base_year, base_month, 13, 9, 30),
            "priority_score": 6,
            "estimated_minute": 30,
            "source": "google",
        },
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "📅 치과 예약",
            "category": "개인",
            "start_at": datetime(base_year, base_month, 14, 17, 0),
            "end_at": datetime(base_year, base_month, 14, 18, 0),
            "priority_score": 5,
            "estimated_minute": 60,
            "source": "google",
        },
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "📅 친구 결혼식",
            "category": "개인",
            "start_at": datetime(base_year, base_month, 18, 12, 0),
            "end_at": datetime(base_year, base_month, 18, 15, 0),
            "priority_score": 7,
            "estimated_minute": 180,
            "source": "google",
        },
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "📅 Google Meet: 1:1 멘토링",
            "category": "미팅",
            "start_at": datetime(base_year, base_month, 20, 14, 0),
            "end_at": datetime(base_year, base_month, 20, 15, 0),
            "priority_score": 6,
            "estimated_minute": 60,
            "source": "google",
        },
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "📅 엄마 생신",
            "category": "가족",
            "start_at": datetime(base_year, base_month, 22, 18, 0),
            "end_at": datetime(base_year, base_month, 22, 21, 0),
            "priority_score": 9,
            "estimated_minute": 180,
            "source": "google",
        },
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "📅 헬스장 PT",
            "category": "운동",
            "start_at": datetime(base_year, base_month, 15, 7, 0),
            "end_at": datetime(base_year, base_month, 15, 8, 0),
            "priority_score": 4,
            "estimated_minute": 60,
            "source": "google",
        },
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "📅 헬스장 PT",
            "category": "운동",
            "start_at": datetime(base_year, base_month, 17, 7, 0),
            "end_at": datetime(base_year, base_month, 17, 8, 0),
            "priority_score": 4,
            "estimated_minute": 60,
            "source": "google",
        },
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "📅 온라인 세미나: React 19 신기능",
            "category": "학습",
            "start_at": datetime(base_year, base_month, 23, 19, 0),
            "end_at": datetime(base_year, base_month, 23, 21, 0),
            "priority_score": 5,
            "estimated_minute": 120,
            "source": "google",
        },
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "📅 은행 업무 (대출 상담)",
            "category": "개인",
            "start_at": datetime(base_year, base_month, 27, 10, 0),
            "end_at": datetime(base_year, base_month, 27, 11, 0),
            "priority_score": 6,
            "estimated_minute": 60,
            "source": "google",
        },
        {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": "event",
            "title": "📅 Google Meet: 월간 팀 회의",
            "category": "미팅",
            "start_at": datetime(base_year, base_month, 30, 10, 0),
            "end_at": datetime(base_year, base_month, 30, 11, 30),
            "priority_score": 7,
            "estimated_minute": 90,
            "source": "google",
        },
    ]
    
    return schedules

def get_seed_sub_tasks():
    """1월 할 일(SubTask) 데이터 (25개)"""
    base_year = 2026
    base_month = 1
    
    sub_tasks = [
        # === 1월 첫째 주 ===
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "새해 계획표 작성하기", "date": date(base_year, base_month, 1), "estimated_minute": 60, "is_done": True, "priority": "high", "category": "기타"},
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "알고리즘 문제 5개 풀기", "date": date(base_year, base_month, 3), "estimated_minute": 120, "is_done": True, "priority": "medium", "category": "과제"},
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "운동하기 (30분)", "date": date(base_year, base_month, 4), "estimated_minute": 30, "is_done": True, "priority": "low", "category": "기타"},
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "독서 1시간", "date": date(base_year, base_month, 5), "estimated_minute": 60, "is_done": True, "priority": "low", "category": "기타"},
        
        # === 1월 둘째 주 ===
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "캡스톤 발표 자료 준비", "date": date(base_year, base_month, 7), "estimated_minute": 180, "is_done": True, "priority": "high", "category": "과제"},
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "프론트엔드 버그 수정", "date": date(base_year, base_month, 8), "estimated_minute": 90, "is_done": True, "priority": "high", "category": "과제"},
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "자료구조 복습 노트 정리", "date": date(base_year, base_month, 10), "estimated_minute": 60, "is_done": True, "priority": "medium", "category": "수업"},
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "운영체제 과제 코드 작성", "date": date(base_year, base_month, 11), "estimated_minute": 120, "is_done": True, "priority": "high", "category": "과제"},
        
        # === 1월 셋째 주 (해커톤 주간!) ===
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "알고리즘 문제 3문제 풀기", "date": date(base_year, base_month, 13), "estimated_minute": 90, "is_done": False, "priority": "medium", "category": "과제"},
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "발표 자료 최종 점검", "date": date(base_year, base_month, 13), "estimated_minute": 30, "is_done": False, "priority": "high", "category": "팀프로젝트"},
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "데모 시나리오 리허설", "date": date(base_year, base_month, 13), "estimated_minute": 45, "is_done": False, "priority": "high", "category": "팀프로젝트"},
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "팀 회의 자료 준비", "date": date(base_year, base_month, 14), "estimated_minute": 30, "is_done": False, "priority": "medium", "category": "팀프로젝트"},
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "SQL 쿼리 연습문제 풀기", "date": date(base_year, base_month, 14), "estimated_minute": 45, "is_done": False, "priority": "medium", "category": "과제"},
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "DB 정규화 개념 복습", "date": date(base_year, base_month, 14), "estimated_minute": 60, "is_done": False, "priority": "high", "category": "시험"},
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "운영체제 과제 코드 작성", "date": date(base_year, base_month, 15), "estimated_minute": 120, "is_done": False, "priority": "high", "category": "과제"},
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "과제 보고서 작성", "date": date(base_year, base_month, 15), "estimated_minute": 60, "is_done": False, "priority": "high", "category": "과제"},
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "🔥 해커톤 데모 시연 준비", "date": date(base_year, base_month, 16), "estimated_minute": 120, "is_done": False, "priority": "high", "category": "대외활동"},
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "발표 대본 최종 점검", "date": date(base_year, base_month, 16), "estimated_minute": 30, "is_done": False, "priority": "high", "category": "대외활동"},
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "회고 미팅 안건 준비", "date": date(base_year, base_month, 17), "estimated_minute": 30, "is_done": False, "priority": "medium", "category": "기타"},
        
        # === 1월 넷째 주 ===
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "소프트웨어 공학 레포트 작성", "date": date(base_year, base_month, 20), "estimated_minute": 120, "is_done": False, "priority": "medium", "category": "과제"},
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "React 컴포넌트 리팩토링", "date": date(base_year, base_month, 22), "estimated_minute": 180, "is_done": False, "priority": "medium", "category": "과제"},
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "알고리즘 모의고사 풀기", "date": date(base_year, base_month, 23), "estimated_minute": 120, "is_done": False, "priority": "high", "category": "시험"},
        
        # === 1월 다섯째 주 ===
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "졸업 프로젝트 진행 상황 정리", "date": date(base_year, base_month, 27), "estimated_minute": 60, "is_done": False, "priority": "high", "category": "과제"},
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "데이터베이스 쿼리 최적화", "date": date(base_year, base_month, 28), "estimated_minute": 90, "is_done": False, "priority": "high", "category": "과제"},
        {"sub_task_id": str(uuid.uuid4()), "user_id": TEST_USER_ID, "schedule_id": None, "title": "2월 목표 및 계획 수립", "date": date(base_year, base_month, 31), "estimated_minute": 60, "is_done": False, "priority": "medium", "category": "기타"},
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
