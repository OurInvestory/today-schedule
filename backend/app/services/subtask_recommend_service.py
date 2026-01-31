"""
할 일 추천 및 일정 세분화 서비스
- AI 기반 할 일 자동 추천
- 일정 → 할 일 세분화
- 빈 시간대 자동 채우기
- 학습 패턴 분석
"""

import os
import json
import logging
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any

import google.generativeai as genai
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models.schedule import Schedule
from app.models.sub_task import SubTask
from app.models.lecture import Lecture

logger = logging.getLogger(__name__)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")

genai.configure(api_key=GOOGLE_API_KEY)


def get_gemini_model():
    """Gemini 모델 인스턴스 반환"""
    return genai.GenerativeModel(
        model_name=GEMINI_MODEL_NAME,
        generation_config={
            "temperature": 0.7,
            "response_mime_type": "application/json"
        }
    )


# ============================================================
# 할 일 추천 기능
# ============================================================

def recommend_subtasks_for_schedule(
    db: Session, 
    user_id: str, 
    schedule_id: str = None,
    schedule_title: str = None,
    category: str = None
) -> List[Dict[str, Any]]:
    """
    일정에 대한 할 일 추천
    - schedule_id가 있으면 해당 일정 기반
    - schedule_title만 있으면 키워드 기반 추천
    """
    # 일정 정보 가져오기
    schedule = None
    if schedule_id:
        schedule = db.query(Schedule).filter(
            and_(Schedule.schedule_id == schedule_id, Schedule.user_id == user_id)
        ).first()
    elif schedule_title:
        schedule = db.query(Schedule).filter(
            and_(
                Schedule.user_id == user_id,
                Schedule.title.ilike(f"%{schedule_title}%")
            )
        ).order_by(Schedule.start_at.desc()).first()
    
    # 기존 할 일 조회 (중복 방지용)
    existing_tasks = []
    if schedule:
        existing_tasks = db.query(SubTask).filter(
            SubTask.schedule_id == schedule.schedule_id
        ).all()
    
    # AI 프롬프트 생성
    context = {
        "schedule_title": schedule.title if schedule else schedule_title,
        "schedule_category": schedule.category if schedule else category,
        "deadline": schedule.end_at.isoformat() if schedule and schedule.end_at else None,
        "existing_tasks": [t.title for t in existing_tasks],
    }
    
    prompt = f"""당신은 대학생 학업 관리 전문가입니다.
다음 일정에 대해 세부 할 일을 추천해주세요.

[일정 정보]
- 제목: {context['schedule_title']}
- 카테고리: {context['schedule_category'] or '기타'}
- 마감일: {context['deadline'] or '미정'}
- 기존 할 일: {', '.join(context['existing_tasks']) if context['existing_tasks'] else '없음'}

[요구사항]
1. 3~5개의 구체적인 할 일을 추천
2. 각 할 일에 예상 소요 시간(분) 포함
3. 우선순위(high/medium/low) 지정
4. 동기부여 팁 포함
5. 기존 할 일과 중복되지 않게

[응답 형식 - JSON]
{{
    "recommendations": [
        {{
            "title": "할 일 제목",
            "estimated_minute": 60,
            "priority": "high",
            "category": "과제",
            "tip": "동기부여 팁 🔥",
            "order": 1
        }}
    ],
    "summary": "추천 요약 메시지"
}}
"""
    
    try:
        model = get_gemini_model()
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        
        # 날짜 계산 (마감일 기준으로 역순 배치)
        if schedule and schedule.end_at:
            deadline = schedule.end_at
            for i, rec in enumerate(result.get("recommendations", [])):
                # 마감일로부터 역순으로 날짜 배정
                days_before = len(result["recommendations"]) - i
                task_date = deadline - timedelta(days=days_before)
                rec["date"] = task_date.strftime("%Y-%m-%d")
                rec["schedule_id"] = str(schedule.schedule_id) if schedule else None
        
        return result
    except Exception as e:
        logger.error(f"SubTask recommendation failed: {e}")
        return {
            "recommendations": [],
            "summary": "할 일 추천 중 오류가 발생했습니다."
        }


