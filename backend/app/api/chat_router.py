"""
AI 챗봇 라우터 - 확장 버전 v2
지원 기능:
- 일정 CRUD (생성/조회/수정/삭제)
- 할 일 추천 및 세분화
- 자동 추가 모드
- 빈 시간대 채우기
- 학습 패턴 분석
- 반복 일정 설정
- 알림 예약
- 🆕 일정 충돌 감지 및 자동 조정
- 🆕 스마트 시간 추천
- 🆕 일정 요약/브리핑
- 🆕 다중 일정 일괄 처리
- 🆕 컨텍스트 기반 스마트 제안
"""

import os
import json
import re
import logging
from datetime import datetime, timedelta, date
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_
from dotenv import load_dotenv

# Google Gemini SDK
import google.generativeai as genai

from app.schemas.ai_chat import (
    ChatRequest, 
    APIResponse, 
    ChatResponseData, 
    AIChatParsed,
    Action,
    MissingField
)
from app.db.database import get_db
from app.models.schedule import Schedule
from app.models.sub_task import SubTask
from app.core.auth import get_current_user_optional, TokenPayload
from app.services.subtask_recommend_service import (
    recommend_subtasks_for_schedule,
    breakdown_schedule_to_subtasks,
    get_gap_times,
    recommend_tasks_for_gap_time,
    analyze_learning_pattern,
    create_recurring_schedules
)
from app.services.smart_schedule_service import (
    detect_schedule_conflicts,
    suggest_alternative_times,
    auto_adjust_schedule,
    analyze_user_schedule_patterns,
    smart_time_suggestion,
    generate_daily_briefing,
    generate_weekly_summary,
    auto_adjust_priorities,
    batch_create_schedules,
    get_contextual_suggestions
)

load_dotenv()

router = APIRouter()
logger = logging.getLogger(__name__)

# ============================================================
# 설정 및 상수
# ============================================================

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# 채팅은 속도와 논리력이 중요하므로 Flash 모델 권장
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")

if not GOOGLE_API_KEY:
    logger.error("GOOGLE_API_KEY is missing. Chat features will fail.")

# Gemini 설정
genai.configure(api_key=GOOGLE_API_KEY)

# 전역 사용자 ID (요청마다 설정됨)
# 로그인하지 않으면 None
TEST_USER_ID: Optional[str] = None

# 카테고리 영어→한국어 매핑
CATEGORY_MAP = {
    "class": "수업", "assignment": "과제", "exam": "시험",
    "contest": "공모전", "activity": "대외활동", "team": "팀 프로젝트",
    "personal": "개인", "other": "기타",
}

# ============================================================
# 유틸리티 함수
# ============================================================

def get_gemini_model():
    """Gemini 모델 인스턴스 반환 (JSON 모드 활성화)"""
    return genai.GenerativeModel(
        model_name=GEMINI_MODEL_NAME,
        generation_config={
            "temperature": 0.0,  # 사실 기반 응답을 위해 0으로 설정
            "response_mime_type": "application/json"  # ★ 핵심: 무조건 JSON만 뱉도록 강제
        }
    )

def translate_category(category: str) -> str:
    """영어 카테고리를 한국어로 변환"""
    return CATEGORY_MAP.get(category.lower(), category) if category else "기타"

# ============================================================
# DB 조회 함수
# ============================================================

def get_schedules_for_period(db: Session, start_date: datetime, end_date: datetime) -> list:
    """지정된 기간의 일정 조회"""
    return db.query(Schedule).filter(
        and_(
            Schedule.user_id == TEST_USER_ID,
            Schedule.end_at >= start_date,
            Schedule.end_at <= end_date
        )
    ).order_by(Schedule.end_at.asc()).all()

def search_schedules_by_keyword(db: Session, keyword: str, limit: int = 5) -> list:
    """키워드가 포함된 일정 검색"""
    now = datetime.now()
    return db.query(Schedule).filter(
        and_(
            Schedule.user_id == TEST_USER_ID,
            Schedule.title.ilike(f"%{keyword}%"),
            Schedule.start_at >= now - timedelta(days=30),
            Schedule.start_at <= now + timedelta(days=60)
        )
    ).order_by(Schedule.start_at.asc()).limit(limit).all()

def format_schedules_for_display(schedules: list) -> str:
    """일정 목록을 읽기 좋은 형식으로 변환"""
    if not schedules:
        return "등록된 일정이 없어요."
    
    lines = []
    for s in schedules:
        date_str = s.end_at.strftime("%m/%d(%a)") if s.end_at else ""
        time_str = s.end_at.strftime("%H:%M") if s.end_at else ""
        category = translate_category(s.category)
        lines.append(f"• [{category}] {s.title} - {date_str} {time_str}")
    return "\n".join(lines)

# ============================================================
# 프롬프트 생성
# ============================================================

def build_context_section(req: ChatRequest) -> str:
    """이전 대화 컨텍스트 섹션 생성"""
    if not req.user_context:
        return "\n[Previous Conversation History]\nNone (New conversation start)"
    
    context_dump = json.dumps(req.user_context, ensure_ascii=False)
    is_notification_clarify = (
        req.user_context.get('previous_intent') == 'CLARIFY' 
        and req.user_context.get('minutes_before')
    )
    
    section = f"""
[Previous Conversation History]
The user is continuing a conversation. The previous state was:
{context_dump}

INSTRUCTION: 
1. Merge the 'User Input' with the info in [Previous Conversation History].
2. If the user answers a missing field (e.g., subject name), combine it with the previous time/date to create a 'SCHEDULE_MUTATION'.
3. **IMPORTANT**: If 'minutes_before' exists in context and user provides a schedule/event name, this is a NOTIFICATION setup request. Create action with target: 'NOTIFICATION'.
"""
    
    if is_notification_clarify:
        minutes = req.user_context.get('minutes_before')
        section += f"""
4. **NOTIFICATION MODE**: The user previously asked to set an alarm {minutes} minutes before.
   - DO NOT create a new schedule. Create a NOTIFICATION action instead.
   - Use: {{"op": "UPDATE", "target": "NOTIFICATION", "payload": {{"schedule_title": "<user's answer>", "minutes_before": {minutes}}}}}
"""
    return section


