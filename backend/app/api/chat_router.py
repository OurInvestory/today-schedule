import os
import json
import re
import logging
from datetime import datetime, timedelta
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

load_dotenv()

router = APIRouter()
logger = logging.getLogger(__name__)

# ============================================================
# 설정 및 상수
# ============================================================

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# 채팅은 속도와 논리력이 중요하므로 Flash 모델 권장 (Pro도 가능)
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")

if not GOOGLE_API_KEY:
    logger.error("GOOGLE_API_KEY is missing. Chat features will fail.")

# Gemini 설정
genai.configure(api_key=GOOGLE_API_KEY)

# 테스트용 고정 사용자 ID (나중에 실제 인증으로 교체 필요)
TEST_USER_ID = "7822a162-788d-4f36-9366-c956a68393e1"

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
            Schedule.start_at <= now + timedelta(days=14)
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
    """시스템 프롬프트 생성"""
    context_section = build_context_section(req)
    
    return f"""You are a smart academic scheduler AI.
Your ONLY task is to analyze the input and output valid JSON.
DO NOT provide any explanations, intro text, or markdown formatting. Just the JSON.

[Current Environment]
- Today: {current_date_str}
- Timezone: {req.timezone}
- Selected Schedule ID: {req.selected_schedule_id or "None"} 

{context_section}

[Rules]
1. Intent Classification:
   - "SCHEDULE_MUTATION": Create, Update, or Delete a schedule/task.
   - "SCHEDULE_QUERY": VIEW/SHOW schedules (e.g., "보여줘", "뭐야").
   - "PRIORITY_QUERY": High priority or recommendation requests.
   - "CLARIFY": If essential info (like Date) is missing.

2. Type Classification:
   - "EVENT": Has START TIME. Use 'start_at'.
   - "TASK": Has DEADLINE. Use 'end_at'.

3. Payload Construction:
   - "importance_score" (1-10)
   - "category": [수업, 과제, 시험, 공모전, 대외활동, 기타]

4. Output Format (JSON):
   - "CLARIFY": Fill 'preserved_info' + 'missingFields'
   - "SCHEDULE_MUTATION": Fill 'actions' list

[Examples]
# Example 1: Creation
User: "내일 3시에 회의"
JSON: {{ "intent": "SCHEDULE_MUTATION", "type": "EVENT", "actions": [ {{ "op": "CREATE", "target": "SCHEDULE", "payload": {{ "title": "회의", "start_at": "2026-01-16T15:00:00+09:00", "end_at": "2026-01-16T16:00:00+09:00", "category": "기타"}} }} ] }}

# Example 2: Query
User: "오늘 일정 보여줘"
JSON: {{ "intent": "SCHEDULE_QUERY", "type": "TASK", "actions": [], "preserved_info": {{ "query_range": "today" }} }}

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
    
    schedule_count = sum(1 for a in actions if getattr(a, 'target', 'SCHEDULE') == 'SCHEDULE')
    sub_task_count = sum(1 for a in actions if getattr(a, 'target', 'SCHEDULE') == 'SUB_TASK')
    
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
# 메인 API 엔드포인트
# ============================================================

@router.post("/chat", response_model=APIResponse)
async def chat_with_ai(req: ChatRequest, db: Session = Depends(get_db)):
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
        
        # 4. Intent 처리 (기존 로직 동일)
        intent_handlers = {
            "CLARIFY": handle_clarify,
            "SCHEDULE_MUTATION": handle_mutation,
            "PRIORITY_QUERY": handle_priority_query,
            "SCHEDULE_QUERY": handle_schedule_query,
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