def breakdown_schedule_to_subtasks(
    db: Session,
    user_id: str,
    schedule_id: str
) -> Dict[str, Any]:
    """
    일정을 세부 할 일로 분해
    """
    schedule = db.query(Schedule).filter(
        and_(Schedule.schedule_id == schedule_id, Schedule.user_id == user_id)
    ).first()
    
    if not schedule:
        return {"error": "일정을 찾을 수 없습니다.", "subtasks": []}
    
    prompt = f"""당신은 프로젝트 관리 전문가입니다.
다음 일정을 구체적인 할 일로 세분화해주세요.

[일정 정보]
- 제목: {schedule.title}
- 유형: {schedule.type}
- 카테고리: {schedule.category or '기타'}
- 시작: {schedule.start_at.isoformat() if schedule.start_at else '미정'}
- 마감: {schedule.end_at.isoformat() if schedule.end_at else '미정'}
- 예상 소요 시간: {schedule.estimated_minute or 60}분

[요구사항]
1. 일정을 5~8개의 구체적인 단계로 분해
2. 각 단계별 예상 소요 시간 배분
3. 논리적인 순서로 정렬
4. 각 단계에 도움이 되는 팁 포함

[응답 형식 - JSON]
{{
    "subtasks": [
        {{
            "title": "단계별 할 일",
            "estimated_minute": 30,
            "priority": "high",
            "category": "{schedule.category or '기타'}",
            "tip": "실행 팁 💡",
            "order": 1
        }}
    ],
    "total_estimated_minute": 180,
    "summary": "세분화 요약"
}}
"""
    
    try:
        model = get_gemini_model()
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        
        # 날짜 배정
        if schedule.end_at and schedule.start_at:
            total_days = (schedule.end_at - schedule.start_at).days
            if total_days <= 0:
                total_days = 1
            
            subtasks = result.get("subtasks", [])
            for i, task in enumerate(subtasks):
                day_offset = int((i / len(subtasks)) * total_days)
                task_date = schedule.start_at + timedelta(days=day_offset)
                task["date"] = task_date.strftime("%Y-%m-%d")
                task["schedule_id"] = str(schedule.schedule_id)
        
        return result
    except Exception as e:
        logger.error(f"Schedule breakdown failed: {e}")
        return {"error": str(e), "subtasks": []}


# ============================================================
# 빈 시간대 채우기
# ============================================================

def get_gap_times(
    db: Session,
    user_id: str,
    target_date: date
) -> List[Dict[str, Any]]:
    """특정 날짜의 빈 시간대 조회"""
    # 해당 날짜의 강의 조회
    day_name = target_date.strftime("%a").lower()[:3]
    lectures = db.query(Lecture).filter(
        and_(Lecture.user_id == user_id, Lecture.day == day_name)
    ).order_by(Lecture.start_time).all()
    
    # 해당 날짜의 일정 조회
    start_of_day = datetime.combine(target_date, datetime.min.time())
    end_of_day = datetime.combine(target_date, datetime.max.time())
    
    schedules = db.query(Schedule).filter(
        and_(
            Schedule.user_id == user_id,
            Schedule.start_at >= start_of_day,
            Schedule.start_at <= end_of_day
        )
    ).order_by(Schedule.start_at).all()
    
    # 바쁜 시간대 수집
    busy_times = []
    for lecture in lectures:
        busy_times.append({
            "start": lecture.start_time,
            "end": lecture.end_time,
            "title": lecture.title
        })
    for schedule in schedules:
        if schedule.start_at and schedule.end_at:
            busy_times.append({
                "start": schedule.start_at.time(),
                "end": schedule.end_at.time(),
                "title": schedule.title
            })
    
    # 활동 시간대 (09:00 ~ 22:00)
    day_start = datetime.strptime("09:00", "%H:%M").time()
    day_end = datetime.strptime("22:00", "%H:%M").time()
    
    # 빈 시간대 계산
    busy_times.sort(key=lambda x: x["start"])
    gap_times = []
    
    current_time = day_start
    for busy in busy_times:
        if busy["start"] > current_time:
            gap_minutes = (
                datetime.combine(target_date, busy["start"]) - 
                datetime.combine(target_date, current_time)
            ).seconds // 60
            
            if gap_minutes >= 30:  # 30분 이상인 경우만
                gap_times.append({
                    "start": current_time.strftime("%H:%M"),
                    "end": busy["start"].strftime("%H:%M"),
                    "duration_minutes": gap_minutes
                })
        current_time = max(current_time, busy["end"])
    
    # 마지막 빈 시간
    if current_time < day_end:
        gap_minutes = (
            datetime.combine(target_date, day_end) - 
            datetime.combine(target_date, current_time)
        ).seconds // 60
        if gap_minutes >= 30:
            gap_times.append({
                "start": current_time.strftime("%H:%M"),
                "end": day_end.strftime("%H:%M"),
                "duration_minutes": gap_minutes
            })
    
    return gap_times


