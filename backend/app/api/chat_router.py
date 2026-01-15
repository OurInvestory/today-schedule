import os
import json
import re
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_
from dotenv import load_dotenv

# IBM Watsonx SDK
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
from ibm_watsonx_ai.foundation_models.utils.enums import DecodingMethods

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

# ============================================================
# 설정 및 상수
# ============================================================

WATSONX_API_KEY = os.getenv("WATSONX_API_KEY")
WATSONX_URL = os.getenv("WATSONX_URL")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID")
WATSONX_MODEL_ID = os.getenv("WATSONX_MODEL_ID", "meta-llama/llama-3-3-70b-instruct")

TEST_USER_ID = "7822a162-788d-4f36-9366-c956a68393e1"

# 카테고리 영어→한국어 매핑
CATEGORY_MAP = {
    "class": "수업", "assignment": "과제", "exam": "시험",
    "contest": "공모전", "activity": "대외활동", "team": "팀 프로젝트",
    "personal": "개인", "other": "기타",
}

GENERATE_PARAMS = {
    GenParams.DECODING_METHOD: DecodingMethods.GREEDY,
    GenParams.MAX_NEW_TOKENS: 500,
    GenParams.MIN_NEW_TOKENS: 1,
    GenParams.TEMPERATURE: 0,
    GenParams.STOP_SEQUENCES: ["User Input:", "User:", "\n\n\n", "```\n"]
}

# ============================================================
# 유틸리티 함수
# ============================================================

def get_watson_model():
    """Watsonx 모델 인스턴스 반환"""
    return ModelInference(
        model_id=WATSONX_MODEL_ID,
        params=GENERATE_PARAMS,
        credentials={"url": WATSONX_URL, "apikey": WATSONX_API_KEY},
        project_id=WATSONX_PROJECT_ID
    )


def translate_category(category: str) -> str:
    """영어 카테고리를 한국어로 변환"""
    return CATEGORY_MAP.get(category.lower(), category) if category else "기타"


