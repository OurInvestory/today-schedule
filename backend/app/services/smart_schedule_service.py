"""
스마트 일정 관리 서비스
- 일정 충돌 감지 및 자동 조정
- 스마트 시간 추천
- 일정 요약 및 브리핑
- 다중 일정 일괄 처리
- 우선순위 자동 조정
"""

import os
import json
import logging
from datetime import datetime, timedelta, date, time
from typing import Optional, List, Dict, Any, Tuple

import google.generativeai as genai
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.schedule import Schedule
from app.models.sub_task import SubTask
from app.models.lecture import Lecture

logger = logging.getLogger(__name__)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")

genai.configure(api_key=GOOGLE_API_KEY)


def get_gemini_model(temperature: float = 0.7):
    """Gemini 모델 인스턴스 반환"""
    return genai.GenerativeModel(
        model_name=GEMINI_MODEL_NAME,
        generation_config={
            "temperature": temperature,
            "response_mime_type": "application/json"
        }
    )


# ============================================================
# 일정 충돌 감지 및 자동 조정
# ============================================================

def detect_schedule_conflicts(
    db: Session,
    user_id: str,
    new_start: datetime,
    new_end: datetime,
    exclude_schedule_id: str = None
) -> List[Dict[str, Any]]:
    """
    새 일정과 충돌하는 기존 일정 감지
    
    Returns:
        충돌하는 일정 목록
    """
    query = db.query(Schedule).filter(
        and_(
            Schedule.user_id == user_id,
            # 시간 범위가 겹치는 경우
            or_(
                # 새 일정이 기존 일정 내에 포함
                and_(Schedule.start_at <= new_start, Schedule.end_at >= new_end),
                # 기존 일정이 새 일정 내에 포함
                and_(Schedule.start_at >= new_start, Schedule.end_at <= new_end),
                # 새 일정 시작이 기존 일정 중간
                and_(Schedule.start_at <= new_start, Schedule.end_at > new_start),
                # 새 일정 끝이 기존 일정 중간
                and_(Schedule.start_at < new_end, Schedule.end_at >= new_end),
            )
        )
    )
    
    if exclude_schedule_id:
        query = query.filter(Schedule.schedule_id != exclude_schedule_id)
    
    conflicts = query.all()
    
    return [
        {
            "schedule_id": s.schedule_id,
            "title": s.title,
            "start_at": s.start_at.isoformat() if s.start_at else None,
            "end_at": s.end_at.isoformat() if s.end_at else None,
            "category": s.category,
            "priority_score": s.priority_score,
        }
        for s in conflicts
    ]