def build_system_prompt(req: ChatRequest, current_date_str: str) -> str:
    """시스템 프롬프트 생성 - 확장된 인텐트 지원 v2"""
    context_section = build_context_section(req)
    
    return f"""You are a smart academic scheduler AI for Korean university students.
Your ONLY task is to analyze the input and output valid JSON.
DO NOT provide any explanations, intro text, or markdown formatting. Just the JSON.

[Current Environment]
- Today: {current_date_str}
- Timezone: {req.timezone}
- Selected Schedule ID: {req.selected_schedule_id or "None"}
- Auto Mode: {req.user_context.get('auto_mode', False) if req.user_context else False}

{context_section}

[Rules]
1. Intent Classification (EXTENDED v2):
   - "SCHEDULE_MUTATION": Create, Update, or Delete a schedule/task.
   - "SCHEDULE_QUERY": VIEW/SHOW schedules (e.g., "보여줘", "뭐야").
   - "PRIORITY_QUERY": High priority or recommendation requests.
   - "CLARIFY": If essential info (like Date) is missing.
   - "SUBTASK_RECOMMEND": User asks for task recommendations for a schedule (e.g., "할 일 추천해줘", "준비할 거 뭐야")
   - "SCHEDULE_BREAKDOWN": User wants to break down a schedule into subtasks (e.g., "세분화해줘", "쪼개줘", "나눠줘")
   - "GAP_FILL": User wants to fill empty time slots (e.g., "빈 시간 채워줘", "공강에 뭐할까")
   - "PATTERN_ANALYSIS": User asks for learning pattern analysis (e.g., "분석해줘", "패턴 알려줘", "통계 보여줘")
   - "RECURRING_SCHEDULE": User wants to create recurring schedules (e.g., "매주", "매일", "반복")
   - "AUTO_MODE_TOGGLE": User wants to toggle auto-add mode (e.g., "자동으로 추가해", "물어보지 마")
   - "SCHEDULE_UPDATE": User wants to modify existing schedule with natural language (e.g., "3시를 5시로 바꿔줘", "시간 변경")
   - "DAILY_BRIEFING": User wants daily briefing/summary (e.g., "오늘 일정 요약해줘", "오늘 브리핑", "하루 정리")
   - "WEEKLY_SUMMARY": User wants weekly summary (e.g., "이번 주 요약", "주간 정리", "한 주 리뷰")
   - "CONFLICT_CHECK": User wants to check schedule conflicts (e.g., "겹치는 일정 있어?", "충돌 확인")
   - "SMART_SUGGEST": User wants smart time/task suggestions (e.g., "언제 하면 좋을까?", "시간 추천해줘")
   - "BATCH_CREATE": User wants to create multiple schedules at once (e.g., multiple items listed)
   - "PRIORITY_ADJUST": User wants to auto-adjust priorities (e.g., "우선순위 조정해줘", "우선순위 자동 정리")

2. Type Classification:
   - "EVENT": Has START TIME. Use 'start_at'.
   - "TASK": Has DEADLINE. Use 'end_at'.

3. Payload Construction:
   - "importance_score" (1-10)
   - "category": [수업, 과제, 시험, 공모전, 대외활동, 기타]

4. For SUBTASK_RECOMMEND intent:
   - Extract the target schedule title or ID from user's message
   - Set preserved_info with "target_schedule" and "category"

5. For SCHEDULE_BREAKDOWN intent:
   - Must have a specific schedule to break down
   - Ask for clarification if schedule is not specified

6. For RECURRING_SCHEDULE intent:
   - Extract recurrence pattern (weekly, daily, monthly)
   - Extract days if weekly (mon, tue, wed, etc.)
   - Set preserved_info with recurrence details

7. For SCHEDULE_UPDATE intent:
   - Extract original time/date and new time/date
   - Set op: "UPDATE" in action

8. For AUTO_MODE_TOGGLE intent:
   - Set preserved_info.auto_mode = true/false

9. For DAILY_BRIEFING / WEEKLY_SUMMARY intent:
   - Extract target date/period if mentioned
   - Set preserved_info.target_date or preserved_info.period

10. For CONFLICT_CHECK intent:
    - Extract schedule info if checking specific schedule
    - Set preserved_info.check_date for date-specific checks

11. For SMART_SUGGEST intent:
    - Extract category and duration if mentioned
    - Set preserved_info.category, preserved_info.duration_minutes

12. For BATCH_CREATE intent:
    - Parse all schedules mentioned
    - Create multiple actions array

13. For PRIORITY_ADJUST intent:
    - No additional info needed, will auto-adjust all

[Output Format (JSON)]
{{
    "intent": "INTENT_NAME",
    "type": "EVENT" | "TASK",
    "actions": [
        {{
            "op": "CREATE" | "UPDATE" | "DELETE",
            "target": "SCHEDULE" | "SUB_TASK" | "NOTIFICATION",
            "payload": {{ ... }}
        }}
    ],
    "preserved_info": {{
        "query_range": "today" | "tomorrow" | "this_week" | "YYYY-MM-DD",
        "target_schedule": "schedule title or id",
        "recurrence": {{
            "type": "weekly" | "daily" | "monthly",
            "days": ["mon", "wed", "fri"],
            "count": 10
        }},
        "auto_mode": true | false,
        "original_time": "15:00",
        "new_time": "17:00",
        "target_date": "today" | "tomorrow" | "YYYY-MM-DD",
        "period": "week" | "month",
        "category": "과제",
        "duration_minutes": 60,
        "check_all_conflicts": true | false
    }},
    "missingFields": [
        {{ "field": "field_name", "question": "질문" }}
    ]
}}

[Examples]
# Example 1: Task Recommendation
User: "중간고사 준비 할 일 추천해줘"
JSON: {{ "intent": "SUBTASK_RECOMMEND", "type": "TASK", "actions": [], "preserved_info": {{ "target_schedule": "중간고사", "category": "시험" }} }}

# Example 2: Schedule Breakdown
User: "해커톤 발표 준비 쪼개줘"
JSON: {{ "intent": "SCHEDULE_BREAKDOWN", "type": "TASK", "actions": [], "preserved_info": {{ "target_schedule": "해커톤 발표" }} }}

# Example 3: Gap Fill
User: "내일 빈 시간에 할 일 채워줘"
JSON: {{ "intent": "GAP_FILL", "type": "TASK", "actions": [], "preserved_info": {{ "target_date": "tomorrow" }} }}

# Example 4: Pattern Analysis
User: "이번 주 학습 패턴 분석해줘"
JSON: {{ "intent": "PATTERN_ANALYSIS", "type": "TASK", "actions": [], "preserved_info": {{ "period": "week" }} }}

# Example 5: Recurring Schedule
User: "매주 월요일 10시에 스터디 넣어줘"
JSON: {{ "intent": "RECURRING_SCHEDULE", "type": "EVENT", "actions": [{{ "op": "CREATE", "target": "SCHEDULE", "payload": {{ "title": "스터디", "start_at": "2026-01-19T10:00:00+09:00", "end_at": "2026-01-19T11:00:00+09:00", "category": "기타" }} }}], "preserved_info": {{ "recurrence": {{ "type": "weekly", "days": ["mon"], "count": 10 }} }} }}

# Example 6: Auto Mode Toggle
User: "앞으로 일정은 물어보지 말고 바로 추가해"
JSON: {{ "intent": "AUTO_MODE_TOGGLE", "type": "EVENT", "actions": [], "preserved_info": {{ "auto_mode": true }} }}

# Example 7: Schedule Update
User: "내일 회의를 3시에서 5시로 바꿔줘"
JSON: {{ "intent": "SCHEDULE_UPDATE", "type": "EVENT", "actions": [{{ "op": "UPDATE", "target": "SCHEDULE", "payload": {{ "title": "회의", "original_time": "15:00", "new_time": "17:00" }} }}], "preserved_info": {{ "target_date": "tomorrow" }} }}

# Example 8: Creation (기존)
User: "내일 3시에 회의"
JSON: {{ "intent": "SCHEDULE_MUTATION", "type": "EVENT", "actions": [ {{ "op": "CREATE", "target": "SCHEDULE", "payload": {{ "title": "회의", "start_at": "2026-01-16T15:00:00+09:00", "end_at": "2026-01-16T16:00:00+09:00", "category": "기타"}} }} ] }}

# Example 9: Daily Briefing
User: "오늘 일정 요약해줘"
JSON: {{ "intent": "DAILY_BRIEFING", "type": "TASK", "actions": [], "preserved_info": {{ "target_date": "today" }} }}

# Example 10: Weekly Summary
User: "이번 주 어땠어?"
JSON: {{ "intent": "WEEKLY_SUMMARY", "type": "TASK", "actions": [], "preserved_info": {{ "period": "week" }} }}

# Example 11: Conflict Check
User: "겹치는 일정 있어?"
JSON: {{ "intent": "CONFLICT_CHECK", "type": "EVENT", "actions": [], "preserved_info": {{ "check_all_conflicts": true }} }}

# Example 12: Smart Suggest
User: "과제 언제 하면 좋을까?"
JSON: {{ "intent": "SMART_SUGGEST", "type": "TASK", "actions": [], "preserved_info": {{ "category": "과제", "duration_minutes": 60, "target_date": "today" }} }}

# Example 13: Priority Adjust
User: "우선순위 자동으로 조정해줘"
JSON: {{ "intent": "PRIORITY_ADJUST", "type": "TASK", "actions": [], "preserved_info": {{}} }}

# Example 14: Batch Create
User: "내일 10시 회의, 2시 발표, 5시 스터디 추가해줘"
JSON: {{ "intent": "BATCH_CREATE", "type": "EVENT", "actions": [{{ "op": "CREATE", "target": "SCHEDULE", "payload": {{ "title": "회의", "start_at": "2026-01-16T10:00:00+09:00", "end_at": "2026-01-16T11:00:00+09:00", "category": "기타"}} }}, {{ "op": "CREATE", "target": "SCHEDULE", "payload": {{ "title": "발표", "start_at": "2026-01-16T14:00:00+09:00", "end_at": "2026-01-16T15:00:00+09:00", "category": "기타"}} }}, {{ "op": "CREATE", "target": "SCHEDULE", "payload": {{ "title": "스터디", "start_at": "2026-01-16T17:00:00+09:00", "end_at": "2026-01-16T18:00:00+09:00", "category": "기타"}} }}], "preserved_info": {{}} }}

User Input: {req.text}
"""