def recommend_tasks_for_gap_time(
    db: Session,
    user_id: str,
    target_date: date,
    gap_time: Dict[str, Any]
) -> Dict[str, Any]:
    """빈 시간대에 할 일 추천"""
    # 미완료 할 일 조회
    pending_tasks = db.query(SubTask).filter(
        and_(
            SubTask.user_id == user_id,
            SubTask.is_done == False,
            SubTask.date >= target_date
        )
    ).order_by(SubTask.date).limit(10).all()
    
    # 다가오는 일정 조회
    upcoming_schedules = db.query(Schedule).filter(
        and_(
            Schedule.user_id == user_id,
            Schedule.end_at >= datetime.combine(target_date, datetime.min.time()),
            Schedule.end_at <= datetime.combine(target_date + timedelta(days=7), datetime.max.time())
        )
    ).order_by(Schedule.end_at).limit(10).all()
    
    prompt = f"""당신은 시간 관리 전문가입니다.
다음 빈 시간대에 적합한 할 일을 추천해주세요.

[빈 시간대]
- 날짜: {target_date.strftime('%Y-%m-%d (%A)')}
- 시간: {gap_time['start']} ~ {gap_time['end']}
- 사용 가능 시간: {gap_time['duration_minutes']}분

[미완료 할 일]
{chr(10).join([f"- {t.title} (예상 {t.estimated_minute or 60}분, {t.priority})" for t in pending_tasks]) or '없음'}

[다가오는 일정]
{chr(10).join([f"- {s.title} (마감: {s.end_at.strftime('%m/%d')})" for s in upcoming_schedules]) or '없음'}

[요구사항]
1. 빈 시간에 맞는 할 일 2~3개 추천
2. 기존 미완료 할 일 중 적합한 것 우선 추천
3. 새로운 할 일도 추천 가능
4. 시간 배분 포함

[응답 형식 - JSON]
{{
    "recommendations": [
        {{
            "title": "할 일",
            "estimated_minute": 30,
            "priority": "medium",
            "category": "기타",
            "tip": "이 시간대에 딱! ⏰",
            "is_existing": false,
            "existing_id": null
        }}
    ],
    "summary": "추천 요약"
}}
"""
    
    try:
        model = get_gemini_model()
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        
        # 날짜 추가
        for rec in result.get("recommendations", []):
            rec["date"] = target_date.strftime("%Y-%m-%d")
        
        return result
    except Exception as e:
        logger.error(f"Gap time recommendation failed: {e}")
        return {"recommendations": [], "summary": "추천 중 오류 발생"}


# ============================================================
# 학습 패턴 분석
# ============================================================

def analyze_learning_pattern(
    db: Session,
    user_id: str,
    days: int = 7
) -> Dict[str, Any]:
    """학습 패턴 분석"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # 완료된 할 일 조회
    completed_tasks = db.query(SubTask).filter(
        and_(
            SubTask.user_id == user_id,
            SubTask.is_done == True,
            SubTask.date >= start_date.date(),
            SubTask.date <= end_date.date()
        )
    ).all()
    
    # 미완료 할 일 조회
    incomplete_tasks = db.query(SubTask).filter(
        and_(
            SubTask.user_id == user_id,
            SubTask.is_done == False,
            SubTask.date >= start_date.date(),
            SubTask.date <= end_date.date()
        )
    ).all()
    
    # 일정 조회
    schedules = db.query(Schedule).filter(
        and_(
            Schedule.user_id == user_id,
            Schedule.end_at >= start_date,
            Schedule.end_at <= end_date
        )
    ).all()
    
    # 통계 계산
    total_tasks = len(completed_tasks) + len(incomplete_tasks)
    completion_rate = (len(completed_tasks) / total_tasks * 100) if total_tasks > 0 else 0
    
    # 카테고리별 완료율
    category_stats = {}
    all_tasks = completed_tasks + incomplete_tasks
    for task in all_tasks:
        cat = task.category or "기타"
        if cat not in category_stats:
            category_stats[cat] = {"completed": 0, "total": 0}
        category_stats[cat]["total"] += 1
        if task.is_done:
            category_stats[cat]["completed"] += 1
    
    for cat in category_stats:
        stats = category_stats[cat]
        stats["rate"] = round(stats["completed"] / stats["total"] * 100) if stats["total"] > 0 else 0
    
    # 가장 미룬 카테고리
    most_delayed = max(
        category_stats.items(),
        key=lambda x: x[1]["total"] - x[1]["completed"],
        default=(None, {"total": 0, "completed": 0})
    )
    
    # AI 분석 및 제안
    prompt = f"""당신은 학습 코치입니다.