def suggest_alternative_times(
    db: Session,
    user_id: str,
    target_date: date,
    duration_minutes: int,
    preferred_start_hour: int = 9,
    preferred_end_hour: int = 22
) -> List[Dict[str, Any]]:
    """
    충돌 없는 대체 시간대 추천
    
    Args:
        target_date: 대상 날짜
        duration_minutes: 필요한 시간 (분)
        preferred_start_hour: 선호 시작 시간 (기본 9시)
        preferred_end_hour: 선호 종료 시간 (기본 22시)
    
    Returns:
        추천 시간대 목록
    """
    # 해당 날짜의 모든 일정 조회
    day_start = datetime.combine(target_date, time(0, 0))
    day_end = datetime.combine(target_date, time(23, 59, 59))
    
    schedules = db.query(Schedule).filter(
        and_(
            Schedule.user_id == user_id,
            Schedule.start_at >= day_start,
            Schedule.end_at <= day_end
        )
    ).order_by(Schedule.start_at.asc()).all()
    
    # 강의 시간표도 확인
    day_of_week = str(target_date.weekday())  # 0=월, 6=일
    lectures = db.query(Lecture).filter(
        and_(
            Lecture.user_id == user_id,
            Lecture.week == day_of_week,
            Lecture.start_day <= target_date,
            Lecture.end_day >= target_date
        )
    ).all()
    
    # 모든 바쁜 시간대 수집
    busy_slots = []
    for s in schedules:
        if s.start_at and s.end_at:
            busy_slots.append((s.start_at.time(), s.end_at.time()))
    
    for l in lectures:
        busy_slots.append((l.start_time, l.end_time))
    
    # 시간순 정렬
    busy_slots.sort(key=lambda x: x[0])
    
    # 빈 시간대 찾기
    available_slots = []
    current_time = time(preferred_start_hour, 0)
    end_time = time(preferred_end_hour, 0)
    
    for busy_start, busy_end in busy_slots:
        if current_time < busy_start:
            # 빈 시간대 발견
            slot_start = datetime.combine(target_date, current_time)
            slot_end = datetime.combine(target_date, busy_start)
            slot_duration = (slot_end - slot_start).total_seconds() / 60
            
            if slot_duration >= duration_minutes:
                available_slots.append({
                    "start": current_time.strftime("%H:%M"),
                    "end": busy_start.strftime("%H:%M"),
                    "duration_minutes": int(slot_duration),
                    "recommended": slot_duration >= duration_minutes * 1.2  # 20% 여유 있으면 추천
                })
        
        current_time = max(current_time, busy_end)
    
    # 마지막 바쁜 시간 이후의 빈 시간
    if current_time < end_time:
        slot_start = datetime.combine(target_date, current_time)
        slot_end = datetime.combine(target_date, end_time)
        slot_duration = (slot_end - slot_start).total_seconds() / 60
        
        if slot_duration >= duration_minutes:
            available_slots.append({
                "start": current_time.strftime("%H:%M"),
                "end": end_time.strftime("%H:%M"),
                "duration_minutes": int(slot_duration),
                "recommended": slot_duration >= duration_minutes * 1.2
            })
    
    return available_slots


