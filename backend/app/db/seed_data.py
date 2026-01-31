"""
시드 데이터 - 테스트 계정용 데이터
- 강원대학교 2026년 학사일정 (2월~8월)
- 강릉원주대 x 강원대학교 AI 개발자 해커톤 (1월)
"""

from datetime import datetime, timedelta, date
import uuid
from app.core.security import get_password_hash

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
        "password": get_password_hash(TEST_USER_PASSWORD),
        "create_at": now,
        "update_at": now,
        "name": "김강원",
        "school": "강원대학교",
        "department": "컴퓨터공학과",
        "grade": "3",
    }


def get_seed_schedules():
    """일정 데이터 - 해커톤 + 강원대 학사일정"""
    schedules = []
    
    # ========================================
    # 1월 해커톤 일정 (강릉원주대 x 강원대학교 AI 개발자 해커톤)
    # ========================================
    hackathon_schedules = [
        # Day 1 (1/5 월) - 교육 준비
        {"title": "IBM AI 해커톤 오프닝", "category": "activity", "start": (1, 5, 9, 30), "end": (1, 5, 10, 30), "priority": 5, "text": "강릉원주대 x 강원대학교 AI 개발자 해커톤"},
        {"title": "Design Thinking Workshop", "category": "activity", "start": (1, 5, 10, 30), "end": (1, 5, 11, 30), "priority": 4},
        {"title": "Innovation Studio Tour & AI 특강", "category": "activity", "start": (1, 5, 13, 0), "end": (1, 5, 13, 50), "priority": 4},
        {"title": "생성형 AI 개념 이해", "category": "activity", "start": (1, 5, 13, 50), "end": (1, 5, 14, 40), "priority": 4},
        {"title": "IBM watsonx platform 이해", "category": "activity", "start": (1, 5, 15, 0), "end": (1, 5, 15, 50), "priority": 4},
        {"title": "실습개발환경 준비", "category": "activity", "start": (1, 5, 16, 0), "end": (1, 5, 17, 30), "priority": 4},
        
        # Day 2 (1/6 화) - 생성형 AI 실습
        {"title": "Prompt Engineering 개념 이해", "category": "activity", "start": (1, 6, 9, 30), "end": (1, 6, 10, 30), "priority": 4, "text": "생성형 AI 실습"},
        {"title": "Prompt Engineering 실습", "category": "activity", "start": (1, 6, 10, 30), "end": (1, 6, 11, 30), "priority": 4},
        {"title": "생성형 AI를 활용한 서비스 구현 방안 이해 및 실습", "category": "activity", "start": (1, 6, 13, 0), "end": (1, 6, 13, 50), "priority": 4},
        {"title": "RAG Pattern 개념 이해 및 실습", "category": "activity", "start": (1, 6, 13, 50), "end": (1, 6, 14, 40), "priority": 4},
        {"title": "Vector DB 이해 및 실습", "category": "activity", "start": (1, 6, 15, 0), "end": (1, 6, 15, 50), "priority": 4},
        {"title": "서비스 개발 및 배포 환경 이해", "category": "activity", "start": (1, 6, 16, 0), "end": (1, 6, 17, 0), "priority": 4},
        {"title": "조별과제 논의", "category": "team", "start": (1, 6, 17, 0), "end": (1, 6, 17, 30), "priority": 3},
        
        # Day 3 (1/7 수) - Agentic AI 실습
        {"title": "생성형 AI 유즈 케이스 기반 실습 1", "category": "activity", "start": (1, 7, 9, 30), "end": (1, 7, 10, 30), "priority": 4, "text": "Agentic AI 실습"},
        {"title": "생성형 AI 유즈 케이스 기반 실습 2", "category": "activity", "start": (1, 7, 10, 30), "end": (1, 7, 11, 30), "priority": 4},
        {"title": "AI Agent 개념 및 플랫폼 소개", "category": "activity", "start": (1, 7, 13, 0), "end": (1, 7, 13, 50), "priority": 4},
        {"title": "AI Agent 유즈 케이스 기반 실습 1", "category": "activity", "start": (1, 7, 13, 50), "end": (1, 7, 14, 40), "priority": 4},
        {"title": "AI Agent 유즈 케이스 기반 실습 2", "category": "activity", "start": (1, 7, 15, 0), "end": (1, 7, 15, 50), "priority": 4},
        {"title": "AI Agent Orchestration 활용 사례 데모", "category": "activity", "start": (1, 7, 16, 0), "end": (1, 7, 17, 0), "priority": 4},
        {"title": "조별과제 논의", "category": "team", "start": (1, 7, 17, 0), "end": (1, 7, 17, 30), "priority": 3},
        
        # Day 4 (1/8 목) - Project 준비
        {"title": "IBM Client Zero 및 watsonx Challenge 사례 소개", "category": "activity", "start": (1, 8, 9, 30), "end": (1, 8, 10, 30), "priority": 4, "text": "Project 준비"},
        {"title": "watsonx Code Assistant 소개 및 활용 데모", "category": "activity", "start": (1, 8, 10, 30), "end": (1, 8, 11, 30), "priority": 4},
        {"title": "멘토링 및 프로젝트 절차 소개", "category": "activity", "start": (1, 8, 13, 0), "end": (1, 8, 13, 50), "priority": 4},
        {"title": "Design Thinking Workshop", "category": "activity", "start": (1, 8, 13, 50), "end": (1, 8, 14, 40), "priority": 4},
        {"title": "조별 주제 선정", "category": "team", "start": (1, 8, 15, 0), "end": (1, 8, 17, 0), "priority": 5},
        {"title": "조별 과제 준비", "category": "team", "start": (1, 8, 17, 0), "end": (1, 8, 17, 30), "priority": 4},
        
        # Day 5-9 (1/9~14) - Project & Mentoring
        {"title": "해커톤 프로젝트 수행", "category": "team", "start": (1, 9, 9, 0), "end": (1, 14, 18, 0), "priority": 5, "type": "task", "text": "Project & Mentoring 기간"},
        {"title": "멘토링 세션", "category": "activity", "start": (1, 9, 17, 0), "end": (1, 9, 17, 30), "priority": 4},
        
        # Day 10 (1/15 목) - Project 발표
        {"title": "현직자와 질의 응답 1", "category": "activity", "start": (1, 15, 9, 30), "end": (1, 15, 10, 30), "priority": 4, "text": "Project 발표"},
        {"title": "현직자와 질의 응답 2", "category": "activity", "start": (1, 15, 10, 30), "end": (1, 15, 11, 30), "priority": 4},
        {"title": "해커톤 결과 발표", "category": "activity", "start": (1, 15, 13, 50), "end": (1, 15, 14, 40), "priority": 5},
        
        # Day 11 (1/16 금) - 최종 발표 및 시상
        {"title": "해커톤 최종 발표", "category": "activity", "start": (1, 16, 15, 0), "end": (1, 16, 17, 0), "priority": 5, "text": "최종 발표"},
        {"title": "🏆 시상 및 종료", "category": "activity", "start": (1, 16, 17, 0), "end": (1, 16, 17, 30), "priority": 5, "text": "강릉원주대 x 강원대학교 AI 개발자 해커톤 종료"},
    ]
    
    # ========================================
    # 강원대학교 2026년 학사일정 (2월~8월)
    # ========================================
    kangwon_schedules = [
        # 2월
        {"title": "제1차 정시모집 합격자 발표", "category": "other", "start": (2, 6, 10, 0), "end": (2, 6, 18, 0), "priority": 3},
        {"title": "제1차 정시모집 등록", "category": "other", "start": (2, 10, 9, 0), "end": (2, 12, 16, 0), "priority": 3},
        {"title": "제2차 정시모집 합격자 발표", "category": "other", "start": (2, 16, 10, 0), "end": (2, 16, 18, 0), "priority": 3},
        {"title": "제2차 정시모집 등록", "category": "other", "start": (2, 19, 9, 0), "end": (2, 20, 16, 0), "priority": 3},
        {"title": "추가모집 합격자 발표", "category": "other", "start": (2, 25, 10, 0), "end": (2, 25, 18, 0), "priority": 3},
        {"title": "추가모집 등록", "category": "other", "start": (2, 26, 9, 0), "end": (2, 27, 16, 0), "priority": 3},
        {"title": "학위수여식", "category": "activity", "start": (2, 20, 11, 0), "end": (2, 20, 12, 0), "priority": 4},
        
        # 3월
        {"title": "1학기 개강", "category": "class", "start": (3, 2, 9, 0), "end": (3, 2, 18, 0), "priority": 5, "text": "2026학년도 1학기 시작"},
        {"title": "수강신청 정정기간", "category": "class", "start": (3, 2, 9, 0), "end": (3, 6, 17, 0), "priority": 4, "type": "task"},
        {"title": "1학기 등록금 납부기간", "category": "other", "start": (3, 2, 9, 0), "end": (3, 13, 16, 0), "priority": 4},
        {"title": "삼일절 (휴일)", "category": "other", "start": (3, 1, 0, 0), "end": (3, 1, 23, 59), "priority": 2},
        {"title": "수강철회 기간", "category": "class", "start": (3, 23, 9, 0), "end": (3, 27, 17, 0), "priority": 3, "type": "task"},
        
        # 4월
        {"title": "중간고사 기간", "category": "exam", "start": (4, 20, 9, 0), "end": (4, 24, 18, 0), "priority": 5, "type": "task", "text": "1학기 중간고사"},
        
        # 5월
        {"title": "어린이날 (휴일)", "category": "other", "start": (5, 5, 0, 0), "end": (5, 5, 23, 59), "priority": 2},
        {"title": "석가탄신일 (휴일)", "category": "other", "start": (5, 24, 0, 0), "end": (5, 24, 23, 59), "priority": 2},
        {"title": "대동제 (축제)", "category": "activity", "start": (5, 13, 18, 0), "end": (5, 15, 22, 0), "priority": 4, "text": "강원대학교 대동제"},
        
        # 6월
        {"title": "현충일 (휴일)", "category": "other", "start": (6, 6, 0, 0), "end": (6, 6, 23, 59), "priority": 2},
        {"title": "기말고사 기간", "category": "exam", "start": (6, 15, 9, 0), "end": (6, 19, 18, 0), "priority": 5, "type": "task", "text": "1학기 기말고사"},
        {"title": "1학기 종강", "category": "class", "start": (6, 19, 9, 0), "end": (6, 19, 18, 0), "priority": 4},
        {"title": "1학기 성적입력 기간", "category": "class", "start": (6, 22, 9, 0), "end": (6, 26, 17, 0), "priority": 3},
        {"title": "1학기 성적열람 및 이의신청", "category": "class", "start": (6, 29, 9, 0), "end": (7, 1, 17, 0), "priority": 3, "type": "task"},
        
        # 7월
        {"title": "여름방학 시작", "category": "other", "start": (7, 1, 0, 0), "end": (7, 1, 23, 59), "priority": 3, "text": "여름방학"},
        {"title": "계절학기 수강신청", "category": "class", "start": (7, 6, 9, 0), "end": (7, 8, 17, 0), "priority": 3},
        {"title": "하계 계절학기", "category": "class", "start": (7, 13, 9, 0), "end": (8, 7, 18, 0), "priority": 3, "type": "task"},
        
        # 8월
        {"title": "2학기 수강신청", "category": "class", "start": (8, 17, 9, 0), "end": (8, 21, 17, 0), "priority": 4, "type": "task", "text": "2학기 수강신청 기간"},
        {"title": "광복절 (휴일)", "category": "other", "start": (8, 15, 0, 0), "end": (8, 15, 23, 59), "priority": 2},
        {"title": "2학기 개강", "category": "class", "start": (8, 31, 9, 0), "end": (8, 31, 18, 0), "priority": 5, "text": "2026학년도 2학기 시작"},
    ]
    
    # 일정 데이터 변환
    base_year = 2026
    
    for item in hackathon_schedules + kangwon_schedules:
        start = item["start"]
        end = item["end"]
        
        schedule = {
            "schedule_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "type": item.get("type", "event"),
            "title": item["title"],
            "category": item["category"],
            "start_at": datetime(base_year, start[0], start[1], start[2], start[3]),
            "end_at": datetime(base_year, end[0], end[1], end[2], end[3]),
            "priority_score": item["priority"],
            "original_text": item.get("text"),
            "source": "manual",
        }
        schedules.append(schedule)
    
    return schedules