# ============================================================
# Intent 핸들러 (기존 로직 유지)
# ============================================================

def handle_clarify(ai_result: AIChatParsed, db: Session) -> str:
    """CLARIFY intent 처리"""
    preserved = ai_result.preserved_info or {}
    search_keyword = preserved.get('search_keyword') or preserved.get('title')
    target_date = preserved.get('date') 
    
    if target_date and ai_result.missingFields:
        field_info = ai_result.missingFields[0]
        field_name = field_info.get('field', '') if isinstance(field_info, dict) else getattr(field_info, 'field', '')
        
        if field_name == 'schedule_title':
            try:
                specific_date = datetime.strptime(target_date, "%Y-%m-%d")
                start_date = specific_date.replace(hour=0, minute=0, second=0)
                end_date = specific_date.replace(hour=23, minute=59, second=59)
                schedules = get_schedules_for_period(db, start_date, end_date)
                
                if schedules:
                    choices = [f"{s.title} ({s.start_at.strftime('%H:%M') if s.start_at else ''})" for s in schedules]
                    
                    if isinstance(field_info, dict):
                        field_info['choices'] = choices
                    else:
                        field_info.choices = choices
                    
                    ai_result.preserved_info['op'] = 'DELETE'
                    
                    date_text = f"{specific_date.month}월 {specific_date.day}일"
                    choice_text = "\n".join([f"• {c}" for c in choices])
                    return f"{date_text}에 {len(schedules)}건의 일정이 있어요. 어떤 걸 취소할까요?\n\n{choice_text}"
                else:
                    date_text = f"{specific_date.month}월 {specific_date.day}일"
                    return f"{date_text}에는 일정이 없어요."
            except ValueError:
                pass
    
    if search_keyword and ai_result.missingFields:
        related = search_schedules_by_keyword(db, search_keyword)
        if related:
            choices = [s.title for s in related]
            field_info = ai_result.missingFields[0]
            if isinstance(field_info, dict):
                field_info['choices'] = choices
            else:
                field_info.choices = choices
    
    if ai_result.missingFields:
        field_info = ai_result.missingFields[0]
        question = field_info.get('question', "정보가 부족합니다.") if isinstance(field_info, dict) else getattr(field_info, 'question', "정보가 부족합니다.")
        choices = field_info.get('choices', []) if isinstance(field_info, dict) else getattr(field_info, 'choices', [])
        
        if choices:
            choice_text = "\n".join([f"• {c}" for c in choices])
            return f"{question}\n\n다음 일정을 찾았어요:\n{choice_text}"
        return question
    
    return "정보가 부족합니다. 조금 더 자세히 말씀해 주세요."

def handle_mutation(ai_result: AIChatParsed, db: Session) -> str:
    actions = ai_result.actions
    if not actions:
        return "처리할 일정이 없습니다."
    
    first_action = actions[0]
    op_type = first_action.op
    target_type = getattr(first_action, 'target', 'SCHEDULE')
    
    if target_type == "NOTIFICATION":
        return handle_notification(ai_result, db)
    
    if op_type == "DELETE":
        return handle_delete(ai_result, db)
    
    if op_type == "UPDATE":
        return "일정을 변경할까요?"
    
    # 자동 모드 확인
    user_context = ai_result.preserved_info or {}
    auto_mode = user_context.get('auto_mode', False)
    
    schedule_count = sum(1 for a in actions if getattr(a, 'target', 'SCHEDULE') == 'SCHEDULE')
    sub_task_count = sum(1 for a in actions if getattr(a, 'target', 'SCHEDULE') == 'SUB_TASK')
    
    if auto_mode:
        # 자동 모드면 바로 추가 플래그 설정
        ai_result.preserved_info = ai_result.preserved_info or {}
        ai_result.preserved_info['auto_confirm'] = True
        if schedule_count > 0 and sub_task_count > 0:
            return f"✅ 자동 추가 모드로 일정 {schedule_count}건과 할 일 {sub_task_count}건을 추가합니다!"
        elif sub_task_count > 0:
            return f"✅ 자동 추가 모드로 할 일 {sub_task_count}건을 추가합니다!"
        return f"✅ 자동 추가 모드로 일정 {schedule_count}건을 추가합니다!"
    
    if schedule_count > 0 and sub_task_count > 0:
        return f"일정 {schedule_count}건과 할 일 {sub_task_count}건을 등록할까요?"
    elif sub_task_count > 0:
        return f"할 일 {sub_task_count}건을 등록할까요?"
    return f"일정 {schedule_count}건을 등록할까요?"

