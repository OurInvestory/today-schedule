import os
import json
import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
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

@router.post("/chat", response_model=APIResponse , response_model_exclude_none=True)
async def chat_with_ai(req: ChatRequest):
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
   - "SCHEDULE_MUTATION": When the user wants to Create, Update, or Delete a schedule.
   - "CLARIFY": If essential info (Subject/Time) is missing for CREATE, or if the target is unclear.

2. Determine 'op' (Operation):
   - "CREATE": Default. (e.g., "Add", "Schedule", "New")
   - "UPDATE": When user wants to change time, title, or details. (e.g., "Delay", "Move", "Change", "Reschedule")
   - "DELETE": When user wants to remove. (e.g., "Cancel", "Delete", "Remove")

3. Payload Construction (Mandatory for CREATE/UPDATE):
   - "importance_score" (int, 1-10): 
      * 10: Final exams, major certification tests.
      * 7-9: Midterms, major assignments, critical team projects.
      * 4-6: Quizzes, regular assignments, meetings.
      * 1-3: Personal tasks, hobbies, routine activities.
   - "estimated_minute" (int): Estimated total workload (e.g., Exam Study: 600-1200, Homework: 60-180, Meetings: 60).
   - "category" (string): Must be one of [수업, 과제, 시험, 공모전, 대외활동, 기타].
   - "CREATE": Must include 'title', 'importance_score', 'estimated_minute', 'category' AND ('start_at' OR 'end_at').
   - "UPDATE": Must include 'title' (to identify target) AND specific fields to change.
   - "DELETE": Must include 'title'.
   
4. Output Format:
   - "CLARIFY": Save partial info to 'preserved_info'. Fill 'missingFields'.
   - "SCHEDULE_MUTATION": Fill 'actions' list.

5. Date Calculation:
   - Always calculate relative dates (e.g., "tomorrow", "next Friday") into exact ISO8601 timestamps based on [Current Environment] date.

6. Sub-task Auto-Generation (SMART FEATURE):
   - IF the intent is "CREATE" AND Category is one of ['시험', '과제', '공모전', '대외활동']:
   - YOU MUST generate 3 to 5 'Sub-tasks' (Preparation steps) leading up to the deadline.
   - Sub-task Payload:
     * title: "[준비] {{Original Title}} - {{Step Description}}"
     * end_at: D-1, D-2, D-3... days before the main event.
     * estimated_minute: 60-180 (reasonable study time).
     * category: Same as parent or '공부'.
     * tip: "Short, practical advice for this step (Korean, Max 20 chars)"

[Examples]
---
# Note: In these examples, the Reference Date is fixed to 2024-05-20 (Monday).
# The model must calculate the target date based on the user's input relative to the [Current Environment] date provided in the real prompt.

# Example 1: Create w/ Sub-tasks (Exam)
User: "다음주 월요일 알고리즘 시험 일정 추가해줘"
Context: Reference Date is 2024-05-20 (Mon). "Next Mon" is 2024-05-27.
JSON: {{
  "intent": "SCHEDULE_MUTATION",
  "type": "TASK",
  "actions": [
    {{ "op": "CREATE", "payload": {{ "title": "알고리즘 시험", "end_at": "2024-05-27T10:00:00+09:00", "importance_score": 10, "estimated_minute": 120, "category": "시험"}} }},
    {{ "op": "CREATE", "payload": {{ "title": "[준비] 알고리즘 시험 - 개념 정리", "end_at": "2024-05-24T23:59:00+09:00", "importance_score": 8, "estimated_minute": 120, "category": "시험", "tip": "핵심 개념 위주로 1회독"}} }},
    {{ "op": "CREATE", "payload": {{ "title": "[준비] 알고리즘 시험 - 기출 풀이", "end_at": "2024-05-25T23:59:00+09:00", "importance_score": 8, "estimated_minute": 180, "category": "시험", "tip": "타이머 켜고 실전처럼 풀기"}} }},
    {{ "op": "CREATE", "payload": {{ "title": "[준비] 알고리즘 시험 - 최종 복습", "end_at": "2024-05-26T23:59:00+09:00", "importance_score": 9, "estimated_minute": 120, "category": "시험", "tip": "틀린 문제 위주로 재점검"}} }}
  ]
}}

# Example 2: Update (Change Time) - Relative Date Calculation
User: "운영체제 과제 마감 하루 미뤄줘"
Context: Reference Date is 2024-05-20 (Monday)
JSON: {{
  "intent": "SCHEDULE_MUTATION",
  "type": "TASK",
  "actions": [ {{ 
    "op": "UPDATE", 
    "payload": {{ "title": "운영체제 과제", "end_at": "2026-05-21T23:59:00+09:00" }} 
  }} ]
}}

# Example 3: Delete (Cancel) - No Date Calculation needed
User: "캡스톤 회의 취소해"
Context: Reference Date is 2026-05-20 (Monday)
JSON: {{
  "intent": "SCHEDULE_MUTATION",
  "type": "EVENT",
  "actions": [ {{ "op": "DELETE", "payload": {{ "title": "캡스톤 회의" }} }} ]
}}

# Example 4: Context Merging (Create Task) - Merging preserved info
User: "자료구조"
Context: {{ 
  "intent": "CLARIFY", 
  "missingFields": ["title"], 
  "preserved_info": {{ "end_at": "2026-05-20T14:00:00+09:00" }}, 
  "type": "TASK" 
}}
JSON: {{
  "intent": "SCHEDULE_MUTATION",
  "type": "TASK",
  "actions": [ {{ 
      "op": "CREATE", 
      "payload": {{ "title": "자료구조", "end_at": "2026-05-20T14:00:00+09:00", "importance_score": 8, "estimated_minute": 180, "category": "과제"}} 
  }} ]
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
                
        elif ai_parsed_result.intent == "SCHEDULE_MUTATION":
            actions = ai_parsed_result.actions
            action_cnt = len(actions)
            if action_cnt > 0:
                op_type = actions[0].op
                
                if op_type == "DELETE":
                    assistant_msg = "해당 일정을 취소할까요?"
                elif op_type == "UPDATE":
                    assistant_msg = "일정을 변경할까요?"
                else: # CREATE
                    # 서브태스크(준비 일정) 감지 로직
                    sub_task_count = sum(1 for a in actions if "[준비]" in a.payload.get('title', ''))
                    main_task_count = action_cnt - sub_task_count
                    
                    if sub_task_count > 0:
                        assistant_msg = f"준비 과정 {sub_task_count}건을 함께 등록할까요?"
                    else:
                        assistant_msg = f"{action_cnt}건의 일정을 등록할까요?"
            else:
                assistant_msg = "처리할 일정이 없습니다."

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