def auto_adjust_schedule(
    db: Session,
    user_id: str,
    schedule_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    충돌 감지 후 자동 조정된 일정 반환
    
    Returns:
        조정된 일정 데이터 + 조정 정보
    """
    start_at = datetime.fromisoformat(schedule_data.get('start_at').replace('Z', '+00:00'))
    end_at = datetime.fromisoformat(schedule_data.get('end_at').replace('Z', '+00:00'))
    duration = int((end_at - start_at).total_seconds() / 60)
    
    # 충돌 확인
    conflicts = detect_schedule_conflicts(db, user_id, start_at, end_at)
    
    if not conflicts:
        return {
            "adjusted": False,
            "schedule_data": schedule_data,
            "message": "충돌 없음"
        }
    
    # 대체 시간 찾기
    alternatives = suggest_alternative_times(
        db, user_id, start_at.date(), duration
    )
    
    if not alternatives:
        return {
            "adjusted": False,
            "has_conflict": True,
            "conflicts": conflicts,
            "schedule_data": schedule_data,
            "message": f"'{conflicts[0]['title']}'과(와) 시간이 겹쳐요. 대체 가능한 시간이 없습니다."
        }
    
    # 가장 적합한 대체 시간 선택 (추천된 것 우선)
    best_slot = next((s for s in alternatives if s.get('recommended')), alternatives[0])
    
    # 새 시간으로 조정
    new_start_time = datetime.strptime(best_slot['start'], "%H:%M").time()
    new_start = datetime.combine(start_at.date(), new_start_time)
    new_end = new_start + timedelta(minutes=duration)
    
    adjusted_data = {
        **schedule_data,
        "start_at": new_start.isoformat(),
        "end_at": new_end.isoformat(),
    }
    
    return {
        "adjusted": True,
        "has_conflict": True,
        "original_time": f"{start_at.strftime('%H:%M')}~{end_at.strftime('%H:%M')}",
        "new_time": f"{new_start.strftime('%H:%M')}~{new_end.strftime('%H:%M')}",
        "conflicts": conflicts,
        "alternatives": alternatives,
        "schedule_data": adjusted_data,
        "message": f"'{conflicts[0]['title']}'과(와) 시간이 겹쳐서 {best_slot['start']}~로 조정했어요."
    }


# ============================================================
# 스마트 시간 추천 (사용자 패턴 기반)
# ============================================================

def analyze_user_schedule_patterns(
    db: Session,
    user_id: str,
    days: int = 30
) -> Dict[str, Any]:
    """
    사용자의 일정 패턴 분석
    - 주로 어떤 시간대에 일정을 잡는지
    - 카테고리별 선호 시간대
    - 평균 일정 길이
    """
    start_date = datetime.now() - timedelta(days=days)
    
    schedules = db.query(Schedule).filter(
        and_(
            Schedule.user_id == user_id,
            Schedule.start_at >= start_date
        )
    ).all()
    
    if not schedules:
        return {"has_data": False, "message": "분석할 데이터가 부족합니다."}
    
    # 시간대별 빈도
    hour_frequency = {}
    category_hours = {}
    durations = []
    
    for s in schedules:
        if s.start_at:
            hour = s.start_at.hour
            hour_frequency[hour] = hour_frequency.get(hour, 0) + 1
            
            cat = s.category or 'other'
            if cat not in category_hours:
                category_hours[cat] = {}
            category_hours[cat][hour] = category_hours[cat].get(hour, 0) + 1
        
        if s.start_at and s.end_at:
            duration = (s.end_at - s.start_at).total_seconds() / 60
            durations.append(duration)
    
    # 가장 활발한 시간대 (상위 3개)
    peak_hours = sorted(hour_frequency.items(), key=lambda x: x[1], reverse=True)[:3]
    
    # 카테고리별 선호 시간
    category_preferences = {}
    for cat, hours in category_hours.items():
        if hours:
            best_hour = max(hours.items(), key=lambda x: x[1])[0]
            category_preferences[cat] = best_hour
    
    return {
        "has_data": True,
        "total_schedules": len(schedules),
        "peak_hours": [{"hour": h, "count": c} for h, c in peak_hours],
        "category_preferences": category_preferences,
        "average_duration_minutes": sum(durations) / len(durations) if durations else 60,
        "most_busy_day": None,  # 추후 구현
    }


def smart_time_suggestion(
    db: Session,
    user_id: str,
    category: str,
    target_date: date,
    duration_minutes: int = 60
) -> Dict[str, Any]:
    """
    사용자 패턴 기반 스마트 시간 추천
    """
    patterns = analyze_user_schedule_patterns(db, user_id)
    
    # 카테고리별 선호 시간이 있으면 사용
    preferred_hour = None
    if patterns.get('has_data'):
        preferred_hour = patterns.get('category_preferences', {}).get(category)
    
    if preferred_hour is None:
        # 기본 시간대 (카테고리별)
        default_hours = {
            'class': 9,
            'exam': 10,
            'assignment': 14,
            'team': 15,
            'activity': 18,
            'contest': 14,
            'other': 14,
        }
        preferred_hour = default_hours.get(category, 14)
    
    # 해당 시간에 충돌이 있는지 확인
    target_start = datetime.combine(target_date, time(preferred_hour, 0))
    target_end = target_start + timedelta(minutes=duration_minutes)
    
    conflicts = detect_schedule_conflicts(db, user_id, target_start, target_end)
    
    if conflicts:
        # 대체 시간 찾기
        alternatives = suggest_alternative_times(db, user_id, target_date, duration_minutes)
        if alternatives:
            best = alternatives[0]
            return {
                "suggested_time": best['start'],
                "suggested_end": datetime.strptime(best['start'], "%H:%M").replace(
                    year=target_date.year, month=target_date.month, day=target_date.day
                ) + timedelta(minutes=duration_minutes),
                "reason": f"선호 시간({preferred_hour}시)에 다른 일정이 있어서 {best['start']}를 추천해요.",
                "alternatives": alternatives[:3]
            }
    
    return {
        "suggested_time": f"{preferred_hour:02d}:00",
        "suggested_end": target_end,
        "reason": f"평소 이 시간대에 {category} 관련 일정을 자주 잡으시네요!",
        "alternatives": []
    }


# ============================================================
# 일정 요약 및 브리핑
# ============================================================

def generate_daily_briefing(
    db: Session,
    user_id: str,
    target_date: date = None
) -> Dict[str, Any]:
    """
    하루 일정 브리핑 생성
    """
    if target_date is None:
        target_date = date.today()
    
    day_start = datetime.combine(target_date, time(0, 0))
    day_end = datetime.combine(target_date, time(23, 59, 59))
    
    # 일정 조회
    schedules = db.query(Schedule).filter(
        and_(
            Schedule.user_id == user_id,
            Schedule.start_at >= day_start,
            Schedule.end_at <= day_end
        )
    ).order_by(Schedule.start_at.asc()).all()
    
    # 할 일 조회
    tasks = db.query(SubTask).filter(
        and_(
            SubTask.user_id == user_id,
            SubTask.date == target_date
        )
    ).all()
    
    # 강의 조회
    day_of_week = str(target_date.weekday())
    lectures = db.query(Lecture).filter(
        and_(
            Lecture.user_id == user_id,
            Lecture.week == day_of_week,
            Lecture.start_day <= target_date,
            Lecture.end_day >= target_date
        )
    ).order_by(Lecture.start_time.asc()).all()
    
    # 통계
    total_events = len(schedules) + len(lectures)
    pending_tasks = len([t for t in tasks if not t.is_done])
    completed_tasks = len([t for t in tasks if t.is_done])
    high_priority = [s for s in schedules if s.priority_score and s.priority_score >= 7]
    
    # AI로 브리핑 메시지 생성
    try:
        model = get_gemini_model(temperature=0.8)
        
        schedule_list = [
            f"- {s.start_at.strftime('%H:%M')} {s.title} ({s.category})"
            for s in schedules
        ]
        lecture_list = [
            f"- {l.start_time.strftime('%H:%M')} {l.title}"
            for l in lectures
        ]
        task_list = [
            f"- {'✅' if t.is_done else '⬜'} {t.title} ({t.priority})"
            for t in tasks
        ]
        
        prompt = f"""당신은 친근한 일정 관리 AI입니다.
{target_date.strftime('%Y년 %m월 %d일')} 일정을 요약해주세요.

[강의]
{chr(10).join(lecture_list) if lecture_list else '없음'}

[일정]
{chr(10).join(schedule_list) if schedule_list else '없음'}

[할 일]
{chr(10).join(task_list) if task_list else '없음'}

[요구사항]
1. 2-3문장으로 하루를 요약
2. 중요한 일정 강조
3. 응원 메시지 포함
4. 이모지 사용

JSON 형식으로 응답:
{{"briefing": "메시지", "tip": "오늘의 팁"}}
"""
        
        response = model.generate_content(prompt)
        ai_result = json.loads(response.text)
        briefing_message = ai_result.get('briefing', '')
        tip = ai_result.get('tip', '')
    except Exception as e:
        logger.error(f"AI briefing 생성 실패: {e}")
        briefing_message = f"오늘 일정 {total_events}개, 할 일 {pending_tasks}개가 있어요!"
        tip = "화이팅! 💪"
    
    return {
        "date": target_date.isoformat(),
        "summary": {
            "total_events": total_events,
            "lectures": len(lectures),
            "schedules": len(schedules),
            "pending_tasks": pending_tasks,
            "completed_tasks": completed_tasks,
            "high_priority_count": len(high_priority),
        },
        "briefing": briefing_message,
        "tip": tip,
        "schedules": [
            {
                "time": s.start_at.strftime("%H:%M") if s.start_at else "",
                "title": s.title,
                "category": s.category,
                "priority": s.priority_score,
            }
            for s in schedules
        ],
        "lectures": [
            {
                "time": l.start_time.strftime("%H:%M"),
                "title": l.title,
            }
            for l in lectures
        ],
        "tasks": [
            {
                "title": t.title,
                "is_done": t.is_done,
                "priority": t.priority,
            }
            for t in tasks
        ],
    }


def generate_weekly_summary(
    db: Session,
    user_id: str,
    start_date: date = None
) -> Dict[str, Any]:
    """
    주간 일정 요약 생성
    """
    if start_date is None:
        today = date.today()
        start_date = today - timedelta(days=today.weekday())  # 이번 주 월요일
    
    end_date = start_date + timedelta(days=6)
    
    week_start = datetime.combine(start_date, time(0, 0))
    week_end = datetime.combine(end_date, time(23, 59, 59))
    
    # 일정 조회
    schedules = db.query(Schedule).filter(
        and_(
            Schedule.user_id == user_id,
            Schedule.start_at >= week_start,
            Schedule.end_at <= week_end
        )
    ).all()
    
    # 할 일 조회
    tasks = db.query(SubTask).filter(
        and_(
            SubTask.user_id == user_id,
            SubTask.date >= start_date,
            SubTask.date <= end_date
        )
    ).all()
    
    # 일별 통계
    daily_stats = {}
    for i in range(7):
        day = start_date + timedelta(days=i)
        day_schedules = [s for s in schedules if s.start_at and s.start_at.date() == day]
        day_tasks = [t for t in tasks if t.date == day]
        
        daily_stats[day.strftime("%a")] = {
            "date": day.isoformat(),
            "schedules": len(day_schedules),
            "tasks": len(day_tasks),
            "completed_tasks": len([t for t in day_tasks if t.is_done]),
        }
    
    # 카테고리별 통계
    category_stats = {}
    for s in schedules:
        cat = s.category or 'other'
        category_stats[cat] = category_stats.get(cat, 0) + 1
    
    # 가장 바쁜 날
    busiest_day = max(daily_stats.items(), key=lambda x: x[1]['schedules'] + x[1]['tasks'])
    
    return {
        "period": f"{start_date.isoformat()} ~ {end_date.isoformat()}",
        "total_schedules": len(schedules),
        "total_tasks": len(tasks),
        "completed_tasks": len([t for t in tasks if t.is_done]),
        "completion_rate": round(len([t for t in tasks if t.is_done]) / len(tasks) * 100, 1) if tasks else 0,
        "daily_stats": daily_stats,
        "category_stats": category_stats,
        "busiest_day": {
            "day": busiest_day[0],
            "date": busiest_day[1]['date'],
            "count": busiest_day[1]['schedules'] + busiest_day[1]['tasks'],
        },
    }


# ============================================================
# 우선순위 자동 조정
# ============================================================

def auto_adjust_priorities(
    db: Session,
    user_id: str
) -> List[Dict[str, Any]]:
    """
    마감일 기반 우선순위 자동 조정
    - D-1: priority 10
    - D-2~3: priority 8-9
    - D-4~7: priority 6-7
    - D-8+: priority 5 이하
    """
    now = datetime.now()
    
    # 미완료 일정만 조회
    schedules = db.query(Schedule).filter(
        and_(
            Schedule.user_id == user_id,
            Schedule.end_at >= now,
            Schedule.type == 'task'  # 할 일 타입만
        )
    ).all()
    
    adjustments = []
    
    for s in schedules:
        if not s.end_at:
            continue
        
        days_until = (s.end_at.date() - now.date()).days
        
        # 새 우선순위 계산
        if days_until <= 0:
            new_priority = 10  # 오늘 또는 지남
        elif days_until == 1:
            new_priority = 9
        elif days_until <= 3:
            new_priority = 8
        elif days_until <= 7:
            new_priority = 7
        elif days_until <= 14:
            new_priority = 6
        else:
            new_priority = 5
        
        # 카테고리 가산점
        if s.category in ['exam', 'assignment']:
            new_priority = min(10, new_priority + 1)
        
        # 변경이 필요한 경우만 기록
        if s.priority_score != new_priority:
            old_priority = s.priority_score
            s.priority_score = new_priority
            
            adjustments.append({
                "schedule_id": s.schedule_id,
                "title": s.title,
                "old_priority": old_priority,
                "new_priority": new_priority,
                "days_until_deadline": days_until,
            })
    
    if adjustments:
        db.commit()
    
    return adjustments


# ============================================================
# 다중 일정 일괄 처리
# ============================================================

def batch_create_schedules(
    db: Session,
    user_id: str,
    schedules_data: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    여러 일정을 한번에 생성 (충돌 검사 포함)
    """
    results = {
        "success": [],
        "conflicts": [],
        "errors": [],
    }
    
    for i, schedule_data in enumerate(schedules_data):
        try:
            start_at = datetime.fromisoformat(schedule_data.get('start_at', '').replace('Z', '+00:00'))
            end_at = datetime.fromisoformat(schedule_data.get('end_at', '').replace('Z', '+00:00'))
            
            # 충돌 검사
            conflicts = detect_schedule_conflicts(db, user_id, start_at, end_at)
            
            if conflicts:
                # 자동 조정 시도
                adjusted = auto_adjust_schedule(db, user_id, schedule_data)
                if adjusted.get('adjusted'):
                    results['success'].append({
                        "index": i,
                        "title": schedule_data.get('title'),
                        "adjusted": True,
                        "message": adjusted['message'],
                        "data": adjusted['schedule_data'],
                    })
                else:
                    results['conflicts'].append({
                        "index": i,
                        "title": schedule_data.get('title'),
                        "conflicts": conflicts,
                        "data": schedule_data,
                    })
            else:
                results['success'].append({
                    "index": i,
                    "title": schedule_data.get('title'),
                    "adjusted": False,
                    "data": schedule_data,
                })
                
        except Exception as e:
            results['errors'].append({
                "index": i,
                "title": schedule_data.get('title', 'Unknown'),
                "error": str(e),
            })
    
    return results


# ============================================================
# 컨텍스트 기반 스마트 응답
# ============================================================

def get_contextual_suggestions(
    db: Session,
    user_id: str,
    current_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    현재 상황에 맞는 스마트 제안 생성
    """
    now = datetime.now()
    today = now.date()
    
    suggestions = []
    
    # 1. 오늘 일정이 없으면 일정 추가 제안
    today_start = datetime.combine(today, time(0, 0))
    today_end = datetime.combine(today, time(23, 59, 59))
    today_schedules = db.query(Schedule).filter(
        and_(
            Schedule.user_id == user_id,
            Schedule.start_at >= today_start,
            Schedule.end_at <= today_end
        )
    ).count()
    
    if today_schedules == 0:
        suggestions.append({
            "type": "add_schedule",
            "message": "오늘 등록된 일정이 없어요. 오늘 계획을 세워볼까요?",
            "action": "오늘 일정 추가하기"
        })
    
    # 2. 마감 임박 일정 알림
    urgent = db.query(Schedule).filter(
        and_(
            Schedule.user_id == user_id,
            Schedule.end_at >= now,
            Schedule.end_at <= now + timedelta(days=2),
            Schedule.type == 'task'
        )
    ).all()
    
    if urgent:
        suggestions.append({
            "type": "urgent_deadline",
            "message": f"마감이 임박한 일정이 {len(urgent)}개 있어요!",
            "items": [{"title": u.title, "deadline": u.end_at.isoformat()} for u in urgent],
            "action": "마감 임박 일정 보기"
        })
    
    # 3. 미완료 할 일 알림
    pending_tasks = db.query(SubTask).filter(
        and_(
            SubTask.user_id == user_id,
            SubTask.date <= today,
            SubTask.is_done == False
        )
    ).count()
    
    if pending_tasks > 0:
        suggestions.append({
            "type": "pending_tasks",
            "message": f"완료하지 않은 할 일이 {pending_tasks}개 있어요.",
            "action": "할 일 확인하기"
        })
    
    # 4. 현재 시간에 따른 제안
    hour = now.hour
    if 6 <= hour < 9:
        suggestions.append({
            "type": "morning_briefing",
            "message": "좋은 아침이에요! ☀️ 오늘 일정을 확인해볼까요?",
            "action": "오늘 브리핑 보기"
        })
    elif 21 <= hour < 24:
        suggestions.append({
            "type": "daily_review",
            "message": "오늘 하루 수고했어요! 🌙 내일 일정을 미리 확인해볼까요?",
            "action": "내일 일정 보기"
        })
    
    return {
        "timestamp": now.isoformat(),
        "suggestions": suggestions,
        "has_suggestions": len(suggestions) > 0,
    }