def handle_delete(ai_result: AIChatParsed, db: Session) -> str:
    payload = ai_result.actions[0].payload
    title_keyword = payload.get('title', '')
    
    if not title_keyword:
        return "어떤 일정을 취소할까요?"
    
    matching = search_schedules_by_keyword(db, title_keyword, limit=10)
    exact_match = [s for s in matching if s.title.lower() == title_keyword.lower()]
    
    if len(exact_match) == 1:
        schedule = exact_match[0]
        payload['schedule_id'] = str(schedule.schedule_id)
        date_str = schedule.end_at.strftime("%m/%d") if schedule.end_at else ""
        return f"'{schedule.title}' ({date_str}) 일정을 취소할까요?"
    
    if len(matching) == 1:
        schedule = matching[0]
        payload['schedule_id'] = str(schedule.schedule_id)
        date_str = schedule.end_at.strftime("%m/%d") if schedule.end_at else ""
        return f"'{schedule.title}' ({date_str}) 일정을 취소할까요?"
    
    if len(matching) > 1:
        choices = [f"{s.title} ({s.end_at.strftime('%m/%d') if s.end_at else ''})" for s in matching]
        ai_result.intent = "CLARIFY"
        ai_result.actions = []
        ai_result.missingFields = [
            MissingField(
                field="schedule_title",
                question="어떤 일정을 취소할까요?",
                choices=choices
            )
        ]
        ai_result.preserved_info = {
            "op": "DELETE",
            "search_keyword": title_keyword,
        }
        choice_text = "\n".join([f"• {c}" for c in choices])
        return f"'{title_keyword}' 관련 일정이 여러 개 있어요. 어떤 걸 취소할까요?\n\n{choice_text}"
    
    return f"'{title_keyword}' 일정을 찾을 수 없어요."

def handle_notification(ai_result: AIChatParsed, db: Session) -> str:
    payload = ai_result.actions[0].payload
    notify_at = payload.get('notify_at')
    schedule_title = payload.get('schedule_title')
    minutes_before = payload.get('minutes_before')
    
    if schedule_title and minutes_before:
        matching = search_schedules_by_keyword(db, schedule_title, limit=1)
        if matching:
            schedule = matching[0]
            payload['schedule_id'] = str(schedule.schedule_id)
            if schedule.start_at:
                calculated_time = schedule.start_at - timedelta(minutes=minutes_before)
                payload['notify_at'] = calculated_time.isoformat()
                time_str = calculated_time.strftime("%m/%d %H:%M")
                return f"'{schedule.title}' {minutes_before}분 전({time_str})에 알림을 설정할까요?"
        return f"'{schedule_title}' 일정을 찾지 못했어요. 알림 시간을 직접 알려주세요!"
    
    if notify_at:
        try:
            notify_dt = datetime.fromisoformat(notify_at.replace('Z', '+00:00'))
            time_str = notify_dt.strftime("%m/%d %H:%M")
            return f"{time_str}에 알림을 설정할까요? 📢"
        except:
            pass
    
    return "언제 알림을 받으실 건가요?"

def handle_priority_query(ai_result: AIChatParsed, db: Session) -> str:
    now = datetime.now()
    start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = now + timedelta(days=14)
    
    schedules = get_schedules_for_period(db, start_date, end_date)
    high_priority = sorted(
        [s for s in schedules if s.priority_score and s.priority_score >= 7],
        key=lambda x: x.priority_score or 0,
        reverse=True
    )[:5]
    
    if not high_priority:
        return "현재 우선순위가 높은 일정이 없어요. 🎉"
    
    ai_result.preserved_info = {
        **(ai_result.preserved_info or {}),
        "query_type": "high_priority",
        "schedules": [
            {
                "id": str(s.schedule_id),
                "title": s.title,
                "category": translate_category(s.category),
                "end_at": s.end_at.isoformat() if s.end_at else None,
                "priority_score": s.priority_score
            }
            for s in high_priority
        ],
        "total_count": len(high_priority)
    }
    return "우선순위가 높은 일정이에요! 🔥"

def handle_schedule_query(ai_result: AIChatParsed, db: Session) -> str:
    now = datetime.now()
    preserved = ai_result.preserved_info or {}
    query_range = preserved.get("query_range", "today")
    
    range_config = {
        "today": (now.replace(hour=0, minute=0, second=0), now.replace(hour=23, minute=59, second=59), "오늘"),
        "tomorrow": ((now + timedelta(days=1)).replace(hour=0, minute=0, second=0), (now + timedelta(days=1)).replace(hour=23, minute=59, second=59), "내일"),
        "this_week": (
            (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0),
            (now - timedelta(days=now.weekday()) + timedelta(days=6, hours=23, minutes=59, seconds=59)),
            "이번 주"
        ),
    }
    
    if query_range not in range_config:
        try:
            specific_date = datetime.strptime(query_range, "%Y-%m-%d")
            start_date = specific_date.replace(hour=0, minute=0, second=0)
            end_date = specific_date.replace(hour=23, minute=59, second=59)
            period_text = f"{specific_date.month}월 {specific_date.day}일"
        except ValueError:
            start_date = now.replace(hour=0, minute=0, second=0)
            end_date = now.replace(hour=23, minute=59, second=59)
            period_text = "오늘"
    else:
        start_date, end_date, period_text = range_config[query_range]
    
    schedules = get_schedules_for_period(db, start_date, end_date)
    
    if schedules:
        schedule_text = format_schedules_for_display(schedules)
        return f"{period_text} 일정이에요! 📅\n\n{schedule_text}\n\n총 {len(schedules)}건의 일정이 있어요."
    return f"{period_text}은 등록된 일정이 없어요."


# ============================================================
# 확장 Intent 핸들러
# ============================================================

def handle_subtask_recommend(ai_result: AIChatParsed, db: Session) -> str:
    """SUBTASK_RECOMMEND 처리 - 할 일 추천"""
    preserved = ai_result.preserved_info or {}
    target_schedule = preserved.get('target_schedule', '')
    category = preserved.get('category', '')
    
    result = recommend_subtasks_for_schedule(
        db=db,
        user_id=TEST_USER_ID,
        schedule_title=target_schedule,
        category=category
    )
    
    recommendations = result.get('recommendations', [])
    
    if not recommendations:
        return f"'{target_schedule}'에 대한 할 일을 추천하기 어려워요. 좀 더 구체적으로 알려주세요!"
    
    # 액션으로 변환
    ai_result.actions = []
    for rec in recommendations:
        action = Action(
            op="CREATE",
            target="SUB_TASK",
            payload={
                "title": rec.get("title"),
                "estimated_minute": rec.get("estimated_minute", 60),
                "priority": rec.get("priority", "medium"),
                "category": rec.get("category", "기타"),
                "tip": rec.get("tip", ""),
                "date": rec.get("date"),
                "schedule_id": rec.get("schedule_id")
            }
        )
        ai_result.actions.append(action)
    
    # 응답 메시지 생성
    task_list = "\n".join([
        f"• {r['title']} ({r.get('estimated_minute', 60)}분, {r.get('priority', 'medium')})"
        for r in recommendations
    ])
    
    return f"'{target_schedule}'에 대해 다음 할 일을 추천드려요! 📋\n\n{task_list}\n\n{result.get('summary', '')}\n\n추가할까요?"


