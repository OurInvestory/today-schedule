"""
추가 시드 데이터 삽입 스크립트
기존 데이터에 더 많은 일정/할 일을 추가합니다.
"""

import requests
from datetime import datetime, date
import json

BASE_URL = "http://localhost:8000/api"

# 추가할 일정 데이터
additional_schedules = [
    # 1월 1-5일
    {"title": "새해 목표 설정 미팅", "category": "기타", "start_at": "2026-01-02T10:00:00", "end_at": "2026-01-02T11:30:00", "priority_score": 7, "estimated_minute": 90, "type": "event"},
    {"title": "알고리즘 복습", "category": "수업", "start_at": "2026-01-03T14:00:00", "end_at": "2026-01-03T16:00:00", "priority_score": 6, "estimated_minute": 120, "type": "event"},
    {"title": "운동하기", "category": "기타", "start_at": "2026-01-04T18:00:00", "end_at": "2026-01-04T19:00:00", "priority_score": 3, "estimated_minute": 60, "type": "event"},
    
    # 1월 6-12일
    {"title": "프론트엔드 팀 회의", "category": "기타", "start_at": "2026-01-06T10:00:00", "end_at": "2026-01-06T11:00:00", "priority_score": 6, "estimated_minute": 60, "type": "event"},
    {"title": "자료구조 수업", "category": "수업", "start_at": "2026-01-07T09:00:00", "end_at": "2026-01-07T12:00:00", "priority_score": 5, "estimated_minute": 180, "type": "event"},
    {"title": "캡스톤 디자인 중간 발표", "category": "과제", "start_at": "2026-01-08T13:00:00", "end_at": "2026-01-08T15:00:00", "priority_score": 9, "estimated_minute": 120, "type": "task"},
    {"title": "백엔드 API 개발", "category": "과제", "start_at": "2026-01-09T14:00:00", "end_at": "2026-01-09T18:00:00", "priority_score": 8, "estimated_minute": 240, "type": "task"},
    {"title": "동아리 정기 모임", "category": "대외활동", "start_at": "2026-01-10T18:00:00", "end_at": "2026-01-10T20:00:00", "priority_score": 4, "estimated_minute": 120, "type": "event"},
    {"title": "운영체제 과제 마감", "category": "과제", "start_at": "2026-01-11T23:00:00", "end_at": "2026-01-11T23:59:00", "priority_score": 8, "estimated_minute": 180, "type": "event"},
    {"title": "주말 독서", "category": "기타", "start_at": "2026-01-12T14:00:00", "end_at": "2026-01-12T16:00:00", "priority_score": 2, "estimated_minute": 120, "type": "event"},
    
    # 1월 17-19일 (해커톤 이후)
    {"title": "프로젝트 회고 미팅", "category": "기타", "start_at": "2026-01-17T15:00:00", "end_at": "2026-01-17T16:30:00", "priority_score": 6, "estimated_minute": 90, "type": "event"},
    {"title": "머신러닝 수업", "category": "수업", "start_at": "2026-01-19T13:00:00", "end_at": "2026-01-19T16:00:00", "priority_score": 6, "estimated_minute": 180, "type": "event"},
    
    # 1월 20-26일
    {"title": "소프트웨어 공학 수업", "category": "수업", "start_at": "2026-01-20T09:00:00", "end_at": "2026-01-20T12:00:00", "priority_score": 5, "estimated_minute": 180, "type": "event"},
    {"title": "웹 개발 동아리 모임", "category": "대외활동", "start_at": "2026-01-21T18:00:00", "end_at": "2026-01-21T20:00:00", "priority_score": 4, "estimated_minute": 120, "type": "event"},
    {"title": "React 프로젝트 리팩토링", "category": "과제", "start_at": "2026-01-22T14:00:00", "end_at": "2026-01-22T18:00:00", "priority_score": 7, "estimated_minute": 240, "type": "task"},
    {"title": "알고리즘 중간고사", "category": "시험", "start_at": "2026-01-24T10:00:00", "end_at": "2026-01-24T12:00:00", "priority_score": 10, "estimated_minute": 120, "type": "event"},
    {"title": "팀 프로젝트 코드 리뷰", "category": "과제", "start_at": "2026-01-25T14:00:00", "end_at": "2026-01-25T16:00:00", "priority_score": 7, "estimated_minute": 120, "type": "event"},
    
    # 1월 27-31일
    {"title": "졸업 프로젝트 멘토링", "category": "과제", "start_at": "2026-01-27T14:00:00", "end_at": "2026-01-27T15:30:00", "priority_score": 8, "estimated_minute": 90, "type": "event"},
    {"title": "데이터베이스 과제 제출", "category": "과제", "start_at": "2026-01-28T23:00:00", "end_at": "2026-01-28T23:59:00", "priority_score": 9, "estimated_minute": 60, "type": "event"},
    {"title": "친구 생일 파티", "category": "기타", "start_at": "2026-01-29T18:00:00", "end_at": "2026-01-29T21:00:00", "priority_score": 3, "estimated_minute": 180, "type": "event"},
    {"title": "1월 마무리 회고", "category": "기타", "start_at": "2026-01-31T20:00:00", "end_at": "2026-01-31T21:00:00", "priority_score": 5, "estimated_minute": 60, "type": "event"},
]

