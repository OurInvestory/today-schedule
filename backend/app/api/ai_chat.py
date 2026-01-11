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

router = APIRouter(
    prefix="/ai/chat",
    tags=["AI Chat"]
)

# --- Watsonx 설정 ---
WATSONX_API_KEY = os.getenv("WATSONX_API_KEY")
WATSONX_URL = os.getenv("WATSONX_URL")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID")
WATSONX_MODEL_ID = os.getenv("WATSONX_MODEL_ID", "ibm/granite-3-8b-instruct")

credentials = {
    "url": WATSONX_URL,
    "apikey": WATSONX_API_KEY
}

# [수정 1] 생성 파라미터에 'STOP_SEQUENCES' 추가 
# AI가 "User Input:"이라는 글자를 쓰려고 하면 즉시 멈추게 합니다.
generate_params = {
    GenParams.DECODING_METHOD: DecodingMethods.GREEDY,
    GenParams.MAX_NEW_TOKENS: 500,  
    GenParams.MIN_NEW_TOKENS: 1,
    GenParams.TEMPERATURE: 0,
    GenParams.STOP_SEQUENCES: ["User Input:", "User:", "\n\n\n"] 
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

@router.post("", response_model=APIResponse)
async def chat_with_ai(req: ChatRequest):
    try:
        model = get_watson_model()
        current_date_str = req.base_date or datetime.now().strftime("%Y-%m-%d")
        
        # 프롬프트 보강: CLARIFY 규칙 추가
        system_prompt = f"""You are a smart academic scheduler AI.
Analyze the user's input and output valid JSON only.

[Current Context]
- Today: {current_date_str}
- Timezone: {req.timezone}

[Rules]
1. Intent Classification:
   - "SCHEDULE_MUTATION": When the request is clear (has Subject + Time).
   - "CLARIFY": If the subject is vague (e.g., just "Exam", "Meeting", "Assignment") OR the time is missing.
   
2. Type determination:
   - "EVENT": Meetings, Classes. Must have start_at.
   - "TASK": Deadlines, Exams. Must have end_at.

3. Actions:
   - For "CLARIFY": Leave 'actions' empty. Fill 'missingFields' with the question.
   - For "SCHEDULE_MUTATION": Fill 'actions'.

[Examples]
User: "내일 오후 2시에 시험 있어"
JSON: {{
  "intent": "CLARIFY",
  "type": "UNKNOWN",
  "missingFields": [ {{ "field": "title", "question": "어떤 과목 시험인가요?", "reason": "Subject is missing" }} ]
}}

User: "내일 오후 2시에 자료구조 시험 있어"
JSON: {{
  "intent": "SCHEDULE_MUTATION",
  "type": "TASK",
  "actions": [ {{ "op": "CREATE", "payload": {{ "title": "자료구조 시험", "end_at": "2026-01-13T14:00:00+09:00" }} }} ]
}}

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
            # AI가 질문을 만들어서 보내줌
            if ai_parsed_result.missingFields:
                assistant_msg = ai_parsed_result.missingFields[0].question
            else:
                assistant_msg = "정보가 부족합니다. 조금 더 자세히 말씀해 주세요."
                
        elif ai_parsed_result.intent == "SCHEDULE_MUTATION":
            action_cnt = len(ai_parsed_result.actions)
            assistant_msg = f"{action_cnt}건의 일정을 정리했습니다. 등록할까요?"

        response_data = ChatResponseData(
            parsed_result=ai_parsed_result,
            assistant_message=assistant_msg
        )

        return APIResponse(status=200, message="Success", data=response_data)

    except json.JSONDecodeError:
        return APIResponse(status=500, message="AI 응답을 분석하는 데 실패했습니다.")
    except Exception as e:
        print(f"Error: {str(e)}")
        return APIResponse(status=500, message=f"Server Error: {str(e)}")