def handle_schedule_breakdown(ai_result: AIChatParsed, db: Session) -> str:
    """SCHEDULE_BREAKDOWN 처리 - 일정 세분화"""
    preserved = ai_result.preserved_info or {}
    target_schedule = preserved.get('target_schedule', '')
    
    # 일정 검색
    schedules = search_schedules_by_keyword(db, target_schedule, limit=1)
    
    if not schedules:
        return f"'{target_schedule}' 일정을 찾지 못했어요. 정확한 일정 이름을 알려주세요!"
    
    schedule = schedules[0]
    result = breakdown_schedule_to_subtasks(
        db=db,
        user_id=TEST_USER_ID,
        schedule_id=str(schedule.schedule_id)
    )
    
    subtasks = result.get('subtasks', [])
    
    if not subtasks:
        return f"'{schedule.title}' 일정을 세분화하기 어려워요."
    
    # 액션으로 변환
    ai_result.actions = []
    for task in subtasks:
        action = Action(
            op="CREATE",
            target="SUB_TASK",
            payload={
                "title": task.get("title"),
                "estimated_minute": task.get("estimated_minute", 30),
                "priority": task.get("priority", "medium"),
                "category": task.get("category", schedule.category or "기타"),
                "tip": task.get("tip", ""),
                "date": task.get("date"),
                "schedule_id": str(schedule.schedule_id)
            }
        )
        ai_result.actions.append(action)
    
    task_list = "\n".join([
        f"{i+1}. {t['title']} ({t.get('estimated_minute', 30)}분)"
        for i, t in enumerate(subtasks)
    ])
    
    total_time = result.get('total_estimated_minute', sum(t.get('estimated_minute', 30) for t in subtasks))
    
    return f"'{schedule.title}'을 다음과 같이 세분화했어요! 🎯\n\n{task_list}\n\n총 예상 소요 시간: {total_time}분\n\n추가할까요?"


def handle_gap_fill(ai_result: AIChatParsed, db: Session) -> str:
    """GAP_FILL 처리 - 빈 시간대 채우기"""
    preserved = ai_result.preserved_info or {}
    target_date_str = preserved.get('target_date', '')
    
    # 날짜 파싱
    now = datetime.now()
    if target_date_str == 'tomorrow':
        target_date = (now + timedelta(days=1)).date()
    elif target_date_str == 'today' or not target_date_str:
        target_date = now.date()
    else:
        try:
            target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        except:
            target_date = now.date()
    
    # 빈 시간대 조회
    gap_times = get_gap_times(db, TEST_USER_ID, target_date)
    
    if not gap_times:
        return f"{target_date.strftime('%m월 %d일')}은 빈 시간대가 없어요! 일정이 꽉 찼네요. 💪"
    
    # 가장 긴 빈 시간대에 할 일 추천
    longest_gap = max(gap_times, key=lambda x: x['duration_minutes'])
    
    result = recommend_tasks_for_gap_time(
        db=db,
        user_id=TEST_USER_ID,
        target_date=target_date,
        gap_time=longest_gap
    )
    
    recommendations = result.get('recommendations', [])
    
    # 액션으로 변환
    ai_result.actions = []
    for rec in recommendations:
        action = Action(
            op="CREATE",
            target="SUB_TASK",
            payload={
                "title": rec.get("title"),
                "estimated_minute": rec.get("estimated_minute", 30),
                "priority": rec.get("priority", "medium"),
                "category": rec.get("category", "기타"),
                "tip": rec.get("tip", ""),
                "date": rec.get("date")
            }
        )
        ai_result.actions.append(action)
    
    # 빈 시간대 목록
    gap_list = "\n".join([
        f"• {g['start']} ~ {g['end']} ({g['duration_minutes']}분)"
        for g in gap_times
    ])
    
    # 추천 할 일 목록
    task_list = "\n".join([
        f"• {r['title']} ({r.get('estimated_minute', 30)}분)"
        for r in recommendations
    ]) if recommendations else "추천할 할 일이 없어요."
    
    return f"📅 {target_date.strftime('%m월 %d일')} 빈 시간대:\n{gap_list}\n\n💡 {longest_gap['start']}~{longest_gap['end']} 시간대에 추천:\n{task_list}\n\n추가할까요?"


def handle_pattern_analysis(ai_result: AIChatParsed, db: Session) -> str:
    """PATTERN_ANALYSIS 처리 - 학습 패턴 분석"""
    preserved = ai_result.preserved_info or {}
    period = preserved.get('period', 'week')
    
    days = 7 if period == 'week' else 30 if period == 'month' else 7
    
    result = analyze_learning_pattern(db, TEST_USER_ID, days)
    
    stats = result.get('statistics', {})
    analysis = result.get('analysis', {})
    
    # 응답 메시지 구성
    stats_text = f"""📊 **{result.get('period', '최근')} 학습 분석**

✅ 완료율: {stats.get('completion_rate', 0)}%
📝 완료한 할 일: {stats.get('completed_count', 0)}개
⏳ 미완료 할 일: {stats.get('incomplete_count', 0)}개
📅 일정 수: {stats.get('total_schedules', 0)}개"""
    
    if stats.get('most_delayed_category'):
        stats_text += f"\n⚠️ 가장 미룬 카테고리: {stats.get('most_delayed_category')}"
    
    feedback = analysis.get('overall_feedback', '')
    strengths = analysis.get('strengths', [])
    improvements = analysis.get('improvements', [])
    motivation = analysis.get('motivation', '화이팅! 💪')
    
    strengths_text = "\n".join([f"• {s}" for s in strengths]) if strengths else ""
    improvements_text = "\n".join([
        f"• {i.get('area', '')}: {i.get('suggestion', '')}"
        for i in improvements
    ]) if improvements else ""
    
    response = f"{stats_text}\n\n"
    
    if feedback:
        response += f"💬 {feedback}\n\n"
    
    if strengths_text:
        response += f"👍 잘한 점:\n{strengths_text}\n\n"
    
    if improvements_text:
        response += f"💡 개선 제안:\n{improvements_text}\n\n"
    
    response += f"🔥 {motivation}"
    
    # preserved_info에 분석 결과 저장
    ai_result.preserved_info = {
        **(ai_result.preserved_info or {}),
        "analysis_result": result
    }
    
    return response


def handle_recurring_schedule(ai_result: AIChatParsed, db: Session) -> str:
    """RECURRING_SCHEDULE 처리 - 반복 일정"""
    preserved = ai_result.preserved_info or {}
    recurrence = preserved.get('recurrence', {})
    
    if not ai_result.actions:
        return "반복 일정 정보가 부족해요. 무슨 일정을 반복할까요?"
    
    base_action = ai_result.actions[0]
    base_schedule = base_action.payload
    
    recurrence_type = recurrence.get('type', 'weekly')
    days = recurrence.get('days', [])
    count = recurrence.get('count', 10)
    
    # 반복 일정 생성
    recurring_schedules = create_recurring_schedules(
        db=db,
        user_id=TEST_USER_ID,
        base_schedule=base_schedule,
        recurrence=recurrence
    )
    
    # 액션 업데이트
    ai_result.actions = []
    for sched in recurring_schedules:
        action = Action(
            op="CREATE",
            target="SCHEDULE",
            payload=sched
        )
        ai_result.actions.append(action)
    
    # 반복 패턴 설명
    if recurrence_type == 'weekly':
        day_names = {'mon': '월', 'tue': '화', 'wed': '수', 'thu': '목', 'fri': '금', 'sat': '토', 'sun': '일'}
        days_text = ', '.join([day_names.get(d, d) for d in days]) if days else '매주'
        pattern_text = f"매주 {days_text}요일"
    elif recurrence_type == 'daily':
        pattern_text = "매일"
    else:
        pattern_text = "매월"
    
    return f"🔄 '{base_schedule.get('title')}' 반복 일정을 생성했어요!\n\n• 패턴: {pattern_text}\n• 횟수: {len(recurring_schedules)}회\n\n추가할까요?"


