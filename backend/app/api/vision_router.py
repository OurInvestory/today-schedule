import io
import os
import json
import re
from datetime import datetime
import easyocr

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.concurrency import run_in_threadpool 
from dotenv import load_dotenv

# IBM Watsonx SDK
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
from ibm_watsonx_ai.foundation_models.utils.enums import DecodingMethods

# 스키마 Import
from app.schemas.ai_chat import (
    APIResponse, 
    ChatResponseData, 
    AIChatParsed
)

load_dotenv()

router = APIRouter()

# --- [OCR Reader 초기화] ---
ocr_reader = easyocr.Reader(['ko', 'en'], gpu=False) 

# --- [Watsonx 설정] ---
WATSONX_API_KEY = os.getenv("WATSONX_API_KEY")
WATSONX_URL = os.getenv("WATSONX_URL")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID")
WATSONX_MODEL_ID = os.getenv("WATSONX_MODEL_ID", "meta-llama/llama-3-3-70b-instruct")

credentials = {
    "url": WATSONX_URL,
    "apikey": WATSONX_API_KEY
}

generate_params = {
    GenParams.DECODING_METHOD: DecodingMethods.GREEDY,
    GenParams.MAX_NEW_TOKENS: 1000, 
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
    """텍스트에서 첫 번째 JSON 객체만 정확하게 추출합니다."""
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

@router.post("/analyze", response_model=APIResponse, response_model_exclude_none=True)
async def analyze_image_schedule(
    file: UploadFile = File(...),
    timezone: str = "Asia/Seoul"
):
    try:
        # 1. OCR 처리 (비동기)
        image_bytes = await file.read()
        result_text_list = await run_in_threadpool(
            ocr_reader.readtext, 
            image_bytes, 
            detail=0
        )
        raw_ocr_text = "\n".join(result_text_list)

        if not raw_ocr_text.strip():
            return APIResponse(status=400, message="이미지에서 텍스트를 인식하지 못했습니다.")

        # 2. 모델 준비
        model = get_watson_model()
        current_date_str = datetime.now().strftime("%Y-%m-%d (%A)")

        vision_system_prompt = f"""
You are an AI assistant that converts raw OCR text into structured schedule JSON.

[Current Environment]
- Today: {current_date_str}
- Timezone: {timezone}

[Raw OCR Text]
{raw_ocr_text}

[Task]
Analyze the text to determine if it is a "Weekly Timetable" or "Event Poster".
Extract schedule actions accordingly.

---
### CASE A: Weekly Timetable (Lecture Schedule)
If the text contains repeating weekdays (Mon, Tue, Wed...) and course names:
1. Create an action for each class.
2. **Date Calculation**: Calculate the *next upcoming date* for that weekday relative to 'Today'. (e.g., If Today is Friday and the class is Mon, find next Monday's date).
3. **Payload Rule**: Set `"type": "EVENT"`.
4. Title: Course Name.

---
### CASE B: Event Poster (Recruitment/Contest)
Separate the "Application Period" from the "Main Event".

1. **Application Start (접수 시작)** -> **TASK**
   - Condition: "접수 시작", "Start Date".
   - **Payload Rule**: Set `"type": "TASK"`.
   - Title: "[접수 시작] {{Title}}"
   - `end_at`: Application START date. (Tasks only use end_at)

2. **Application Deadline (접수 마감)** -> **TASK**
   - Condition: "마감", "Deadline", "End Date".
   - **Payload Rule**: Set `"type": "TASK"`.
   - Title: "[접수 마감] {{Title}}"
   - `end_at`: Application END date.

3. **Main Event (행사/OT)** -> **EVENT**
   - Condition: "일시", "Event Date".
   - **Payload Rule**: Set `"type": "EVENT"`.
   - Title: "[행사] {{Title}}"
   - `start_at` & `end_at`: Event date.

[Examples]
**(Example 1: Timetable)**
Input: "월요일 10:00 자료구조, 수요일 13:00 운영체제" (Today is 2024-05-20 Mon)
Output:
{{
  "intent": "SCHEDULE_MUTATION",
  "type": "UNKNOWN",
  "actions": [
    {{ "op": "CREATE", "payload": {{ "type": "EVENT", "title": "자료구조", "start_at": "2024-05-20T10:00:00+09:00", "end_at": "2024-05-20T12:00:00+09:00" ,"description": "Extracted memo or location"}} }},
    {{ "op": "CREATE", "payload": {{ "type": "EVENT", "title": "운영체제", "start_at": "2024-05-22T13:00:00+09:00", "end_at": "2024-05-22T15:00:00+09:00" ,"description": "Extracted memo or location"}} }}
  ]
}}

**(Example 2: Contest Poster)**
Input: "제1회 AI 공모전 / 접수: 2024.12.01 ~ 12.31 / 시상식: 2025.01.15"
Output:
{{
  "intent": "SCHEDULE_MUTATION",
  "type": "UNKNOWN",
  "actions": [
    {{ "op": "CREATE", "payload": {{ "type": "TASK", "title": "[접수 시작] AI 공모전", "end_at": "2024-12-01T09:00:00+09:00" }} }},
    {{ "op": "CREATE", "payload": {{ "type": "TASK", "title": "[접수 마감] AI 공모전", "end_at": "2024-12-31T23:59:00+09:00" }} }},
    {{ "op": "CREATE", "payload": {{ "type": "EVENT", "title": "[행사] 시상식", "start_at": "2025-01-15T14:00:00+09:00", "end_at": "2025-01-15T16:00:00+09:00" }} }}
  ]
}}

[Output Format]
Output ONLY valid JSON.
**IMPORTANT**: 
1. The top-level `type` MUST be **"UNKNOWN"** (to indicate mixed content).
2. Inside `actions` -> `payload`, you MUST include the specific `"type"` ("TASK" or "EVENT").

{{
  "intent": "SCHEDULE_MUTATION",
  "type": "UNKNOWN", 
  "actions": [
    {{
      "op": "CREATE",
      "payload": {{
        "type": "TASK", 
        "title": "[접수 마감] 공모전 이름",
        "end_at": "YYYY-MM-DDTHH:MM:SS+09:00",
        "description": "Details..."
      }}
    }},
    {{
      "op": "CREATE",
      "payload": {{
        "type": "EVENT",
        "title": "[행사] 시상식",
        "start_at": "YYYY-MM-DDTHH:MM:SS+09:00",
        "end_at": "YYYY-MM-DDTHH:MM:SS+09:00",
        "description": "Location..."
      }}
    }}
  ]
}}
"""

        # 4. LLM 생성 및 파싱
        generated_response = model.generate_text(prompt=vision_system_prompt)
        clean_json_str = extract_json_from_text(generated_response)
        parsed_data = json.loads(clean_json_str)
        
        # Pydantic 모델로 변환 (AIChatParsed의 type="UNKNOWN" 허용 필수)
        ai_parsed_result = AIChatParsed(**parsed_data)

        # 5. 응답 메시지 생성
        action_cnt = len(ai_parsed_result.actions) if ai_parsed_result.actions else 0
        assistant_msg = f"이미지에서 {action_cnt}건의 일정을 발견했습니다. 등록할까요?"

        response_data = ChatResponseData(
            parsed_result=ai_parsed_result,
            assistant_message=assistant_msg
        )

        return APIResponse(status=200, message="Success", data=response_data)

    except json.JSONDecodeError:
        print(f"Failed JSON Parsing: {generated_response}")
        return APIResponse(status=500, message="AI 분석 결과가 올바른 형식이 아닙니다.")
    except Exception as e:
        print(f"Error in Vision Router: {str(e)}")
        return APIResponse(status=500, message=f"Server Error: {str(e)}")