# 추가할 할 일 데이터
additional_sub_tasks = [
    # 1월 첫째 주
    {"title": "새해 계획표 작성하기", "date": "2026-01-01", "estimated_minute": 60, "priority": "high", "category": "기타", "is_done": True},
    {"title": "알고리즘 문제 5개 풀기", "date": "2026-01-03", "estimated_minute": 120, "priority": "medium", "category": "과제", "is_done": True},
    {"title": "운동하기 (30분)", "date": "2026-01-04", "estimated_minute": 30, "priority": "low", "category": "기타", "is_done": True},
    {"title": "독서 1시간", "date": "2026-01-05", "estimated_minute": 60, "priority": "low", "category": "기타", "is_done": True},
    
    # 1월 둘째 주
    {"title": "캡스톤 발표 자료 준비", "date": "2026-01-07", "estimated_minute": 180, "priority": "high", "category": "과제", "is_done": True},
    {"title": "프론트엔드 버그 수정", "date": "2026-01-08", "estimated_minute": 90, "priority": "high", "category": "과제", "is_done": True},
    {"title": "자료구조 복습 노트 정리", "date": "2026-01-10", "estimated_minute": 60, "priority": "medium", "category": "수업", "is_done": True},
    {"title": "운영체제 과제 코드 작성", "date": "2026-01-11", "estimated_minute": 120, "priority": "high", "category": "과제", "is_done": True},
    
    # 1월 셋째 주 (해커톤 전후)
    {"title": "해커톤 발표 PPT 제작", "date": "2026-01-15", "estimated_minute": 180, "priority": "high", "category": "대외활동", "is_done": False},
    {"title": "발표 대본 연습하기", "date": "2026-01-15", "estimated_minute": 60, "priority": "high", "category": "대외활동", "is_done": False},
    {"title": "🔥 해커톤 데모 시연 준비", "date": "2026-01-16", "estimated_minute": 120, "priority": "high", "category": "대외활동", "is_done": False},
    {"title": "네트워크 시험 범위 정리", "date": "2026-01-16", "estimated_minute": 90, "priority": "high", "category": "시험", "is_done": False},
    {"title": "회고 미팅 안건 준비", "date": "2026-01-17", "estimated_minute": 30, "priority": "medium", "category": "기타", "is_done": False},
    {"title": "주간 일정 정리", "date": "2026-01-19", "estimated_minute": 20, "priority": "low", "category": "기타", "is_done": False},
    
    # 1월 넷째 주
    {"title": "소프트웨어 공학 레포트 작성", "date": "2026-01-20", "estimated_minute": 120, "priority": "medium", "category": "과제", "is_done": False},
    {"title": "React 컴포넌트 리팩토링", "date": "2026-01-22", "estimated_minute": 180, "priority": "medium", "category": "과제", "is_done": False},
    {"title": "머신러닝 과제 데이터 수집", "date": "2026-01-23", "estimated_minute": 90, "priority": "medium", "category": "과제", "is_done": False},
    {"title": "알고리즘 모의고사 풀기", "date": "2026-01-23", "estimated_minute": 120, "priority": "high", "category": "시험", "is_done": False},
    {"title": "코드 리뷰 피드백 반영", "date": "2026-01-25", "estimated_minute": 60, "priority": "medium", "category": "과제", "is_done": False},
    
    # 1월 다섯째 주
    {"title": "졸업 프로젝트 진행 상황 정리", "date": "2026-01-27", "estimated_minute": 60, "priority": "high", "category": "과제", "is_done": False},
    {"title": "데이터베이스 쿼리 최적화", "date": "2026-01-28", "estimated_minute": 90, "priority": "high", "category": "과제", "is_done": False},
    {"title": "생일 선물 구매하기", "date": "2026-01-29", "estimated_minute": 60, "priority": "low", "category": "기타", "is_done": False},
    {"title": "2월 목표 및 계획 수립", "date": "2026-01-31", "estimated_minute": 60, "priority": "medium", "category": "기타", "is_done": False},
]

def add_schedules():
    """일정 추가"""
    print("📅 일정 추가 중...")
    success_count = 0
    for schedule in additional_schedules:
        try:
            response = requests.post(f"{BASE_URL}/schedules", json=schedule)
            if response.status_code == 200:
                success_count += 1
                print(f"  ✓ {schedule['title']}")
            else:
                print(f"  ✗ {schedule['title']} - {response.text}")
        except Exception as e:
            print(f"  ✗ {schedule['title']} - {e}")
    print(f"✅ 일정 {success_count}/{len(additional_schedules)}개 추가 완료")

def add_sub_tasks():
    """할 일 추가"""
    print("\n✅ 할 일 추가 중...")
    success_count = 0
    for task in additional_sub_tasks:
        try:
            response = requests.post(f"{BASE_URL}/sub-tasks", json=task)
            if response.status_code == 200:
                success_count += 1
                print(f"  ✓ {task['title']}")
            else:
                print(f"  ✗ {task['title']} - {response.text}")
        except Exception as e:
            print(f"  ✗ {task['title']} - {e}")
    print(f"✅ 할 일 {success_count}/{len(additional_sub_tasks)}개 추가 완료")

if __name__ == "__main__":
    print("🌱 추가 시드 데이터 삽입을 시작합니다...\n")
    add_schedules()
    add_sub_tasks()
    print("\n🎉 완료!")