def handle_auto_mode_toggle(ai_result: AIChatParsed, db: Session) -> str:
    """AUTO_MODE_TOGGLE 처리 - 자동 추가 모드"""
    preserved = ai_result.preserved_info or {}
    auto_mode = preserved.get('auto_mode', False)
    
    if auto_mode:
        return "🚀 **자동 추가 모드 ON!**\n\n앞으로 일정/할 일 추가 요청 시 확인 없이 바로 추가합니다.\n\n'자동 모드 꺼줘'라고 하면 다시 확인 모드로 돌아갑니다."
    else:
        return "⏸️ **자동 추가 모드 OFF**\n\n앞으로 일정/할 일 추가 전 확인을 받습니다."


def handle_schedule_update(ai_result: AIChatParsed, db: Session) -> str:
    """SCHEDULE_UPDATE 처리 - 자연어 일정 수정"""
    if not ai_result.actions:
        return "수정할 일정 정보가 부족해요."
    
    payload = ai_result.actions[0].payload
    title = payload.get('title', '')
    original_time = payload.get('original_time', '')
    new_time = payload.get('new_time', '')
    
    # 일정 검색
    schedules = search_schedules_by_keyword(db, title, limit=5)
    
    if not schedules:
        return f"'{title}' 일정을 찾지 못했어요."
    
    if len(schedules) > 1:
        choices = [f"{s.title} ({s.start_at.strftime('%m/%d %H:%M') if s.start_at else ''})" for s in schedules]
        ai_result.intent = "CLARIFY"
        ai_result.missingFields = [
            MissingField(
                field="schedule_id",
                question="어떤 일정을 수정할까요?",
                choices=choices
            )
        ]
        choice_text = "\n".join([f"• {c}" for c in choices])
        return f"'{title}' 관련 일정이 여러 개 있어요:\n\n{choice_text}\n\n어떤 걸 수정할까요?"
    
    schedule = schedules[0]
    payload['schedule_id'] = str(schedule.schedule_id)
    
    return f"'{schedule.title}'의 시간을 {original_time} → {new_time}로 변경할까요?"


# ============================================================
# 🆕 스마트 기능 핸들러
# ============================================================

def handle_daily_briefing(ai_result: AIChatParsed, db: Session) -> str:
    """DAILY_BRIEFING 처리 - 오늘 일정 브리핑"""
    preserved = ai_result.preserved_info or {}
    target_date_str = preserved.get('target_date', 'today')
    
    # 날짜 파싱
    now = datetime.now()
    if target_date_str == 'tomorrow':
        target_date = (now + timedelta(days=1)).date()
    elif target_date_str == 'today' or not target_date_str:
        target_date = now.date()
    else:
        try:
            target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        except:
            target_date = now.date()
    
    briefing = generate_daily_briefing(db, TEST_USER_ID, target_date)
    
    summary = briefing.get('summary', {})
    schedules = briefing.get('schedules', [])
    lectures = briefing.get('lectures', [])
    tasks = briefing.get('tasks', [])
    
    # 응답 구성
    date_text = target_date.strftime("%m월 %d일 %A")
    
    response = f"📅 **{date_text} 브리핑**\n\n"
    response += f"{briefing.get('briefing', '')}\n\n"
    
    if lectures:
        response += "📚 **강의**\n"
        for l in lectures:
            response += f"• {l['time']} {l['title']}\n"
        response += "\n"
    
    if schedules:
        response += "📌 **일정**\n"
        for s in schedules:
            priority_emoji = "🔴" if s.get('priority', 0) >= 8 else "🟡" if s.get('priority', 0) >= 5 else "🟢"
            response += f"• {s['time']} {s['title']} {priority_emoji}\n"
        response += "\n"
    
    if tasks:
        response += "✅ **할 일**\n"
        done_count = len([t for t in tasks if t.get('is_done')])
        response += f"완료: {done_count}/{len(tasks)}개\n"
        for t in tasks[:5]:  # 최대 5개만 표시
            check = "✅" if t.get('is_done') else "⬜"
            response += f"{check} {t['title']}\n"
        if len(tasks) > 5:
            response += f"... 외 {len(tasks) - 5}개\n"
        response += "\n"
    
    response += f"💡 **Tip:** {briefing.get('tip', '오늘도 화이팅!')}"
    
    # 결과 저장
    ai_result.preserved_info = {
        **(ai_result.preserved_info or {}),
        "briefing_data": briefing
    }
    
    return response


def handle_weekly_summary(ai_result: AIChatParsed, db: Session) -> str:
    """WEEKLY_SUMMARY 처리 - 주간 요약"""
    summary = generate_weekly_summary(db, TEST_USER_ID)
    
    daily = summary.get('daily_stats', {})
    categories = summary.get('category_stats', {})
    busiest = summary.get('busiest_day', {})
    
    response = f"📊 **{summary.get('period', '이번 주')} 요약**\n\n"
    
    # 통계
    response += f"📅 총 일정: {summary.get('total_schedules', 0)}개\n"
    response += f"✅ 할 일 완료율: {summary.get('completion_rate', 0)}%\n"
    response += f"({summary.get('completed_tasks', 0)}/{summary.get('total_tasks', 0)}개 완료)\n\n"
    
    # 요일별 현황
    response += "📈 **요일별 현황**\n"
    day_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    day_korean = {'Mon': '월', 'Tue': '화', 'Wed': '수', 'Thu': '목', 'Fri': '금', 'Sat': '토', 'Sun': '일'}
    
    for day_en in day_order:
        if day_en in daily:
            d = daily[day_en]
            bar = "█" * min(d['schedules'] + d['tasks'], 10)
            response += f"{day_korean.get(day_en, day_en)}: {bar or '░'} ({d['schedules']}일정, {d['tasks']}할일)\n"
    
    response += "\n"
    
    # 카테고리별
    if categories:
        response += "📁 **카테고리별 일정**\n"
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            response += f"• {translate_category(cat)}: {count}건\n"
        response += "\n"
    
    # 가장 바쁜 날
    if busiest:
        response += f"🔥 가장 바쁜 날: {busiest.get('day', '')} ({busiest.get('count', 0)}건)\n"
    
    # 결과 저장
    ai_result.preserved_info = {
        **(ai_result.preserved_info or {}),
        "weekly_summary": summary
    }
    
    return response


def handle_conflict_check(ai_result: AIChatParsed, db: Session) -> str:
    """CONFLICT_CHECK 처리 - 일정 충돌 확인"""
    preserved = ai_result.preserved_info or {}
    check_all = preserved.get('check_all_conflicts', True)
    
    now = datetime.now()
    
    # 향후 2주간 일정 조회
    schedules = db.query(Schedule).filter(
        and_(
            Schedule.user_id == TEST_USER_ID,
            Schedule.start_at >= now,
            Schedule.start_at <= now + timedelta(days=14)
        )
    ).order_by(Schedule.start_at.asc()).all()
    
    conflicts_found = []
    
    # 충돌 검사
    for i, s1 in enumerate(schedules):
        if not s1.start_at or not s1.end_at:
            continue
        for s2 in schedules[i+1:]:
            if not s2.start_at or not s2.end_at:
                continue
            # 시간이 겹치는지 확인
            if s1.start_at < s2.end_at and s2.start_at < s1.end_at:
                conflicts_found.append({
                    "schedule1": {
                        "title": s1.title,
                        "time": f"{s1.start_at.strftime('%m/%d %H:%M')}~{s1.end_at.strftime('%H:%M')}"
                    },
                    "schedule2": {
                        "title": s2.title,
                        "time": f"{s2.start_at.strftime('%m/%d %H:%M')}~{s2.end_at.strftime('%H:%M')}"
                    }
                })
    
    if not conflicts_found:
        return "✅ 충돌하는 일정이 없어요! 깔끔하게 정리되어 있네요. 🎉"
    
    response = f"⚠️ **{len(conflicts_found)}건의 일정 충돌 발견!**\n\n"
    
    for i, conflict in enumerate(conflicts_found[:5], 1):
        s1 = conflict['schedule1']
        s2 = conflict['schedule2']
        response += f"{i}. 🔴 충돌\n"
        response += f"   • {s1['title']} ({s1['time']})\n"
        response += f"   • {s2['title']} ({s2['time']})\n\n"
    
    if len(conflicts_found) > 5:
        response += f"... 외 {len(conflicts_found) - 5}건 더 있어요.\n\n"
    
    response += "충돌된 일정 중 조정이 필요하면 말씀해주세요!"
    
    # 결과 저장
    ai_result.preserved_info = {
        **(ai_result.preserved_info or {}),
        "conflicts": conflicts_found
    }
    
    return response