def get_seed_sub_tasks():
    """할 일(SubTask) 데이터"""
    base_year = 2026
    
    sub_tasks = [
        # ========================================
        # 해커톤 관련 할 일
        # ========================================
        # Day 1
        {"title": "노트북 및 개발환경 준비", "date": date(base_year, 1, 5), "estimated_minute": 30, "is_done": True, "priority": "high", "category": "activity", "tip": "충전기 필수! 🔌"},
        {"title": "팀원 연락처 교환", "date": date(base_year, 1, 5), "estimated_minute": 15, "is_done": True, "priority": "medium", "category": "team", "tip": "카카오톡 단톡방 만들기 💬"},
        
        # Day 2
        {"title": "Prompt Engineering 실습 과제 제출", "date": date(base_year, 1, 6), "estimated_minute": 60, "is_done": True, "priority": "high", "category": "assignment", "tip": "다양한 프롬프트 시도해보기! ✨"},
        {"title": "RAG 개념 복습 노트 정리", "date": date(base_year, 1, 6), "estimated_minute": 45, "is_done": True, "priority": "medium", "category": "class", "tip": "벡터 임베딩 이해하기 📚"},
        
        # Day 3
        {"title": "AI Agent 실습 코드 정리", "date": date(base_year, 1, 7), "estimated_minute": 60, "is_done": True, "priority": "high", "category": "assignment", "tip": "GitHub에 푸시하기! 🚀"},
        
        # Day 4
        {"title": "프로젝트 아이디어 브레인스토밍", "date": date(base_year, 1, 8), "estimated_minute": 90, "is_done": True, "priority": "high", "category": "team", "tip": "최소 3개 아이디어 준비 💡"},
        {"title": "팀 역할 분담 정하기", "date": date(base_year, 1, 8), "estimated_minute": 30, "is_done": True, "priority": "high", "category": "team", "tip": "각자 강점 파악하기 👥"},
        
        # Day 5-9 (프로젝트 기간)
        {"title": "백엔드 API 설계", "date": date(base_year, 1, 9), "estimated_minute": 120, "is_done": True, "priority": "high", "category": "assignment", "tip": "FastAPI 문서화 필수! 📝"},
        {"title": "프론트엔드 UI 설계", "date": date(base_year, 1, 9), "estimated_minute": 90, "is_done": True, "priority": "high", "category": "assignment", "tip": "Figma로 목업 만들기 🎨"},
        {"title": "AI 모델 연동 테스트", "date": date(base_year, 1, 10), "estimated_minute": 180, "is_done": True, "priority": "high", "category": "assignment", "tip": "API 키 환경변수로 관리! 🔑"},
        {"title": "데이터베이스 스키마 설계", "date": date(base_year, 1, 10), "estimated_minute": 60, "is_done": True, "priority": "medium", "category": "assignment", "tip": "ERD 다이어그램 그리기 📊"},
        {"title": "MVP 기능 구현", "date": date(base_year, 1, 11), "estimated_minute": 240, "is_done": True, "priority": "high", "category": "assignment", "tip": "핵심 기능부터 구현! 🎯"},
        {"title": "버그 수정 및 테스트", "date": date(base_year, 1, 12), "estimated_minute": 120, "is_done": True, "priority": "high", "category": "assignment", "tip": "에러 핸들링 꼼꼼히! 🔧"},
        {"title": "발표 자료 초안 작성", "date": date(base_year, 1, 13), "estimated_minute": 90, "is_done": True, "priority": "medium", "category": "assignment", "tip": "슬라이드 15장 이내! 📽️"},
        {"title": "데모 시나리오 작성", "date": date(base_year, 1, 14), "estimated_minute": 60, "is_done": True, "priority": "high", "category": "assignment", "tip": "예외 상황 대비하기! 🚨"},
        
        # Day 10
        {"title": "발표 자료 최종 점검", "date": date(base_year, 1, 15), "estimated_minute": 60, "is_done": True, "priority": "high", "category": "assignment", "tip": "오타 확인 필수! ✅"},
        {"title": "발표 리허설", "date": date(base_year, 1, 15), "estimated_minute": 30, "is_done": True, "priority": "high", "category": "team", "tip": "시간 체크하며 연습! ⏱️"},
        
        # Day 11
        {"title": "최종 발표 준비", "date": date(base_year, 1, 16), "estimated_minute": 60, "is_done": True, "priority": "high", "category": "activity", "tip": "긴장 풀고 화이팅! 💪"},
        {"title": "프로젝트 코드 정리 및 README 작성", "date": date(base_year, 1, 16), "estimated_minute": 45, "is_done": True, "priority": "medium", "category": "assignment", "tip": "GitHub 링크 공유! 🔗"},
        
        # ========================================
        # 강원대 학사일정 관련 할 일
        # ========================================
        # 3월 - 개강
        {"title": "수강신청 확인 및 정정", "date": date(base_year, 3, 2), "estimated_minute": 60, "is_done": False, "priority": "high", "category": "class", "tip": "인기 과목 빠르게 신청! ⚡"},
        {"title": "교재 구매", "date": date(base_year, 3, 3), "estimated_minute": 120, "is_done": False, "priority": "medium", "category": "class", "tip": "중고책 먼저 알아보기 📚"},
        {"title": "학기 목표 설정", "date": date(base_year, 3, 2), "estimated_minute": 30, "is_done": False, "priority": "medium", "category": "other", "tip": "SMART 목표 설정하기 🎯"},
        {"title": "등록금 납부 확인", "date": date(base_year, 3, 10), "estimated_minute": 15, "is_done": False, "priority": "high", "category": "other", "tip": "납부 영수증 보관! 💳"},
        {"title": "수강철회 대상 과목 검토", "date": date(base_year, 3, 23), "estimated_minute": 30, "is_done": False, "priority": "medium", "category": "class", "tip": "성적 관리 전략적으로! 📊"},
        
        # 4월 - 중간고사
        {"title": "중간고사 범위 정리", "date": date(base_year, 4, 13), "estimated_minute": 120, "is_done": False, "priority": "high", "category": "exam", "tip": "과목별 출제 범위 체크! 📝"},
        {"title": "중간고사 공부 계획 수립", "date": date(base_year, 4, 14), "estimated_minute": 60, "is_done": False, "priority": "high", "category": "exam", "tip": "D-7부터 집중 모드! 🔥"},
        {"title": "스터디 그룹 결성", "date": date(base_year, 4, 15), "estimated_minute": 30, "is_done": False, "priority": "medium", "category": "class", "tip": "같이 공부하면 효율 UP! 👥"},
        {"title": "기출문제 풀이", "date": date(base_year, 4, 17), "estimated_minute": 180, "is_done": False, "priority": "high", "category": "exam", "tip": "최근 3년치 풀어보기! 📄"},
        
        # 5월 - 축제
        {"title": "대동제 일정 확인", "date": date(base_year, 5, 10), "estimated_minute": 15, "is_done": False, "priority": "low", "category": "activity", "tip": "라인업 체크하기! 🎵"},
        {"title": "팀 프로젝트 중간 점검", "date": date(base_year, 5, 12), "estimated_minute": 90, "is_done": False, "priority": "high", "category": "team", "tip": "진행 상황 공유! 📊"},
        
        # 6월 - 기말고사
        {"title": "기말고사 범위 정리", "date": date(base_year, 6, 8), "estimated_minute": 120, "is_done": False, "priority": "high", "category": "exam", "tip": "중간 이후 내용 집중! 📚"},
        {"title": "기말고사 공부 계획", "date": date(base_year, 6, 9), "estimated_minute": 60, "is_done": False, "priority": "high", "category": "exam", "tip": "과목별 시간 배분! ⏰"},
        {"title": "기말 레포트 제출", "date": date(base_year, 6, 12), "estimated_minute": 180, "is_done": False, "priority": "high", "category": "assignment", "tip": "마감 하루 전 제출! 📮"},
        {"title": "성적 확인 및 이의신청 준비", "date": date(base_year, 6, 29), "estimated_minute": 30, "is_done": False, "priority": "medium", "category": "class", "tip": "채점 기준 확인! 🔍"},
        
        # 7월~8월 - 방학
        {"title": "계절학기 수강 여부 결정", "date": date(base_year, 7, 1), "estimated_minute": 30, "is_done": False, "priority": "medium", "category": "class", "tip": "부족한 학점 채우기! 📖"},
        {"title": "여름방학 계획 수립", "date": date(base_year, 7, 2), "estimated_minute": 60, "is_done": False, "priority": "medium", "category": "other", "tip": "인턴/대외활동 알아보기! 💼"},
        {"title": "2학기 수강신청 준비", "date": date(base_year, 8, 14), "estimated_minute": 90, "is_done": False, "priority": "high", "category": "class", "tip": "시간표 미리 짜두기! 📅"},
        {"title": "2학기 목표 설정", "date": date(base_year, 8, 28), "estimated_minute": 30, "is_done": False, "priority": "medium", "category": "other", "tip": "지난 학기 회고하기! 🎯"},
    ]
    
    # user_id와 sub_task_id 자동 추가
    for task in sub_tasks:
        task["sub_task_id"] = str(uuid.uuid4())
        task["user_id"] = TEST_USER_ID
        task["schedule_id"] = None  # 독립적인 할 일
    
    return sub_tasks


