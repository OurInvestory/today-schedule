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

# --- Watsonx 설정 ---
WATSONX_API_KEY = os.getenv("WATSONX_API_KEY")
WATSONX_URL = os.getenv("WATSONX_URL")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID")
WATSONX_MODEL_ID = os.getenv("WATSONX_MODEL_ID", "meta-llama/llama-3-3-70b-instruct")

credentials = {
    "url": WATSONX_URL,
    "apikey": WATSONX_API_KEY
}

# AI가 "User Input:"이라는 글자를 쓰려고 하면 즉시 멈추게 합니다.
generate_params = {
    GenParams.DECODING_METHOD: DecodingMethods.GREEDY,
    GenParams.MAX_NEW_TOKENS: 500,  
    GenParams.MIN_NEW_TOKENS: 1,
    GenParams.TEMPERATURE: 0,
    GenParams.STOP_SEQUENCES: ["User Input:", "User:", "\n\n\n", "```\n"] 
}

def get_watson_model():
    return ModelInference(
        model_id=WATSONX_MODEL_ID,
        params=generate_params,
        credentials=credentials,
        project_id=WATSONX_PROJECT_ID
    )

def get_schedules_for_period(db: Session, start_date: datetime, end_date: datetime) -> list:
    """지정된 기간의 일정을 조회합니다."""
    test_user_id = "7822a162-788d-4f36-9366-c956a68393e1"
    schedules = db.query(Schedule).filter(
        and_(
            Schedule.user_id == test_user_id,
            Schedule.end_at >= start_date,
            Schedule.end_at <= end_date
        )
    ).order_by(Schedule.end_at.asc()).all()
    return schedules

def search_schedules_by_keyword(db: Session, keyword: str, limit: int = 5) -> list:
    """키워드가 포함된 최근 일정을 검색합니다."""
    test_user_id = "7822a162-788d-4f36-9366-c956a68393e1"
    now = datetime.now()
    # 최근 30일 이내 + 앞으로 14일 이내 일정에서 검색
    start_date = now - timedelta(days=30)
    end_date = now + timedelta(days=14)
    
    schedules = db.query(Schedule).filter(
        and_(
            Schedule.user_id == test_user_id,
            Schedule.title.ilike(f"%{keyword}%"),
            Schedule.start_at >= start_date,
            Schedule.start_at <= end_date
        )
    ).order_by(Schedule.start_at.asc()).limit(limit).all()
    return schedules

# 카테고리 영어→한국어 매핑
CATEGORY_MAP = {
    "class": "수업",
    "assignment": "과제",
    "exam": "시험",
    "contest": "공모전",
    "activity": "대외활동",
    "team": "팀 프로젝트",
    "personal": "개인",
    "other": "기타",
}

def translate_category(category: str) -> str:
    """영어 카테고리를 한국어로 변환합니다."""
    if not category:
        return "기타"
    return CATEGORY_MAP.get(category.lower(), category)

def format_schedules_for_display(schedules: list) -> str:
    """일정 목록을 사람이 읽기 좋은 형식으로 변환합니다."""
    if not schedules:
        return "등록된 일정이 없어요."
    
    result = []
    for s in schedules:
        date_str = s.end_at.strftime("%m/%d(%a)") if s.end_at else ""
        time_str = s.end_at.strftime("%H:%M") if s.end_at else ""
        category = translate_category(s.category)
        result.append(f"• [{category}] {s.title} - {date_str} {time_str}")
    
    return "\n".join(result)

def extract_json_from_text(text: str) -> str:
    """
    텍스트에서 첫 번째 JSON 객체만 정확하게 추출합니다.
    """
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
                    return text[start_index : i+1]
        
        return text.strip()
    except Exception:
        return text.strip()