def handle_smart_suggest(ai_result: AIChatParsed, db: Session) -> str:
    """SMART_SUGGEST 처리 - 스마트 시간 추천"""
    preserved = ai_result.preserved_info or {}
    category = preserved.get('category', 'other')
    duration = preserved.get('duration_minutes', 60)
    target_date_str = preserved.get('target_date', 'today')
    
    # 날짜 파싱
    now = datetime.now()
    if target_date_str == 'tomorrow':
        target_date = (now + timedelta(days=1)).date()
    elif target_date_str == 'today' or not target_date_str:
        target_date = now.date()
    else:
        try:
            target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        except:
            target_date = now.date()
    
    suggestion = smart_time_suggestion(
        db=db,
        user_id=TEST_USER_ID,
        category=category,
        target_date=target_date,
        duration_minutes=duration
    )
    
    response = f"💡 **스마트 시간 추천**\n\n"
    response += f"📅 {target_date.strftime('%m월 %d일')}\n"
    response += f"📌 카테고리: {translate_category(category)}\n"
    response += f"⏱️ 필요 시간: {duration}분\n\n"
    
    response += f"✨ **추천 시간: {suggestion.get('suggested_time', '')}**\n"
    response += f"   {suggestion.get('reason', '')}\n\n"
    
    alternatives = suggestion.get('alternatives', [])
    if alternatives:
        response += "🔄 **대체 가능한 시간**\n"
        for alt in alternatives[:3]:
            response += f"• {alt['start']}~{alt['end']} ({alt['duration_minutes']}분 여유)\n"
    
    # 결과 저장
    ai_result.preserved_info = {
        **(ai_result.preserved_info or {}),
        "suggestion": suggestion
    }
    
    return response


def handle_batch_create(ai_result: AIChatParsed, db: Session) -> str:
    """BATCH_CREATE 처리 - 다중 일정 일괄 생성"""
    if not ai_result.actions:
        return "생성할 일정이 없어요."
    
    schedules_data = [action.payload for action in ai_result.actions]
    
    # 일괄 처리 (충돌 검사 포함)
    result = batch_create_schedules(db, TEST_USER_ID, schedules_data)
    
    success = result.get('success', [])
    conflicts = result.get('conflicts', [])
    errors = result.get('errors', [])
    
    response = f"📋 **{len(schedules_data)}건 일정 일괄 처리 결과**\n\n"
    
    if success:
        response += f"✅ **성공: {len(success)}건**\n"
        for s in success:
            adjusted_mark = " (시간 조정됨)" if s.get('adjusted') else ""
            response += f"• {s.get('title', '')}{adjusted_mark}\n"
        response += "\n"
    
    if conflicts:
        response += f"⚠️ **충돌: {len(conflicts)}건**\n"
        for c in conflicts:
            conflict_titles = [cf['title'] for cf in c.get('conflicts', [])]
            response += f"• {c.get('title', '')} - '{', '.join(conflict_titles)}'과 충돌\n"
        response += "\n"
    
    if errors:
        response += f"❌ **오류: {len(errors)}건**\n"
        for e in errors:
            response += f"• {e.get('title', '')}: {e.get('error', '')}\n"
    
    # 성공한 것만 액션에 남기기
    ai_result.actions = []
    for s in success:
        ai_result.actions.append(Action(
            op="CREATE",
            target="SCHEDULE",
            payload=s.get('data', {})
        ))
    
    if success:
        response += f"\n{len(success)}건을 추가할까요?"
    
    return response


def handle_priority_adjust(ai_result: AIChatParsed, db: Session) -> str:
    """PRIORITY_ADJUST 처리 - 우선순위 자동 조정"""
    adjustments = auto_adjust_priorities(db, TEST_USER_ID)
    
    if not adjustments:
        return "✅ 모든 일정의 우선순위가 적절해요! 조정할 필요가 없습니다. 🎉"
    
    response = f"🔄 **{len(adjustments)}건의 우선순위를 조정했어요!**\n\n"
    
    # 우선순위가 올라간 것과 내려간 것 분류
    increased = [a for a in adjustments if a['new_priority'] > (a['old_priority'] or 0)]
    decreased = [a for a in adjustments if a['new_priority'] < (a['old_priority'] or 0)]
    
    if increased:
        response += "📈 **우선순위 상승**\n"
        for a in increased[:5]:
            days = a.get('days_until_deadline', 0)
            response += f"• {a['title']}: {a['old_priority'] or '없음'} → {a['new_priority']} (D-{days})\n"
        if len(increased) > 5:
            response += f"... 외 {len(increased) - 5}건\n"
        response += "\n"
    
    if decreased:
        response += "📉 **우선순위 하락**\n"
        for a in decreased[:5]:
            days = a.get('days_until_deadline', 0)
            response += f"• {a['title']}: {a['old_priority'] or '없음'} → {a['new_priority']} (D-{days})\n"
        if len(decreased) > 5:
            response += f"... 외 {len(decreased) - 5}건\n"
    
    response += "\n마감일이 가까운 일정은 우선순위가 자동으로 올라갔어요! ⏰"
    
    # 결과 저장
    ai_result.preserved_info = {
        **(ai_result.preserved_info or {}),
        "priority_adjustments": adjustments
    }
    
    return response

# ============================================================
# 메인 API 엔드포인트
# ============================================================

