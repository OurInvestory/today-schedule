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
    AIChatParsed
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

def format_schedules_for_display(schedules: list) -> str:
    """일정 목록을 사람이 읽기 좋은 형식으로 변환합니다."""
    if not schedules:
        return "등록된 일정이 없어요."
    
    result = []
    for s in schedules:
        date_str = s.end_at.strftime("%m/%d(%a)") if s.end_at else ""
        time_str = s.end_at.strftime("%H:%M") if s.end_at else ""
        category = s.category or "기타"
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
            context_section = f"""
[Previous Conversation History]
The user is continuing a conversation. The previous state was:
{context_dump}

INSTRUCTION: 
1. Merge the 'User Input' with the info in [Previous Conversation History].
2. If the user answers a missing field (e.g., subject name), combine it with the previous time/date to create a 'SCHEDULE_MUTATION'.
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
   - "PRIORITY_QUERY": When user asks for high-priority items or recommendations.
   - "CLARIFY": If essential info is missing, or if the target is unclear for notification/alarm.
   - "IMAGE_ANALYSIS": When user mentions analyzing an image/photo (시간표, 공모전, etc).

2. Determine 'type' (CRITICAL - MUST be correct):
   - "EVENT": Time-bound appointments with specific start and end times (회의, 미팅, 수업, 발표).
   - "TASK": To-do items with a deadline. Things to complete by a certain time (과제, 보고서 작성, 시험 준비).

3. Determine 'op' (Operation):
   - "CREATE": Default. (e.g., "Add", "Schedule", "New", "추가")
   - "UPDATE": When user wants to change time, title, or details. (e.g., "Delay", "Move", "Change")
   - "DELETE": When user wants to remove. (e.g., "Cancel", "Delete", "Remove", "취소")

4. Payload Construction (Mandatory for CREATE/UPDATE):
   COMMON FIELDS:
   - "title" (string): Name of the event or task.
   - "category" (string): One of [수업, 과제, 시험, 공모전, 대외활동, 스터디, 미팅, 기타].
   - "importance_score" (int, 1-10): Priority level.
      * 10: Final exams, major certification tests.
      * 7-9: Midterms, major assignments, critical team projects.
      * 4-6: Quizzes, regular assignments, meetings.
      * 1-3: Personal tasks, hobbies, routine activities.
   - "estimated_minute" (int): Duration in minutes.
   
   FOR "EVENT" type (time-bound appointments):
   - "start_at" (ISO8601): Event start time. REQUIRED for events.
   - "end_at" (ISO8601): Event end time. Default to start_at + estimated_minute if not specified.
   
   FOR "TASK" type (to-do items):
   - "date" (YYYY-MM-DD): The due date for the task. REQUIRED for tasks.
   - "end_at" (ISO8601): The deadline time. Default to 23:59 if only "까지" is mentioned.

5. Multiple Items in One Request:
   - If user mentions multiple items (e.g., "회의, 미팅"), create SEPARATE actions for EACH.
   - Parse conjunctions like "그리고", ",", "랑", "하고" to split items.

6. Time Parsing Rules:
   - "3시" without AM/PM: Assume PM (15:00) for afternoon context, AM for morning context.
   - "오후 3시" = 15:00, "오전 3시" = 03:00
   - "6시까지" = deadline at 18:00, type should be TASK.
   - "6시에" = event at 18:00, type should be EVENT.
   - Always calculate relative dates based on [Current Environment].

7. Notification/Alarm Handling:
   - IF user asks to set alarm without specifying which schedule: intent="CLARIFY".
   - Ask "어떤 일정에 알림을 설정할까요?" and preserve "minutes_before" info.
   - IF schedule is specified: Set target="NOTIFICATION" with schedule_title and minutes_before.

8. Sub-task Auto-Generation:
   - IF creating a TASK with category in ['시험', '과제', '공모전']:
   - Generate 2-3 preparation sub-tasks leading up to the deadline.
   - Sub-task format: title="[준비] {{Title}} - {{Step}}", tip="practical advice (max 20 chars)"

9. Image Analysis Request:
   - IF user mentions analyzing 시간표/사진/이미지 for schedules:
   - intent="IMAGE_ANALYSIS", preserved_info.image_type = "timetable" | "contest" | "other"
   - The frontend will handle actual image upload and analysis.

10. Priority Query:
   - IF user asks for high-priority items or recommendations:
   - intent="PRIORITY_QUERY", preserved_info.query_type = "high_priority"

[Examples]
---
# Example 1: Multiple Events in One Request
User: "내일 3시에 회의, 5시에 미팅 추가해줘"
Context: Today is 2026-01-14. Tomorrow is 2026-01-15.
JSON: {{
  "intent": "SCHEDULE_MUTATION",
  "type": "EVENT",
  "actions": [
    {{ "op": "CREATE", "target": "SCHEDULE", "payload": {{ "title": "회의", "start_at": "2026-01-15T15:00:00+09:00", "end_at": "2026-01-15T16:00:00+09:00", "importance_score": 5, "estimated_minute": 60, "category": "미팅" }} }},
    {{ "op": "CREATE", "target": "SCHEDULE", "payload": {{ "title": "미팅", "start_at": "2026-01-15T17:00:00+09:00", "end_at": "2026-01-15T18:00:00+09:00", "importance_score": 5, "estimated_minute": 60, "category": "미팅" }} }}
  ]
}}

# Example 2: Task with Deadline (Sub-task)
User: "오늘 6시까지 보고서 작성해야 해"
Context: Today is 2026-01-14.
JSON: {{
  "intent": "SCHEDULE_MUTATION",
  "type": "TASK",
  "actions": [
    {{ "op": "CREATE", "target": "SUB_TASK", "payload": {{ "title": "보고서 작성", "date": "2026-01-14", "end_at": "2026-01-14T18:00:00+09:00", "importance_score": 7, "estimated_minute": 120, "category": "과제" }} }}
  ]
}}

# Example 3: Notification - Need Clarification
User: "회의 10분 전에 알림 예약해줘"
JSON: {{
  "intent": "CLARIFY",
  "type": "EVENT",
  "missingFields": [{{ "field": "schedule_title", "question": "어떤 회의에 알림을 설정할까요? 일정 목록에서 선택하거나 회의 이름을 알려주세요." }}],
  "preserved_info": {{ "minutes_before": 10, "target": "NOTIFICATION" }}
}}

# Example 4: Notification - With Schedule Name
User: "캡스톤 회의 10분 전에 알림 예약해줘"
JSON: {{
  "intent": "SCHEDULE_MUTATION",
  "type": "EVENT",
  "actions": [{{ 
    "op": "UPDATE", 
    "target": "NOTIFICATION",
    "payload": {{ "schedule_title": "캡스톤 회의", "minutes_before": 10, "notification_msg": "캡스톤 회의 10분 전입니다!" }} 
  }}]
}}

# Example 5: Image Analysis Request
User: "시간표 사진에 있는 강의 추가해줘"
JSON: {{
  "intent": "IMAGE_ANALYSIS",
  "type": "EVENT",
  "actions": [],
  "preserved_info": {{ "image_type": "timetable", "message": "시간표 이미지를 업로드해 주세요. 📸" }}
}}

# Example 6: Contest Image Analysis
User: "공모전 포스터 분석해줘"
JSON: {{
  "intent": "IMAGE_ANALYSIS",
  "type": "TASK",
  "actions": [],
  "preserved_info": {{ "image_type": "contest", "message": "공모전 포스터 이미지를 업로드해 주세요. 분석 후 일정과 준비 할 일을 추천해 드릴게요! 📸" }}
}}

# Example 7: Priority Query
User: "우선순위 높은 일정 추천해줘"
JSON: {{
  "intent": "PRIORITY_QUERY",
  "type": "TASK",
  "actions": [],
  "preserved_info": {{ "query_type": "high_priority" }}
}}

# Example 8: Schedule Query (Today)
User: "오늘 일정 보여줘"
JSON: {{
  "intent": "SCHEDULE_QUERY",
  "type": "TASK",
  "actions": [],
  "preserved_info": {{ "query_range": "today" }}
}}

# Example 9: Exam with Sub-tasks
User: "다음주 월요일 알고리즘 시험 추가해줘"
Context: Today is 2026-01-14 (Tue). Next Mon is 2026-01-19.
JSON: {{
  "intent": "SCHEDULE_MUTATION",
  "type": "TASK",
  "actions": [
    {{ "op": "CREATE", "target": "SCHEDULE", "payload": {{ "title": "알고리즘 시험", "start_at": "2026-01-19T10:00:00+09:00", "end_at": "2026-01-19T12:00:00+09:00", "importance_score": 10, "estimated_minute": 120, "category": "시험" }} }},
    {{ "op": "CREATE", "target": "SUB_TASK", "payload": {{ "title": "[준비] 알고리즘 시험 - 개념 정리", "date": "2026-01-16", "importance_score": 8, "estimated_minute": 120, "category": "시험", "tip": "핵심 개념 위주로 1회독" }} }},
    {{ "op": "CREATE", "target": "SUB_TASK", "payload": {{ "title": "[준비] 알고리즘 시험 - 기출 풀이", "date": "2026-01-17", "importance_score": 8, "estimated_minute": 180, "category": "시험", "tip": "타이머 켜고 실전처럼" }} }},
    {{ "op": "CREATE", "target": "SUB_TASK", "payload": {{ "title": "[준비] 알고리즘 시험 - 최종 복습", "date": "2026-01-18", "importance_score": 9, "estimated_minute": 120, "category": "시험", "tip": "틀린 문제 위주 재점검" }} }}
  ]
}}

# Example 10: Delete
User: "캡스톤 회의 취소해"
JSON: {{
  "intent": "SCHEDULE_MUTATION",
  "type": "EVENT",
  "actions": [{{ "op": "DELETE", "target": "SCHEDULE", "payload": {{ "title": "캡스톤 회의" }} }}]
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
            if ai_parsed_result.missingFields:
                # missingFields 구조가 바뀌었을 수 있으므로 안전하게 처리
                field_info = ai_parsed_result.missingFields[0]
                # Pydantic 모델 or Dict 처리
                if isinstance(field_info, dict):
                    assistant_msg = field_info.get('question', "정보가 부족합니다.")
                else: 
                    assistant_msg = getattr(field_info, 'question', "정보가 부족합니다.")
            else:
                assistant_msg = "정보가 부족합니다. 조금 더 자세히 말씀해 주세요."
        
        elif ai_parsed_result.intent == "IMAGE_ANALYSIS":
            # 이미지 분석 요청 처리
            preserved = ai_parsed_result.preserved_info or {}
            image_type = preserved.get("image_type", "other")
            
            if image_type == "timetable":
                assistant_msg = "시간표 이미지를 업로드해 주세요. 📸\n분석 후 강의 일정을 추가해 드릴게요!"
            elif image_type == "contest":
                assistant_msg = "공모전 포스터 이미지를 업로드해 주세요. 📸\n마감일과 준비 할 일을 함께 추천해 드릴게요!"
            else:
                assistant_msg = preserved.get("message", "이미지를 업로드해 주세요. 📸")
        
        elif ai_parsed_result.intent == "PRIORITY_QUERY":
            # 우선순위 높은 일정 조회
            test_user_id = "7822a162-788d-4f36-9366-c956a68393e1"
            high_priority_schedules = db.query(Schedule).filter(
                and_(
                    Schedule.user_id == test_user_id,
                    Schedule.end_at >= now,
                    Schedule.priority_score >= 7
                )
            ).order_by(Schedule.priority_score.desc(), Schedule.end_at.asc()).limit(5).all()
            
            if high_priority_schedules:
                result = []
                for s in high_priority_schedules:
                    date_str = s.end_at.strftime("%m/%d") if s.end_at else ""
                    priority_emoji = "🔴" if s.priority_score >= 9 else "🟠" if s.priority_score >= 7 else "🟡"
                    result.append(f"{priority_emoji} [{s.category or '기타'}] {s.title} ({date_str})")
                
                schedule_text = "\n".join(result)
                assistant_msg = f"📌 우선순위가 높은 일정이에요!\n\n{schedule_text}\n\n가장 먼저 처리해야 할 항목들입니다."
            else:
                assistant_msg = "현재 우선순위가 높은 일정이 없어요. 🎉 여유롭게 하루를 보내세요!"
                
        elif ai_parsed_result.intent == "SCHEDULE_MUTATION":
            actions = ai_parsed_result.actions
            action_cnt = len(actions)
            if action_cnt > 0:
                op_type = actions[0].op
                target_type = getattr(actions[0], 'target', 'SCHEDULE')

                if target_type == "NOTIFICATION":
                    assistant_msg = "🔔 알림 설정을 변경할까요?"
                elif op_type == "DELETE":
                    assistant_msg = "해당 일정을 취소할까요?"
                elif op_type == "UPDATE":
                    assistant_msg = "일정을 변경할까요?"
                else: # CREATE
                    # 일정(EVENT)과 할 일(SUB_TASK) 분류
                    event_count = sum(1 for a in actions if a.target == "SCHEDULE" and "[준비]" not in a.payload.get('title', ''))
                    sub_task_count = sum(1 for a in actions if a.target == "SUB_TASK" or "[준비]" in a.payload.get('title', ''))
                    
                    msg_parts = []
                    if event_count > 0:
                        msg_parts.append(f"📅 일정 {event_count}건")
                    if sub_task_count > 0:
                        msg_parts.append(f"✅ 할 일 {sub_task_count}건")
                    
                    if msg_parts:
                        assistant_msg = f"{', '.join(msg_parts)}을 등록할까요?"
                    else:
                        assistant_msg = f"{action_cnt}건을 등록할까요?"
            else:
                assistant_msg = "처리할 일정이 없습니다."
        
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