def get_seed_notifications(schedules):
    """알림 시드 데이터
    
    Args:
        schedules: 일정 목록 (schedule_id를 참조하기 위해)
    """
    now = datetime.now()
    
    # 해커톤 최종 발표 일정 찾기
    hackathon_final = None
    semester_start = None
    for s in schedules:
        if "최종 발표" in s.get("title", ""):
            hackathon_final = s
        if "1학기 개강" in s.get("title", ""):
            semester_start = s
    
    notifications = []
    
    # 해커톤 관련 알림 (일정이 있으면 연결)
    if hackathon_final:
        notifications.append({
            "notification_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "schedule_id": hackathon_final["schedule_id"],
            "message": "🏆 강릉원주대 x 강원대학교 AI 개발자 해커톤에서 수상했습니다! 축하합니다!",
            "notify_at": now - timedelta(days=15),
            "is_sent": True,
            "is_checked": False,
        })
    
    # 개강 관련 알림
    if semester_start:
        notifications.append({
            "notification_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "schedule_id": semester_start["schedule_id"],
            "message": "📚 1학기 개강이 한 달 앞으로 다가왔습니다. 수강신청 준비하세요!",
            "notify_at": now - timedelta(days=2),
            "is_sent": True,
            "is_checked": False,
        })
    
    return notifications