@router.post("/chat", response_model=APIResponse, response_model_exclude_none=True)
async def chat_with_ai(req: ChatRequest, db: Session = Depends(get_db)):
    try:
        model = get_watson_model()
        now = datetime.now()
        current_date_str = req.base_date or now.strftime("%Y-%m-%d (%A)")
        
        context_section = ""
        if req.user_context:
            context_dump = json.dumps(req.user_context, ensure_ascii=False)
            
            # 이전 대화가 알림 설정 관련 CLARIFY였는지 확인
            is_notification_clarify = req.user_context.get('previous_intent') == 'CLARIFY' and req.user_context.get('minutes_before')
            
            context_section = f"""
[Previous Conversation History]
The user is continuing a conversation. The previous state was:
{context_dump}

INSTRUCTION: 
1. Merge the 'User Input' with the info in [Previous Conversation History].
2. If the user answers a missing field (e.g., subject name), combine it with the previous time/date to create a 'SCHEDULE_MUTATION'.
3. **IMPORTANT**: If 'minutes_before' exists in context and user provides a schedule/event name, this is a NOTIFICATION setup request. Create action with target: 'NOTIFICATION'.
"""
            if is_notification_clarify:
                context_section += f"""
4. **NOTIFICATION MODE**: The user previously asked to set an alarm {req.user_context.get('minutes_before')} minutes before.
   - DO NOT create a new schedule. Create a NOTIFICATION action instead.
   - Use: {{"op": "UPDATE", "target": "NOTIFICATION", "payload": {{"schedule_title": "<user's answer>", "minutes_before": {req.user_context.get('minutes_before')}}}}}
"""
        else:
            context_section = "\n[Previous Conversation History]\nNone (New conversation start)"

        system_prompt = f"""You are a smart academic scheduler AI.
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
   - "SCHEDULE_MUTATION": When the user wants to Create, Update, or Delete a schedule or task.
   - "SCHEDULE_QUERY": When user asks to VIEW/SHOW schedules. (e.g., "보여줘", "알려줘", "뭐야", "있어?")
   - "PRIORITY_QUERY": When user asks about high priority or recommended tasks. (e.g., "우선순위 높은", "추천해줘", "뭐부터 해야 해")
   - "CLARIFY": If essential info is missing OR if clarification is needed (e.g., for notification - which schedule?).

2. Type Classification (EVENT vs TASK):
   - "EVENT": Has a specific START TIME (e.g., "3시에 회의", "오후 5시 미팅"). Use 'start_at'.
   - "TASK": Has a DEADLINE with "~까지" or "마감" (e.g., "6시까지 보고서", "내일까지 과제"). Use 'end_at'. Goes to sub_task.

3. Determine 'op' (Operation):
   - "CREATE": Default. (e.g., "Add", "Schedule", "New", "추가해줘")
   - "UPDATE": When user wants to change time, title, or details. (e.g., "Delay", "Move", "Change", "Reschedule")
   - "DELETE": When user wants to remove. (e.g., "Cancel", "Delete", "Remove")

4. Determine 'target':
   - "SCHEDULE": For EVENTs with specific time (회의, 미팅, 수업). Creates a Schedule.
   - "SUB_TASK": For TASKs with deadline (~까지, 해야 해). Creates a SubTask/Todo.
   - "NOTIFICATION": For alarm/reminder settings.

5. Time Parsing (CRITICAL):
   - Default assumption: If just a number (e.g., "3시", "5시"), assume PM (오후) unless context suggests otherwise.
   - "3시에 회의" → start_at: 15:00 (3 PM), type: EVENT, target: SCHEDULE
   - "6시까지 보고서" → end_at: 18:00 (6 PM), type: TASK, target: SUB_TASK
   - Multiple items: Parse each item separately into actions array.

6. Payload Construction:
   - "importance_score" (int, 1-10): 
      * 10: Final exams, major certification tests.
      * 7-9: Midterms, major assignments, critical team projects.
      * 4-6: Quizzes, regular assignments, meetings.
      * 1-3: Personal tasks, hobbies, routine activities.
   - "estimated_minute" (int): Estimated time (Meeting: 60, Report: 90, Study: 120).
   - "category" (string): Must be one of [수업, 과제, 시험, 공모전, 대외활동, 기타].
   - For EVENTs (target: SCHEDULE): MUST have 'start_at' AND 'end_at' (1 hour default if only start given).
   - For TASKs (target: SUB_TASK): MUST have 'end_at' (deadline), 'date' (YYYY-MM-DD), 'priority' (high/medium/low).
   - "DELETE": Must include 'title'.
   
7. Output Format:
   - "CLARIFY": Save partial info to 'preserved_info'. Fill 'missingFields' with {{ "field": "...", "question": "..." }}.
   - "SCHEDULE_MUTATION": Fill 'actions' list. EACH item is a separate action.
   - "PRIORITY_QUERY": Set "preserved_info.query_type" to "high_priority".

8. Date Calculation:
   - Always calculate relative dates into exact ISO8601 timestamps based on [Current Environment] date.
   - "내일" = Today + 1 day
   - "오늘" = Today

9. Notification Clarification:
   - IF user asks to set alarm but DOESN'T specify which schedule (e.g., "회의 10분 전에 알림"):
   - MUST return CLARIFY intent asking which specific schedule.
   - preserved_info should contain: minutes_before, notification_msg (if any).
   - missingFields: [{{ "field": "schedule_title", "question": "어떤 일정에 대한 알림을 설정할까요?" }}]

10. Sub-task for Exams/Assignments:
   - IF creating 시험/과제/공모전: Generate 2-3 preparation sub-tasks with 'target': 'SUB_TASK'.

[Examples]
---
# Example 1: Multiple EVENTs with specific times
User: "내일 3시에 회의, 5시에 미팅 추가해줘"
Context: Today is 2026-01-14, Tomorrow is 2026-01-15.
JSON: {{
  "intent": "SCHEDULE_MUTATION",
  "type": "EVENT",
  "actions": [
    {{ "op": "CREATE", "target": "SCHEDULE", "payload": {{ "title": "회의", "start_at": "2026-01-15T15:00:00+09:00", "end_at": "2026-01-15T16:00:00+09:00", "importance_score": 5, "estimated_minute": 60, "category": "기타"}} }},
    {{ "op": "CREATE", "target": "SCHEDULE", "payload": {{ "title": "미팅", "start_at": "2026-01-15T17:00:00+09:00", "end_at": "2026-01-15T18:00:00+09:00", "importance_score": 5, "estimated_minute": 60, "category": "기타"}} }}
  ]
}}

# Example 2: TASK with deadline (~까지) -> SubTask
User: "오늘 6시까지 보고서 작성해야 해"
Context: Today is 2026-01-14.
JSON: {{
  "intent": "SCHEDULE_MUTATION",
  "type": "TASK",
  "actions": [
    {{ "op": "CREATE", "target": "SUB_TASK", "payload": {{ "title": "보고서 작성", "date": "2026-01-14", "end_at": "2026-01-14T18:00:00+09:00", "importance_score": 7, "estimated_minute": 90, "category": "과제", "priority": "high"}} }}
  ]
}}

# Example 2-1: TASK with natural deadline expression
User: "오늘 저녁까지 보고서 작성 할 일 추가"
Context: Today is 2026-01-14.
JSON: {{
  "intent": "SCHEDULE_MUTATION",
  "type": "TASK",
  "actions": [
    {{ "op": "CREATE", "target": "SUB_TASK", "payload": {{ "title": "보고서 작성", "date": "2026-01-14", "end_at": "2026-01-14T18:00:00+09:00", "importance_score": 7, "estimated_minute": 90, "category": "과제", "priority": "high"}} }}
  ]
}}

# Example 3: Notification without specifying schedule -> CLARIFY
User: "회의 10분 전에 알림 예약해줘"
JSON: {{
  "intent": "CLARIFY",
  "type": "TASK",
  "actions": [],
  "preserved_info": {{ "minutes_before": 10, "notification_msg": "회의 10분 전입니다!", "search_keyword": "회의" }},
  "missingFields": [{{ "field": "schedule_title", "question": "어떤 회의에 대한 알림을 설정할까요?", "choices": [] }}]
}}

# Example 4: Notification with specific schedule
User: "캡스톤 회의 10분 전에 알림 설정해줘"
JSON: {{
  "intent": "SCHEDULE_MUTATION",
  "type": "EVENT",
  "actions": [
    {{ "op": "UPDATE", "target": "NOTIFICATION", "payload": {{ "schedule_title": "캡스톤 회의", "minutes_before": 10, "notification_msg": "캡스톤 회의 10분 전입니다!" }} }}
  ]
}}

# Example 5: Priority Query
User: "우선순위 높은 일정 추천해줘"
JSON: {{
  "intent": "PRIORITY_QUERY",
  "type": "TASK",
  "actions": [],
  "preserved_info": {{ "query_type": "high_priority" }}
}}

# Example 6: Exam with sub-tasks
User: "다음주 월요일 알고리즘 시험 추가해줘"
Context: Today is 2026-01-14 (Tue). Next Mon is 2026-01-19.
JSON: {{
  "intent": "SCHEDULE_MUTATION",
  "type": "TASK",
  "actions": [
    {{ "op": "CREATE", "target": "SCHEDULE", "payload": {{ "title": "알고리즘 시험", "start_at": "2026-01-19T10:00:00+09:00", "end_at": "2026-01-19T12:00:00+09:00", "importance_score": 10, "estimated_minute": 120, "category": "시험"}} }},
    {{ "op": "CREATE", "target": "SUB_TASK", "payload": {{ "title": "알고리즘 시험 - 개념 정리", "date": "2026-01-16", "end_at": "2026-01-16T23:59:00+09:00", "importance_score": 8, "estimated_minute": 120, "category": "시험", "priority": "high", "tip": "핵심 개념 위주로 1회독"}} }},
    {{ "op": "CREATE", "target": "SUB_TASK", "payload": {{ "title": "알고리즘 시험 - 기출 풀이", "date": "2026-01-17", "end_at": "2026-01-17T23:59:00+09:00", "importance_score": 8, "estimated_minute": 180, "category": "시험", "priority": "high", "tip": "타이머 켜고 실전처럼"}} }},
    {{ "op": "CREATE", "target": "SUB_TASK", "payload": {{ "title": "알고리즘 시험 - 최종 복습", "date": "2026-01-18", "end_at": "2026-01-18T23:59:00+09:00", "importance_score": 9, "estimated_minute": 120, "category": "시험", "priority": "high", "tip": "틀린 문제 위주 재점검"}} }}
  ]
}}

# Example 7: Delete
User: "캡스톤 회의 취소해"
JSON: {{
  "intent": "SCHEDULE_MUTATION",
  "type": "EVENT",
  "actions": [ {{ "op": "DELETE", "target": "SCHEDULE", "payload": {{ "title": "캡스톤 회의" }} }} ]
}}

# Example 8: Schedule Query (View)
User: "오늘 일정 보여줘"
JSON: {{
  "intent": "SCHEDULE_QUERY",
  "type": "TASK",
  "actions": [],
  "preserved_info": {{ "query_range": "today" }}
}}

---

User Input: {req.text}
JSON Output:
"""
        
        generated_response = model.generate_text(prompt=system_prompt)

        clean_json_str = extract_json_from_text(generated_response)
        parsed_data = json.loads(clean_json_str)
        ai_parsed_result = AIChatParsed(**parsed_data)
        
        # 메시지 생성 로직
        assistant_msg = "일정을 확인했습니다."
        
        if ai_parsed_result.intent == "CLARIFY":
            # 알림 설정 관련 CLARIFY인 경우, 키워드로 일정 검색하여 choices 제공
            preserved = ai_parsed_result.preserved_info or {}
            search_keyword = preserved.get('search_keyword') or preserved.get('notification_msg', '').split()[0] if preserved.get('notification_msg') else None
            
            if search_keyword and ai_parsed_result.missingFields:
                # 키워드로 관련 일정 검색
                related_schedules = search_schedules_by_keyword(db, search_keyword)
                if related_schedules:
                    choices = [s.title for s in related_schedules]
                    # missingFields의 첫 번째 항목에 choices 추가
                    field_info = ai_parsed_result.missingFields[0]
                    if isinstance(field_info, dict):
                        field_info['choices'] = choices
                    else:
                        field_info.choices = choices
            
            if ai_parsed_result.missingFields:
                # missingFields 구조가 바뀌었을 수 있으므로 안전하게 처리
                field_info = ai_parsed_result.missingFields[0]
                # Pydantic 모델 or Dict 처리
                if isinstance(field_info, dict):
                    question = field_info.get('question', "정보가 부족합니다.")
                    choices = field_info.get('choices', [])
                else: 
                    question = getattr(field_info, 'question', "정보가 부족합니다.")
                    choices = getattr(field_info, 'choices', [])
                
                assistant_msg = question
                if choices:
                    choice_text = "\n".join([f"• {c}" for c in choices])
                    assistant_msg = f"{question}\n\n다음 일정을 찾았어요:\n{choice_text}"
            else:
                assistant_msg = "정보가 부족합니다. 조금 더 자세히 말씀해 주세요."
                
        elif ai_parsed_result.intent == "SCHEDULE_MUTATION":
            actions = ai_parsed_result.actions
            action_cnt = len(actions)
            if action_cnt > 0:
                op_type = actions[0].op
                target_type = getattr(actions[0], 'target', 'SCHEDULE')

                if target_type == "NOTIFICATION":
                    # 알림 설정 시 DB에서 해당 일정 확인
                    payload = actions[0].payload
                    schedule_title = payload.get('schedule_title', '')
                    
                    if schedule_title:
                        # DB에서 해당 제목의 일정 검색
                        matching_schedules = search_schedules_by_keyword(db, schedule_title, limit=1)
                        exact_match = [s for s in matching_schedules if s.title == schedule_title]
                        
                        if exact_match:
                            # 일정이 존재하면 알림 설정 진행
                            schedule = exact_match[0]
                            # schedule_id를 payload에 추가
                            payload['schedule_id'] = str(schedule.id)
                            assistant_msg = f"'{schedule_title}' 일정에 알림을 설정할까요?"
                        elif matching_schedules:
                            # 유사한 일정이 있는 경우
                            similar_title = matching_schedules[0].title
                            assistant_msg = f"'{schedule_title}' 일정을 찾지 못했어요. 혹시 '{similar_title}'을 말씀하신 건가요?"
                        else:
                            # 일정이 없으면 새 일정 생성 유도
                            # actions를 일정 생성으로 변경
                            ai_parsed_result.actions = [
                                Action(
                                    op="CREATE",
                                    target="SCHEDULE",
                                    payload={
                                        "title": schedule_title,
                                        "importance_score": 5,
                                        "category": "기타"
                                    }
                                )
                            ]
                            ai_parsed_result.missingFields = [
                                MissingField(
                                    field="schedule_time",
                                    question=f"'{schedule_title}' 일정이 없어요. 새로 추가하려면 시간을 알려주세요! (예: 내일 3시)",
                                    choices=[]
                                )
                            ]
                            ai_parsed_result.intent = "CLARIFY"
                            ai_parsed_result.preserved_info = {
                                **payload,
                                'pending_title': schedule_title
                            }
                            assistant_msg = f"'{schedule_title}' 일정이 등록되어 있지 않아요. 새로 추가하려면 시간을 알려주세요! (예: 내일 3시)"
                    else:
                        assistant_msg = "알림 설정을 변경할까요?"
                elif op_type == "DELETE":
                    assistant_msg = "해당 일정을 취소할까요?"
                elif op_type == "UPDATE":
                    assistant_msg = "일정을 변경할까요?"
                else: # CREATE
                    # 일정과 할 일 분리해서 카운트
                    schedule_count = sum(1 for a in actions if getattr(a, 'target', 'SCHEDULE') == 'SCHEDULE')
                    sub_task_count = sum(1 for a in actions if getattr(a, 'target', 'SCHEDULE') == 'SUB_TASK')
                    
                    if schedule_count > 0 and sub_task_count > 0:
                        assistant_msg = f"일정 {schedule_count}건과 할 일 {sub_task_count}건을 등록할까요?"
                    elif sub_task_count > 0:
                        assistant_msg = f"할 일 {sub_task_count}건을 등록할까요?"
                    else:
                        assistant_msg = f"일정 {schedule_count}건을 등록할까요?"
            else:
                assistant_msg = "처리할 일정이 없습니다."
        
        elif ai_parsed_result.intent == "PRIORITY_QUERY":
            # 우선순위 높은 일정 조회
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now + timedelta(days=14)  # 2주 이내 일정
            
            schedules = get_schedules_for_period(db, start_date, end_date)
            
            # priority_score 기준으로 정렬 (높은 순)
            high_priority = [s for s in schedules if s.priority_score and s.priority_score >= 7]
            high_priority.sort(key=lambda x: x.priority_score or 0, reverse=True)
            
            if high_priority:
                schedule_text = format_schedules_for_display(high_priority[:5])  # 상위 5개
                assistant_msg = f"우선순위가 높은 일정이에요! 🔥\n\n{schedule_text}\n\n총 {len(high_priority)}건의 중요 일정이 있어요."
            else:
                assistant_msg = "현재 우선순위가 높은 일정이 없어요. 🎉 여유롭게 하루를 보내세요!"
        
        elif ai_parsed_result.intent == "SCHEDULE_QUERY":
            # 일정 조회 처리
            preserved = ai_parsed_result.preserved_info or {}
            query_range = preserved.get("query_range", "today")
            
            # 날짜 범위 계산
            if query_range == "today":
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = now.replace(hour=23, minute=59, second=59)
                period_text = "오늘"
            elif query_range == "tomorrow":
                tomorrow = now + timedelta(days=1)
                start_date = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = tomorrow.replace(hour=23, minute=59, second=59)
                period_text = "내일"
            elif query_range == "this_week":
                start_date = now - timedelta(days=now.weekday())
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59)
                period_text = "이번 주"
            elif query_range == "next_week":
                start_date = now + timedelta(days=7-now.weekday())
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59)
                period_text = "다음 주"
            else:
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = now + timedelta(days=7)
                period_text = "앞으로"
            
            # DB에서 일정 조회
            schedules = get_schedules_for_period(db, start_date, end_date)
            
            if schedules:
                schedule_text = format_schedules_for_display(schedules)
                assistant_msg = f"{period_text} 일정이에요! 📅\n\n{schedule_text}\n\n총 {len(schedules)}건의 일정이 있어요."
            else:
                assistant_msg = f"{period_text}은 등록된 일정이 없어요. 🎉 여유로운 하루 보내세요!"

        response_data = ChatResponseData(
            parsed_result=ai_parsed_result,
            assistant_message=assistant_msg
        )
        return APIResponse(status=200, message="Success", data=response_data)

    except json.JSONDecodeError:
        print(f"Failed JSON: {generated_response}") # 디버깅용 로그
        return APIResponse(status=500, message="AI 응답을 분석하는 데 실패했습니다.")
    except Exception as e:
        print(f"Error: {str(e)}")
        return APIResponse(status=500, message=f"Server Error: {str(e)}")