@router.post("/chat", response_model=APIResponse)
async def chat_with_ai(
    req: ChatRequest, 
    db: Session = Depends(get_db),
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional)
):
    global TEST_USER_ID
    
    # 로그인 확인
    if not current_user:
        return APIResponse(
            status=401, 
            message="로그인이 필요합니다. 로그인 후 다시 시도해주세요.",
            data=None
        )
    
    # 전역 user_id 설정 (핸들러에서 사용)
    TEST_USER_ID = current_user.sub
    
    try:
        model = get_gemini_model()
        now = datetime.now()
        current_date_str = req.base_date or now.strftime("%Y-%m-%d (%A)")
        
        # 1. 프롬프트 생성
        system_prompt = build_system_prompt(req, current_date_str)
        
        # 2. Gemini 호출 (JSON 모드로 인해 후처리 불필요)
        response = model.generate_content(system_prompt)
        
        # 3. 결과 파싱 (Gemini가 JSON을 보장하므로 바로 로드)
        try:
            parsed_data = json.loads(response.text)
        except json.JSONDecodeError:
            # 혹시라도 마크다운이 섞여있을 경우 대비 (안전장치)
            text = response.text
            text = re.sub(r"```json\s*", "", text)
            text = re.sub(r"```", "", text)
            parsed_data = json.loads(text)
            
        ai_result = AIChatParsed(**parsed_data)
        
        # 4. Intent 처리 (확장 v2)
        intent_handlers = {
            "CLARIFY": handle_clarify,
            "SCHEDULE_MUTATION": handle_mutation,
            "PRIORITY_QUERY": handle_priority_query,
            "SCHEDULE_QUERY": handle_schedule_query,
            "SUBTASK_RECOMMEND": handle_subtask_recommend,
            "SCHEDULE_BREAKDOWN": handle_schedule_breakdown,
            "GAP_FILL": handle_gap_fill,
            "PATTERN_ANALYSIS": handle_pattern_analysis,
            "RECURRING_SCHEDULE": handle_recurring_schedule,
            "AUTO_MODE_TOGGLE": handle_auto_mode_toggle,
            "SCHEDULE_UPDATE": handle_schedule_update,
            # 🆕 스마트 기능 핸들러
            "DAILY_BRIEFING": handle_daily_briefing,
            "WEEKLY_SUMMARY": handle_weekly_summary,
            "CONFLICT_CHECK": handle_conflict_check,
            "SMART_SUGGEST": handle_smart_suggest,
            "BATCH_CREATE": handle_batch_create,
            "PRIORITY_ADJUST": handle_priority_adjust,
        }
        
        handler = intent_handlers.get(ai_result.intent)
        assistant_msg = handler(ai_result, db) if handler else "일정을 확인했습니다."
        
        return APIResponse(
            status=200, 
            message="Success", 
            data=ChatResponseData(parsed_result=ai_result, assistant_message=assistant_msg)
        )

    except Exception as e:
        logger.error(f"Chat API Error: {str(e)}")
        return APIResponse(status=500, message=f"AI 처리 중 오류가 발생했습니다: {str(e)}")


@router.get("/ai/suggestions")
async def get_ai_suggestions(
    db: Session = Depends(get_db),
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional)
):
    """
    컨텍스트 기반 스마트 제안 API
    현재 상황에 맞는 제안을 반환합니다.
    """
    try:
        if not current_user:
            return {"status": 200, "message": "Success", "data": {"suggestions": [], "has_suggestions": False}}
        
        suggestions = get_contextual_suggestions(db, current_user.sub, {})
        return {
            "status": 200,
            "message": "Success",
            "data": suggestions
        }
    except Exception as e:
        logger.error(f"Suggestions API Error: {str(e)}")
        return {
            "status": 500,
            "message": f"제안 조회 중 오류가 발생했습니다: {str(e)}",
            "data": {"suggestions": [], "has_suggestions": False}
        }


@router.get("/ai/briefing")
async def get_daily_briefing_api(
    target_date: str = None, 
    db: Session = Depends(get_db),
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional)
):
    """
    일일 브리핑 API
    오늘 또는 특정 날짜의 일정 브리핑을 반환합니다.
    """
    try:
        if not current_user:
            return {"status": 200, "message": "Success", "data": None}
        
        if target_date:
            target = datetime.strptime(target_date, "%Y-%m-%d").date()
        else:
            target = date.today()
        
        briefing = generate_daily_briefing(db, current_user.sub, target)
        return {
            "status": 200,
            "message": "Success",
            "data": briefing
        }
    except Exception as e:
        logger.error(f"Briefing API Error: {str(e)}")
        return {
            "status": 500,
            "message": f"브리핑 조회 중 오류가 발생했습니다: {str(e)}",
            "data": None
        }


@router.get("/ai/weekly-summary")
async def get_weekly_summary_api(
    db: Session = Depends(get_db),
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional)
):
    """
    주간 요약 API
    이번 주 일정 요약을 반환합니다.
    """
    try:
        if not current_user:
            return {"status": 200, "message": "Success", "data": None}
        
        summary = generate_weekly_summary(db, current_user.sub)
        return {
            "status": 200,
            "message": "Success",
            "data": summary
        }
    except Exception as e:
        logger.error(f"Weekly Summary API Error: {str(e)}")
        return {
            "status": 500,
            "message": f"주간 요약 조회 중 오류가 발생했습니다: {str(e)}",
            "data": None
        }


@router.post("/ai/priority-adjust")
async def adjust_priorities_api(
    db: Session = Depends(get_db),
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional)
):
    """
    우선순위 자동 조정 API
    마감일 기반으로 우선순위를 자동 조정합니다.
    """
    try:
        if not current_user:
            return {"status": 401, "message": "로그인이 필요합니다.", "data": None}
        
        adjustments = auto_adjust_priorities(db, current_user.sub)
        return {
            "status": 200,
            "message": f"{len(adjustments)}건의 우선순위가 조정되었습니다.",
            "data": {
                "adjustments": adjustments,
                "count": len(adjustments)
            }
        }
    except Exception as e:
        logger.error(f"Priority Adjust API Error: {str(e)}")
        return {
            "status": 500,
            "message": f"우선순위 조정 중 오류가 발생했습니다: {str(e)}",
            "data": None
        }


@router.get("/ai/conflict-check")
async def check_conflicts_api(
    db: Session = Depends(get_db),
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional)
):
    """
    일정 충돌 확인 API
    향후 2주간 충돌하는 일정을 확인합니다.
    """
    try:
        if not current_user:
            return {"status": 200, "message": "충돌하는 일정이 없습니다.", "data": {"conflicts": [], "count": 0, "has_conflicts": False}}
        
        now = datetime.now()
        
        # 향후 2주간 일정 조회
        schedules = db.query(Schedule).filter(
            and_(
                Schedule.user_id == current_user.sub,
                Schedule.start_at >= now,
                Schedule.start_at <= now + timedelta(days=14)
            )
        ).order_by(Schedule.start_at.asc()).all()
        
        conflicts_found = []
        
        for i, s1 in enumerate(schedules):
            if not s1.start_at or not s1.end_at:
                continue
            for s2 in schedules[i+1:]:
                if not s2.start_at or not s2.end_at:
                    continue
                if s1.start_at < s2.end_at and s2.start_at < s1.end_at:
                    conflicts_found.append({
                        "schedule1": {
                            "id": str(s1.schedule_id),
                            "title": s1.title,
                            "time": f"{s1.start_at.strftime('%m/%d %H:%M')}~{s1.end_at.strftime('%H:%M')}"
                        },
                        "schedule2": {
                            "id": str(s2.schedule_id),
                            "title": s2.title,
                            "time": f"{s2.start_at.strftime('%m/%d %H:%M')}~{s2.end_at.strftime('%H:%M')}"
                        }
                    })
        
        return {
            "status": 200,
            "message": f"{len(conflicts_found)}건의 충돌이 발견되었습니다." if conflicts_found else "충돌하는 일정이 없습니다.",
            "data": {
                "conflicts": conflicts_found,
                "count": len(conflicts_found),
                "has_conflicts": len(conflicts_found) > 0
            }
        }
    except Exception as e:
        logger.error(f"Conflict Check API Error: {str(e)}")
        return {
            "status": 500,
            "message": f"충돌 확인 중 오류가 발생했습니다: {str(e)}",
            "data": None
        }