def get_seed_lectures():
    """강의 시간표 데이터 (1학기)"""
    from datetime import time
    
    base_year = 2026
    # 1학기 시작: 3월 2일, 종료: 6월 19일 (약 16주)
    semester_start = date(base_year, 3, 2)
    semester_end = date(base_year, 6, 19)
    
    # day 매핑: mon=0, tue=1, wed=2, thu=3, fri=4
    day_map = {"mon": "0", "tue": "1", "wed": "2", "thu": "3", "fri": "4", "sat": "5", "sun": "6"}
    
    lectures = [
        # 월요일
        {"title": "운영체제 (김철수, 공대 301호)", "day": "mon", "start_time": "09:00", "end_time": "10:30"},
        {"title": "알고리즘 (이영희, 공대 201호)", "day": "mon", "start_time": "13:00", "end_time": "14:30"},
        
        # 화요일
        {"title": "데이터베이스 (박민수, 공대 401호)", "day": "tue", "start_time": "10:30", "end_time": "12:00"},
        {"title": "인공지능 (정수연, 공대 501호)", "day": "tue", "start_time": "15:00", "end_time": "16:30"},
        
        # 수요일
        {"title": "운영체제 (김철수, 공대 301호)", "day": "wed", "start_time": "09:00", "end_time": "10:30"},
        {"title": "컴퓨터네트워크 (최지훈, 공대 302호)", "day": "wed", "start_time": "13:00", "end_time": "14:30"},
        
        # 목요일
        {"title": "데이터베이스 (박민수, 공대 401호)", "day": "thu", "start_time": "10:30", "end_time": "12:00"},
        {"title": "인공지능 (정수연, 공대 501호)", "day": "thu", "start_time": "15:00", "end_time": "16:30"},
        
        # 금요일
        {"title": "알고리즘 (이영희, 공대 201호)", "day": "fri", "start_time": "09:00", "end_time": "10:30"},
        {"title": "컴퓨터네트워크 (최지훈, 공대 302호)", "day": "fri", "start_time": "13:00", "end_time": "14:30"},
    ]
    
    now = datetime.now()
    result = []
    for lecture in lectures:
        # 시간 문자열을 time 객체로 변환
        start_h, start_m = map(int, lecture["start_time"].split(":"))
        end_h, end_m = map(int, lecture["end_time"].split(":"))
        
        result.append({
            "lecture_id": str(uuid.uuid4()),
            "user_id": TEST_USER_ID,
            "title": lecture["title"],
            "start_time": time(start_h, start_m),
            "end_time": time(end_h, end_m),
            "start_day": semester_start,
            "end_day": semester_end,
            "week": day_map[lecture["day"]],  # 요일을 숫자로 변환
            "update_text": None,
        })
    
    return result