다음 학습 패턴을 분석하고 개선 제안을 해주세요.

[지난 {days}일 통계]
- 전체 완료율: {completion_rate:.1f}%
- 완료한 할 일: {len(completed_tasks)}개
- 미완료 할 일: {len(incomplete_tasks)}개
- 카테고리별 현황: {json.dumps(category_stats, ensure_ascii=False)}
- 가장 미룬 카테고리: {most_delayed[0] or '없음'}

[요구사항]
1. 긍정적인 피드백으로 시작
2. 개선이 필요한 부분 1~2가지 제안
3. 구체적인 실천 방법 제시
4. 동기부여 메시지 포함

[응답 형식 - JSON]
{{
    "overall_feedback": "전체 피드백",
    "strengths": ["잘한 점 1", "잘한 점 2"],
    "improvements": [
        {{
            "area": "개선 영역",
            "suggestion": "구체적 제안",
            "tip": "실천 팁"
        }}
    ],
    "motivation": "동기부여 메시지 💪"
}}
"""
    
    try:
        model = get_gemini_model()
        response = model.generate_content(prompt)
        ai_analysis = json.loads(response.text)
    except Exception as e:
        logger.error(f"Pattern analysis failed: {e}")
        ai_analysis = {
            "overall_feedback": "분석 중 오류가 발생했습니다.",
            "strengths": [],
            "improvements": [],
            "motivation": "화이팅! 💪"
        }
    
    return {
        "period": f"{start_date.strftime('%m/%d')} ~ {end_date.strftime('%m/%d')}",
        "statistics": {
            "completion_rate": round(completion_rate, 1),
            "completed_count": len(completed_tasks),
            "incomplete_count": len(incomplete_tasks),
            "total_schedules": len(schedules),
            "category_stats": category_stats,
            "most_delayed_category": most_delayed[0]
        },
        "analysis": ai_analysis
    }


# ============================================================
# 반복 일정 생성
# ============================================================

def create_recurring_schedules(
    db: Session,
    user_id: str,
    base_schedule: Dict[str, Any],
    recurrence: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    반복 일정 생성
    recurrence: {
        "type": "weekly" | "daily" | "monthly",
        "interval": 1,  # 1주마다, 1일마다
        "days": ["mon", "wed", "fri"],  # weekly인 경우
        "count": 10,  # 반복 횟수
        "until": "2026-06-30"  # 종료일
    }
    """
    created_schedules = []
    
    recurrence_type = recurrence.get("type", "weekly")
    interval = recurrence.get("interval", 1)
    days = recurrence.get("days", [])
    count = recurrence.get("count", 10)
    until_str = recurrence.get("until")
    
    until_date = datetime.strptime(until_str, "%Y-%m-%d") if until_str else None
    
    # 시작 날짜/시간
    start_at = datetime.fromisoformat(base_schedule.get("start_at").replace("Z", "+00:00"))
    end_at = datetime.fromisoformat(base_schedule.get("end_at").replace("Z", "+00:00"))
    duration = end_at - start_at
    
    day_map = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
    
    current_date = start_at
    created_count = 0
    
    while created_count < count:
        if until_date and current_date > until_date:
            break
        
        should_create = False
        
        if recurrence_type == "daily":
            should_create = True
        elif recurrence_type == "weekly":
            current_day = current_date.strftime("%a").lower()[:3]
            if not days or current_day in days:
                should_create = True
        elif recurrence_type == "monthly":
            if current_date.day == start_at.day:
                should_create = True
        
        if should_create and current_date >= start_at:
            schedule_data = {
                **base_schedule,
                "start_at": current_date.isoformat(),
                "end_at": (current_date + duration).isoformat(),
                "original_text": f"반복 일정 ({created_count + 1}/{count})"
            }
            created_schedules.append(schedule_data)
            created_count += 1
        
        # 다음 날짜로 이동
        if recurrence_type == "daily":
            current_date += timedelta(days=interval)
        elif recurrence_type == "weekly":
            current_date += timedelta(days=1)
        elif recurrence_type == "monthly":
            # 다음 달 같은 날
            next_month = current_date.month + interval
            next_year = current_date.year + (next_month - 1) // 12
            next_month = ((next_month - 1) % 12) + 1
            try:
                current_date = current_date.replace(year=next_year, month=next_month)
            except ValueError:
                # 해당 월에 그 날짜가 없는 경우 (예: 2/30)
                current_date = current_date.replace(year=next_year, month=next_month + 1, day=1)
    
    return created_schedules