def extract_json_from_text(text: str) -> str:
    """텍스트에서 첫 번째 JSON 객체만 추출"""
    try:
        text = text.split("User Input:")[0]
        text = re.sub(r"```json\s*", "", text)
        text = re.sub(r"```", "", text)
        
        start_index = text.find('{')
        if start_index != -1:
            brace_count = 0
            for i, char in enumerate(text[start_index:], start=start_index):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                if brace_count == 0:
                    return text[start_index:i+1]
        return text.strip()
    except Exception:
        return text.strip()


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
(If 'Selected Schedule ID' exists, the user's command likely applies to this specific schedule.)

{context_section}

[Rules]
1. Intent Classification:
   - "SCHEDULE_MUTATION": When the user wants to Create, Update, or Delete a schedule or task AND all required info is provided.
   - "SCHEDULE_QUERY": When user asks to VIEW/SHOW schedules. (e.g., "보여줘", "알려줘", "뭐야", "있어?")
   - "PRIORITY_QUERY": When user asks about high priority or recommended tasks. (e.g., "우선순위 높은", "추천해줘", "뭐부터 해야 해")
   - "CLARIFY": If essential info is missing. MUST use CLARIFY when:
      * No date/time specified for schedule (e.g., "시험 있어", "과제 해야해" without when)
      * Notification without specific schedule name
      * Ambiguous schedule reference

2. Type Classification (EVENT vs TASK):
   - "EVENT": Has a specific START TIME (e.g., "3시에 회의"). Use 'start_at'.
   - "TASK": Has a DEADLINE with "~까지" or "마감". Use 'end_at'. Goes to sub_task.

3. Determine 'op': "CREATE" (default), "UPDATE", or "DELETE"

4. Determine 'target': "SCHEDULE", "SUB_TASK", or "NOTIFICATION"

5. Time Parsing: If just a number (e.g., "3시"), assume PM unless context suggests otherwise.

6. Payload Construction:
   - "importance_score" (1-10): 10=기말/자격증, 7-9=중간/과제, 4-6=퀴즈/회의, 1-3=개인
   - "estimated_minute": Meeting=60, Report=90, Study=120
   - "category": [수업, 과제, 시험, 공모전, 대외활동, 기타]
   - EVENTs: MUST have 'start_at' AND 'end_at'
   - TASKs: MUST have 'end_at', 'date', 'priority'

7. Output Format:
   - "CLARIFY": Fill 'preserved_info' + 'missingFields'
   - "SCHEDULE_MUTATION": Fill 'actions' list
   - "PRIORITY_QUERY": Set "preserved_info.query_type" to "high_priority"

8. Date Calculation: "내일" = Today + 1 day, "오늘" = Today

9. Notification: If no specific schedule, return CLARIFY asking which schedule.

10. Sub-task for Exams: IF creating 시험/과제, generate 2-3 preparation sub-tasks.

[Examples]
---
# Example 1: Multiple EVENTs
User: "내일 3시에 회의, 5시에 미팅 추가해줘"
JSON: {{
  "intent": "SCHEDULE_MUTATION",
  "type": "EVENT",
  "actions": [
    {{ "op": "CREATE", "target": "SCHEDULE", "payload": {{ "title": "회의", "start_at": "2026-01-16T15:00:00+09:00", "end_at": "2026-01-16T16:00:00+09:00", "importance_score": 5, "estimated_minute": 60, "category": "기타"}} }},
    {{ "op": "CREATE", "target": "SCHEDULE", "payload": {{ "title": "미팅", "start_at": "2026-01-16T17:00:00+09:00", "end_at": "2026-01-16T18:00:00+09:00", "importance_score": 5, "estimated_minute": 60, "category": "기타"}} }}
  ]
}}

# Example 2: TASK with deadline
User: "오늘 6시까지 보고서 작성해야 해"
JSON: {{
  "intent": "SCHEDULE_MUTATION",
  "type": "TASK",
  "actions": [
    {{ "op": "CREATE", "target": "SUB_TASK", "payload": {{ "title": "보고서 작성", "date": "2026-01-15", "end_at": "2026-01-15T18:00:00+09:00", "importance_score": 7, "estimated_minute": 90, "category": "과제", "priority": "high"}} }}
  ]
}}

# Example 3: CLARIFY - No date specified
User: "알고리즘 시험 있어"
JSON: {{
  "intent": "CLARIFY",
  "type": "TASK",
  "actions": [],
  "preserved_info": {{ "title": "알고리즘 시험", "category": "시험", "importance_score": 10 }},
  "missingFields": [{{ "field": "date", "question": "알고리즘 시험이 언제인가요?", "choices": [] }}]
}}

# Example 4: Notification CLARIFY
User: "회의 10분 전에 알림 예약해줘"
JSON: {{
  "intent": "CLARIFY",
  "type": "TASK",
  "actions": [],
  "preserved_info": {{ "minutes_before": 10, "search_keyword": "회의" }},
  "missingFields": [{{ "field": "schedule_title", "question": "어떤 회의에 대한 알림을 설정할까요?", "choices": [] }}]
}}

# Example 5: Exam with sub-tasks
User: "다음주 월요일 알고리즘 시험 추가해줘"
JSON: {{
  "intent": "SCHEDULE_MUTATION",
  "type": "TASK",
  "actions": [
    {{ "op": "CREATE", "target": "SCHEDULE", "payload": {{ "title": "알고리즘 시험", "start_at": "2026-01-19T10:00:00+09:00", "end_at": "2026-01-19T12:00:00+09:00", "importance_score": 10, "estimated_minute": 120, "category": "시험"}} }},
    {{ "op": "CREATE", "target": "SUB_TASK", "payload": {{ "title": "알고리즘 시험 - 개념 정리", "date": "2026-01-16", "end_at": "2026-01-16T23:59:00+09:00", "importance_score": 8, "estimated_minute": 120, "category": "시험", "priority": "high", "tip": "핵심 개념 위주로 1회독"}} }},
    {{ "op": "CREATE", "target": "SUB_TASK", "payload": {{ "title": "알고리즘 시험 - 기출 풀이", "date": "2026-01-17", "end_at": "2026-01-17T23:59:00+09:00", "importance_score": 8, "estimated_minute": 180, "category": "시험", "priority": "high", "tip": "타이머 켜고 실전처럼"}} }}
  ]
}}

# Example 6: Schedule Query
User: "오늘 일정 보여줘"
JSON: {{
  "intent": "SCHEDULE_QUERY",
  "type": "TASK",
  "actions": [],
  "preserved_info": {{ "query_range": "today" }}
}}

# Example 7: Priority Query
User: "우선순위 높은 일정 추천해줘"
JSON: {{
  "intent": "PRIORITY_QUERY",
  "type": "TASK",
  "actions": [],
  "preserved_info": {{ "query_type": "high_priority" }}
}}

# Example 8: Delete
User: "캡스톤 회의 취소해"
JSON: {{
  "intent": "SCHEDULE_MUTATION",
  "type": "EVENT",
  "actions": [ {{ "op": "DELETE", "target": "SCHEDULE", "payload": {{ "title": "캡스톤 회의" }} }} ]
}}
---

User Input: {req.text}
JSON Output:
"""


# ============================================================
# Intent 핸들러
# ============================================================

def handle_clarify(ai_result: AIChatParsed, db: Session) -> str:
    """CLARIFY intent 처리"""
    preserved = ai_result.preserved_info or {}
    search_keyword = preserved.get('search_keyword') or preserved.get('title')
    target_date = preserved.get('date')  # "2026-01-16" 형식
    
    # 날짜 기반 삭제 요청 (예: "내일 일정 취소해줘")
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
                    matching_schedules = [
                        {"id": str(s.schedule_id), "title": s.title, "date": s.start_at.isoformat() if s.start_at else None}
                        for s in schedules
                    ]
                    
                    # missingFields 업데이트
                    if isinstance(field_info, dict):
                        field_info['choices'] = choices
                    else:
                        field_info.choices = choices
                    
                    # preserved_info에 일정 정보 추가
                    ai_result.preserved_info['op'] = 'DELETE'
                    ai_result.preserved_info['matching_schedules'] = matching_schedules
                    
                    date_text = f"{specific_date.month}월 {specific_date.day}일"
                    choice_text = "\n".join([f"• {c}" for c in choices])
                    return f"{date_text}에 {len(schedules)}건의 일정이 있어요. 어떤 걸 취소할까요?\n\n{choice_text}"
                else:
                    date_text = f"{specific_date.month}월 {specific_date.day}일"
                    return f"{date_text}에는 일정이 없어요."
            except ValueError:
                pass
    
    # 키워드로 일정 검색하여 choices 추가
    if search_keyword and ai_result.missingFields:
        related = search_schedules_by_keyword(db, search_keyword)
        if related:
            choices = [s.title for s in related]
            field_info = ai_result.missingFields[0]
            if isinstance(field_info, dict):
                field_info['choices'] = choices
            else:
                field_info.choices = choices
    
    # 메시지 생성
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
    """SCHEDULE_MUTATION intent 처리"""
    actions = ai_result.actions
    if not actions:
        return "처리할 일정이 없습니다."
    
    first_action = actions[0]
    op_type = first_action.op
    target_type = getattr(first_action, 'target', 'SCHEDULE')
    
    # 알림 설정
    if target_type == "NOTIFICATION":
        return handle_notification(ai_result, db)
    
    # 삭제 처리 - DB 검증
    if op_type == "DELETE":
        return handle_delete(ai_result, db)
    
    # 수정
    if op_type == "UPDATE":
        return "일정을 변경할까요?"
    
    # 생성 - 일정/할일 카운트
    schedule_count = sum(1 for a in actions if getattr(a, 'target', 'SCHEDULE') == 'SCHEDULE')
    sub_task_count = sum(1 for a in actions if getattr(a, 'target', 'SCHEDULE') == 'SUB_TASK')
    
    if schedule_count > 0 and sub_task_count > 0:
        return f"일정 {schedule_count}건과 할 일 {sub_task_count}건을 등록할까요?"
    elif sub_task_count > 0:
        return f"할 일 {sub_task_count}건을 등록할까요?"
    return f"일정 {schedule_count}건을 등록할까요?"


def handle_delete(ai_result: AIChatParsed, db: Session) -> str:
    """DELETE 요청 처리 - DB 검증 후 적절한 응답"""
    payload = ai_result.actions[0].payload
    title_keyword = payload.get('title', '')
    
    if not title_keyword:
        return "어떤 일정을 취소할까요?"
    
    # DB에서 해당 제목으로 일정 검색
    matching = search_schedules_by_keyword(db, title_keyword, limit=10)
    
    # 정확히 일치하는 것 우선
    exact_match = [s for s in matching if s.title.lower() == title_keyword.lower()]
    
    if len(exact_match) == 1:
        # 정확히 1건 → 바로 삭제 확인
        schedule = exact_match[0]
        payload['schedule_id'] = str(schedule.schedule_id)
        date_str = schedule.end_at.strftime("%m/%d") if schedule.end_at else ""
        return f"'{schedule.title}' ({date_str}) 일정을 취소할까요?"
    
    if len(matching) == 1:
        # 유사한 거 1건
        schedule = matching[0]
        payload['schedule_id'] = str(schedule.schedule_id)
        date_str = schedule.end_at.strftime("%m/%d") if schedule.end_at else ""
        return f"'{schedule.title}' ({date_str}) 일정을 취소할까요?"
    
    if len(matching) > 1:
        # 여러 건 → CLARIFY로 전환하여 선택 요청
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
            "matching_schedules": [
                {"id": str(s.schedule_id), "title": s.title, "date": s.end_at.isoformat() if s.end_at else None}
                for s in matching
            ]
        }
        choice_text = "\n".join([f"• {c}" for c in choices])
        return f"'{title_keyword}' 관련 일정이 여러 개 있어요. 어떤 걸 취소할까요?\n\n{choice_text}"
    
    # 0건 - 찾을 수 없음
    return f"'{title_keyword}' 일정을 찾을 수 없어요."


def handle_notification(ai_result: AIChatParsed, db: Session) -> str:
    """알림 설정 처리"""
    payload = ai_result.actions[0].payload
    schedule_title = payload.get('schedule_title', '')
    
    if not schedule_title:
        return "알림 설정을 변경할까요?"
    
    matching = search_schedules_by_keyword(db, schedule_title, limit=1)
    exact_match = [s for s in matching if s.title == schedule_title]
    
    if exact_match:
        payload['schedule_id'] = str(exact_match[0].schedule_id)
        return f"'{schedule_title}' 일정에 알림을 설정할까요?"
    
    if matching:
        return f"'{schedule_title}' 일정을 찾지 못했어요. 혹시 '{matching[0].title}'을 말씀하신 건가요?"
    
    # 일정이 없으면 CLARIFY로 전환
    ai_result.actions = [
        Action(op="CREATE", target="SCHEDULE", payload={"title": schedule_title, "importance_score": 5, "category": "기타"})
    ]
    ai_result.missingFields = [
        MissingField(field="schedule_time", question=f"'{schedule_title}' 일정이 없어요. 새로 추가하려면 시간을 알려주세요! (예: 내일 3시)", choices=[])
    ]
    ai_result.intent = "CLARIFY"
    ai_result.preserved_info = {**payload, 'pending_title': schedule_title}
    return f"'{schedule_title}' 일정이 등록되어 있지 않아요. 새로 추가하려면 시간을 알려주세요! (예: 내일 3시)"


def handle_priority_query(ai_result: AIChatParsed, db: Session) -> str:
    """PRIORITY_QUERY intent 처리"""
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
        return "현재 우선순위가 높은 일정이 없어요. 🎉 여유롭게 하루를 보내세요!"
    
    # 구조화된 데이터 추가
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
    """SCHEDULE_QUERY intent 처리"""
    now = datetime.now()
    preserved = ai_result.preserved_info or {}
    query_range = preserved.get("query_range", "today")
    
    # 날짜 범위 계산
    range_config = {
        "today": (now.replace(hour=0, minute=0, second=0), now.replace(hour=23, minute=59, second=59), "오늘"),
        "tomorrow": ((now + timedelta(days=1)).replace(hour=0, minute=0, second=0), (now + timedelta(days=1)).replace(hour=23, minute=59, second=59), "내일"),
        "this_week": (
            (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0),
            (now - timedelta(days=now.weekday()) + timedelta(days=6, hours=23, minutes=59, seconds=59)),
            "이번 주"
        ),
    }
    
    # 특정 날짜 형식 처리 (예: "2026-01-20")
    if query_range not in range_config:
        try:
            specific_date = datetime.strptime(query_range, "%Y-%m-%d")
            start_date = specific_date.replace(hour=0, minute=0, second=0)
            end_date = specific_date.replace(hour=23, minute=59, second=59)
            period_text = f"{specific_date.month}월 {specific_date.day}일"
        except ValueError:
            # 파싱 실패 시 기본값 (오늘)
            start_date = now.replace(hour=0, minute=0, second=0)
            end_date = now.replace(hour=23, minute=59, second=59)
            period_text = "오늘"
    else:
        start_date, end_date, period_text = range_config[query_range]
    
    schedules = get_schedules_for_period(db, start_date, end_date)
    
    if schedules:
        schedule_text = format_schedules_for_display(schedules)
        return f"{period_text} 일정이에요! 📅\n\n{schedule_text}\n\n총 {len(schedules)}건의 일정이 있어요."
    return f"{period_text}은 등록된 일정이 없어요. 🎉 여유로운 하루 보내세요!"


# ============================================================
# 메인 API 엔드포인트
# ============================================================

@router.post("/chat", response_model=APIResponse, response_model_exclude_none=True)
async def chat_with_ai(req: ChatRequest, db: Session = Depends(get_db)):
    try:
        model = get_watson_model()
        now = datetime.now()
        current_date_str = req.base_date or now.strftime("%Y-%m-%d (%A)")
        
        # AI 호출
        system_prompt = build_system_prompt(req, current_date_str)
        generated_response = model.generate_text(prompt=system_prompt)
        
        # JSON 파싱
        clean_json_str = extract_json_from_text(generated_response)
        parsed_data = json.loads(clean_json_str)
        ai_result = AIChatParsed(**parsed_data)
        
        # Intent별 처리
        intent_handlers = {
            "CLARIFY": handle_clarify,
            "SCHEDULE_MUTATION": handle_mutation,
            "PRIORITY_QUERY": handle_priority_query,
            "SCHEDULE_QUERY": handle_schedule_query,
        }
        
        handler = intent_handlers.get(ai_result.intent)
        assistant_msg = handler(ai_result, db) if handler else "일정을 확인했습니다."
        
        # 응답 반환
        response_data = ChatResponseData(parsed_result=ai_result, assistant_message=assistant_msg)
        return APIResponse(status=200, message="Success", data=response_data)

    except json.JSONDecodeError:
        print(f"Failed JSON: {generated_response}")
        return APIResponse(status=500, message="AI 응답을 분석하는 데 실패했습니다.")
    except Exception as e:
        print(f"Error: {str(e)}")
        return APIResponse(status=500, message=f"Server Error: {str(e)}")