def seed_database(db, force_reseed=False):
    """데이터베이스에 시드 데이터 삽입
    
    Args:
        db: Database session
        force_reseed: True면 기존 데이터 삭제 후 재삽입
    """
    from app.models.user import User
    from app.models.schedule import Schedule
    from app.models.sub_task import SubTask
    from app.models.notification import Notification
    from app.models.lecture import Lecture
    
    # 테스트 사용자가 이미 있는지 확인
    existing_user = db.query(User).filter(User.user_id == TEST_USER_ID).first()
    
    if existing_user and not force_reseed:
        print("✅ 시드 데이터가 이미 존재합니다. 건너뜁니다.")
        print("   (강제 재삽입: force_reseed=True)")
        return False
    
    if existing_user and force_reseed:
        print("🔄 기존 시드 데이터를 삭제하고 재삽입합니다...")
        try:
            # 기존 데이터 삭제 (순서 중요: 외래키 참조 순서)
            db.query(Notification).filter(Notification.user_id == TEST_USER_ID).delete()
            db.query(SubTask).filter(SubTask.user_id == TEST_USER_ID).delete()
            db.query(Schedule).filter(Schedule.user_id == TEST_USER_ID).delete()
            db.query(Lecture).filter(Lecture.user_id == TEST_USER_ID).delete()
            db.query(User).filter(User.user_id == TEST_USER_ID).delete()
            db.commit()
            print("  ✓ 기존 데이터 삭제 완료")
        except Exception as e:
            db.rollback()
            print(f"❌ 기존 데이터 삭제 실패: {e}")
            raise e
    
    print("🌱 시드 데이터 삽입을 시작합니다...")
    
    try:
        # 1. 사용자 생성
        user_data = get_seed_user()
        user = User(**user_data)
        db.add(user)
        db.flush()
        print(f"  ✓ 사용자 생성: {user.email} ({user.name}, {user.school})")
        
        # 2. 일정 생성
        schedules = get_seed_schedules()
        for s_data in schedules:
            schedule = Schedule(**s_data)
            db.add(schedule)
        print(f"  ✓ 일정 {len(schedules)}개 생성 (해커톤 + 강원대 학사일정)")
        
        # 3. 할 일 생성
        sub_tasks = get_seed_sub_tasks()
        for t_data in sub_tasks:
            sub_task = SubTask(**t_data)
            db.add(sub_task)
        print(f"  ✓ 할 일 {len(sub_tasks)}개 생성")
        
        # 4. 알림 생성 (일정 데이터 필요)
        notifications = get_seed_notifications(schedules)
        for n_data in notifications:
            notification = Notification(**n_data)
            db.add(notification)
        print(f"  ✓ 알림 {len(notifications)}개 생성")
        
        # 5. 강의 시간표 생성
        lectures = get_seed_lectures()
        for l_data in lectures:
            lecture = Lecture(**l_data)
            db.add(lecture)
        print(f"  ✓ 강의 {len(lectures)}개 생성")
        
        db.commit()
        print("🎉 시드 데이터 삽입 완료!")
        print(f"   - 테스트 계정: {TEST_USER_EMAIL} / {TEST_USER_PASSWORD}")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ 시드 데이터 삽입 실패: {e}")
        raise e
