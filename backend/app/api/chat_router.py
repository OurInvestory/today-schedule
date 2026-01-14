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
    for idx, s in enumerate(schedules, 1):
        date_str = s.end_at.strftime("%m/%d") if s.end_at else ""
        time_str = s.end_at.strftime("%H:%M") if s.end_at else ""
        category = s.category or "기타"
        priority = "🔴" if (s.priority_score or 0) >= 8 else "🟡" if (s.priority_score or 0) >= 5 else "🟢"
        result.append(f"{idx}. {priority} **{s.title}**\n   📁 {category} | 📅 {date_str} {time_str}")
    
    return "\n\n".join(result)

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

        system_prompt = f"""You are a Korean schedule assistant AI. Output ONLY valid JSON.

[Today]: {current_date_str}
[Timezone]: {req.timezone}
{context_section}

####################
# INTENT DETECTION #
####################

CRITICAL RULE: Determine intent by analyzing the ENTIRE sentence context!

STEP 1 - Check if it's a QUERY first (asking about existing schedules):
  ★ "일정 알려줘", "할 일 알려줘", "일정 보여줘", "뭐 있어", "뭐야" → intent="SCHEDULE_QUERY"
  ★ These are INFORMATION REQUESTS, NOT mutations!

STEP 2 - Check for MUTATION keywords (creating/modifying schedules):
  ★ 추가, 등록, 잡아, 만들어 → intent="SCHEDULE_MUTATION", op="CREATE"
  ★ 미뤄, 옮겨, 바꿔, 변경, 연기 → intent="SCHEDULE_MUTATION", op="UPDATE"  
  ★ 취소, 삭제, 제거 → intent="SCHEDULE_MUTATION", op="DELETE"

STEP 3 - Check for NOTIFICATION requests (with specific time):
  ★ "N시간/분 전에 알림", "알림줘", "리마인드" → intent="NOTIFICATION_REQUEST"

####################
# CRITICAL EXAMPLES#
####################

★ QUERY examples (NO action keywords, just asking):
Input: "오늘 일정 알려줘"
Output: {{"intent":"SCHEDULE_QUERY","preserved_info":{{"query_range":"today"}}}}

Input: "이번 주 할 일 뭐야"
Output: {{"intent":"SCHEDULE_QUERY","preserved_info":{{"query_range":"this_week"}}}}

Input: "내일 뭐 있어?"
Output: {{"intent":"SCHEDULE_QUERY","preserved_info":{{"query_range":"tomorrow"}}}}

★ "추가" found → MUST be CREATE:
Input: "내일 3시 회의 추가해줘"
Output: {{"intent":"SCHEDULE_MUTATION","actions":[{{"op":"CREATE","payload":{{"title":"회의","start_at":"...","end_at":"...","importance_score":5,"estimated_minute":60,"category":"기타"}}}}]}}

★ "미뤄줘" found → MUST be UPDATE:
Input: "캡스톤 회의 다음주로 미뤄줘"  
Output: {{"intent":"SCHEDULE_MUTATION","actions":[{{"op":"UPDATE","payload":{{"title":"캡스톤 회의","end_at":"..."}}}}]}}

★ "취소" found → MUST be DELETE:
Input: "알고리즘 시험 취소해"
Output: {{"intent":"SCHEDULE_MUTATION","actions":[{{"op":"DELETE","payload":{{"title":"알고리즘 시험"}}}}]}}

★ NOTIFICATION_REQUEST (with specific time + 알림/리마인드):
Input: "자료구조 시험 1시간 전에 알림줘"
Output: {{"intent":"NOTIFICATION_REQUEST","preserved_info":{{"target_title":"자료구조 시험","minutes_before":60}}}}

Input: "내일 오전 9시에 회의 리마인드 해줘"
Output: {{"intent":"NOTIFICATION_REQUEST","preserved_info":{{"target_title":"회의","reminder_time":"2024-05-21T09:00:00+09:00"}}}}

####################
# KEYWORD TABLE    #
####################

| User Input | Keyword | Intent | op |
|------------|---------|--------|-----|
| "회의 추가해줘" | 추가 | SCHEDULE_MUTATION | CREATE |
| "회의 미뤄줘" | 미뤄 | SCHEDULE_MUTATION | UPDATE |
| "회의 취소해" | 취소 | SCHEDULE_MUTATION | DELETE |
| "일정 보여줘" | 보여줘 | SCHEDULE_QUERY | - |
| "알고리즘 시험 취소해" | "취소" (DELETE) | SCHEDULE_MUTATION |
| "오늘 할 일 보여줘" | "보여줘" (QUERY only) | SCHEDULE_QUERY |
| "이번 주 일정 알려줘" | "알려줘" (QUERY only) | SCHEDULE_QUERY |

####################
# OPERATION RULES  #
####################

For SCHEDULE_MUTATION, set "op":
- "CREATE": 추가, 등록, 넣어, 잡아, 만들어
- "UPDATE": 미뤄, 옮겨, 바꿔, 변경, 수정, 연기  
- "DELETE": 취소, 삭제, 제거, 빼

For SCHEDULE_QUERY, set "preserved_info.query_range":
- "today": 오늘
- "tomorrow": 내일
- "this_week": 이번 주
- "next_week": 다음 주

####################
# PAYLOAD FIELDS   #
####################

CREATE payload requires:
- title (string): Event name
- start_at (ISO8601): When the event starts. Calculate from [Today] + relative date/time.
- end_at (ISO8601): When the event ends. If duration not specified, default to start_at + 1 hour.
- importance_score (1-10): 10=시험, 7-9=과제, 4-6=회의, 1-3=개인
- estimated_minute (int): 60-180 for meetings, 120+ for exams
- category: One of [수업, 과제, 시험, 공모전, 대외활동, 기타]

IMPORTANT: Always include BOTH start_at and end_at for CREATE operations!

DELETE payload requires:
- title (string): Target schedule name

####################
# CLARIFY INTENT   #
####################

When the user wants to CREATE a schedule but required info is missing, use CLARIFY:
- If title is missing: Ask "일정 제목이 뭔가요?"
- If time is missing: Ask "몇 시에 예정된 일정인가요?"
- If date is missing: Ask "언제 예정된 일정인가요?"

CLARIFY Example:
Input: "일정 추가해줘"
{{"intent": "CLARIFY", "missing_fields": [{{"field": "title", "question": "어떤 일정을 추가할까요? 일정 이름을 알려주세요! 📝"}}]}}

Input: "회의 추가해줘"
{{"intent": "CLARIFY", "missing_fields": [{{"field": "end_at", "question": "회의가 언제인가요? 날짜와 시간을 알려주세요! ⏰"}}]}}

Input: "내일 회의"
{{"intent": "CLARIFY", "missing_fields": [{{"field": "end_at", "question": "회의가 몇 시에 시작하나요? ⏰"}}]}}

####################
# JSON EXAMPLES    #
####################

Example 1 - QUERY (keyword: "보여줘"):
Input: "오늘 할 일 보여줘"
{{"intent": "SCHEDULE_QUERY", "type": "TASK", "actions": [], "preserved_info": {{"query_range": "today"}}}}

Example 2 - CREATE (keyword: "추가"):
Input: "내일 오후 3시 회의 추가해줘"
{{"intent": "SCHEDULE_MUTATION", "type": "EVENT", "actions": [{{"op": "CREATE", "payload": {{"title": "회의", "start_at": "2024-05-21T15:00:00+09:00", "end_at": "2024-05-21T16:00:00+09:00", "importance_score": 5, "estimated_minute": 60, "category": "기타"}}}}]}}

Example 3 - UPDATE (keyword: "미뤄"):
Input: "캡스톤 회의 다음주로 미뤄줘"
{{"intent": "SCHEDULE_MUTATION", "type": "EVENT", "actions": [{{"op": "UPDATE", "payload": {{"title": "캡스톤 회의", "end_at": "2024-05-28T10:00:00+09:00"}}}}]}}

Example 4 - DELETE (keyword: "취소"):
Input: "알고리즘 시험 취소해"
{{"intent": "SCHEDULE_MUTATION", "type": "EVENT", "actions": [{{"op": "DELETE", "payload": {{"title": "알고리즘 시험"}}}}]}}

Now analyze this input and output ONLY the JSON:
User Input: {req.text}
"""
        
        generated_response = model.generate_text(prompt=system_prompt)

        clean_json_str = extract_json_from_text(generated_response)
        parsed_data = json.loads(clean_json_str)
        ai_parsed_result = AIChatParsed(**parsed_data)
        
        # 메시지 생성 로직
        assistant_msg = "일정을 확인했습니다."
        
        if ai_parsed_result.intent == "SCHEDULE_QUERY":
            # 일정 조회 처리
            query_range = ai_parsed_result.preserved_info.get("query_range", "today")
            filter_type = ai_parsed_result.preserved_info.get("filter", None)
            
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
                # 이번 주 월요일 ~ 일요일
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
            
            # 필터 적용 (우선순위 높은 일정)
            if filter_type == "high_priority":
                schedules = [s for s in schedules if s.importance_score and s.importance_score >= 7]
            
            if schedules:
                schedule_text = format_schedules_for_display(schedules)
                assistant_msg = f"{period_text} 일정이에요! 📅\n\n{schedule_text}\n\n총 {len(schedules)}건의 일정이 있어요."
            else:
                assistant_msg = f"{period_text}은 등록된 일정이 없어요. 🎉 여유로운 하루 보내세요!"
        
        elif ai_parsed_result.intent == "CLARIFY":
            if ai_parsed_result.missingFields:
                field_info = ai_parsed_result.missingFields[0]
                if isinstance(field_info, dict):
                    assistant_msg = field_info.get('question', "정보가 부족해요. 조금 더 자세히 알려주세요!")
                else: 
                    assistant_msg = getattr(field_info, 'question', "정보가 부족해요. 조금 더 자세히 알려주세요!")
            else:
                assistant_msg = "정보가 부족해요. 조금 더 자세히 말씀해 주시겠어요? 😊"
                
        elif ai_parsed_result.intent == "SCHEDULE_MUTATION":
            actions = ai_parsed_result.actions
            action_cnt = len(actions)
            if action_cnt > 0:
                op_type = actions[0].op
                first_title = actions[0].payload.get('title', '일정')
                
                if op_type == "DELETE":
                    assistant_msg = f"'{first_title}' 일정을 취소할까요? 🗑️"
                elif op_type == "UPDATE":
                    assistant_msg = f"'{first_title}' 일정을 변경할까요? ✏️"
                else: # CREATE
                    sub_task_count = sum(1 for a in actions if "[준비]" in a.payload.get('title', ''))
                    main_task_count = action_cnt - sub_task_count
                    
                    if sub_task_count > 0:
                        assistant_msg = f"'{first_title}' 일정과 준비 과정 {sub_task_count}건을 함께 등록할까요? 📝"
                    else:
                        assistant_msg = f"'{first_title}' 일정을 등록할까요? 📝"
            else:
                assistant_msg = "처리할 일정이 없어요."
        
        elif ai_parsed_result.intent == "NOTIFICATION_REQUEST":
            # 알림 예약 처리
            preserved = ai_parsed_result.preserved_info
            target_title = preserved.get('target_title', '일정')
            minutes_before = preserved.get('minutes_before')
            reminder_time = preserved.get('reminder_time')
            
            if minutes_before:
                assistant_msg = f"'{target_title}' {minutes_before}분 전에 알림을 예약할까요? 🔔"
            elif reminder_time:
                try:
                    rt = datetime.fromisoformat(reminder_time.replace('Z', '+00:00'))
                    time_str = rt.strftime('%m월 %d일 %H:%M')
                    assistant_msg = f"'{target_title}' 알림을 {time_str}에 예약할까요? 🔔"
                except:
                    assistant_msg = f"'{target_title}' 알림을 예약할까요? 🔔"
            else:
                assistant_msg = f"'{target_title}' 알림을 예약할까요? 🔔"

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