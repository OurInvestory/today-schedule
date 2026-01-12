import io
import os
import json
import re
from datetime import datetime
import easyocr

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.concurrency import run_in_threadpool # OCR 비동기 처리를 위해 필수
from dotenv import load_dotenv

# IBM Watsonx SDK (chat_router와 동일한 설정)
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
from ibm_watsonx_ai.foundation_models.utils.enums import DecodingMethods

# 스키마 Import (chat_router와 동일한 경로 사용)
from app.schemas.ai_chat import (
    APIResponse, 
    ChatResponseData, 
    AIChatParsed
)

load_dotenv()

router = APIRouter()

# --- [OCR Reader 초기화] ---
# 서버 시작 시 모델 로드 (GPU가 없으면 gpu=False)
ocr_reader = easyocr.Reader(['ko', 'en'], gpu=False) 

# --- [Watsonx 설정] (chat_router와 동일하게 구성) ---
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
    GenParams.MAX_NEW_TOKENS: 1000,  # OCR 텍스트가 길 수 있으므로 토큰 수 여유 있게
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
    텍스트에서 첫 번째 JSON 객체만 정확하게 추출합니다. (chat_router와 동일 로직)
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

@router.post("", response_model=APIResponse, response_model_exclude_none=True)
async def analyze_image_schedule(
    file: UploadFile = File(...),
    timezone: str = "Asia/Seoul"
):
    try:
        # 1. 이미지 파일 읽기 & OCR 처리 (비동기 처리)
        image_bytes = await file.read()
        
        # run_in_threadpool을 사용하여 메인 스레드 차단 방지
        result_text_list = await run_in_threadpool(
            ocr_reader.readtext, 
            image_bytes, 
            detail=0
        )
        
        raw_ocr_text = "\n".join(result_text_list)
        # print(f"--- [OCR Extracted] ---\n{raw_ocr_text}\n-----------------------")

        if not raw_ocr_text.strip():
            return APIResponse(status=400, message="이미지에서 텍스트를 인식하지 못했습니다.")

        # 2. Watsonx 모델 준비
        model = get_watson_model()
        current_date_str = datetime.now().strftime("%Y-%m-%d (%A)")

        # 3. 비전 분석 전용 시스템 프롬프트
        vision_system_prompt = f"""
You are an AI assistant that converts raw OCR text from an image into structured schedule JSON.

[Current Environment]
- Today: {current_date_str}
- Timezone: {timezone}

[Task]
Analyze the 'Raw OCR Text' (from a timetable or poster).
Extract schedule information and output valid JSON matching the schema.

[Rules]
1. Ignore noise (UI elements, random numbers).
2. For Timetables:
   - Identify Course Name, Day, Time.
   - If exact date is missing, assume it's for the upcoming week.
3. For Event Posters:
   - Extract Title, Start Time, End Time.
4. Output Schema:
   - Intent is always "SCHEDULE_MUTATION".
   - Type is usually "EVENT" or "TASK".
   - "op" is "CREATE".

[Output Format]
Output ONLY a valid JSON object. No markdown.
{{
  "intent": "SCHEDULE_MUTATION",
  "type": "EVENT", 
  "actions": [
    {{
      "op": "CREATE",
      "payload": {{
        "title": "Course or Event Title",
        "start_at": "YYYY-MM-DDTHH:MM:SS+09:00",
        "end_at": "YYYY-MM-DDTHH:MM:SS+09:00",
        "description": "Extracted memo or location"
      }}
    }}
  ]
}}

[Raw OCR Text]
{raw_ocr_text}

JSON Output:
"""

        # 4. Llama-3에게 생성 요청
        # (OCR 텍스트가 길 경우 시간이 걸릴 수 있으므로, 필요시 이것도 threadpool 고려 가능)
        generated_response = model.generate_text(prompt=vision_system_prompt)
        
        # 5. JSON 추출 및 파싱
        clean_json_str = extract_json_from_text(generated_response)
        parsed_data = json.loads(clean_json_str)
        
        # Pydantic 모델로 변환 (AIChatParsed 재사용)
        ai_parsed_result = AIChatParsed(**parsed_data)

        # 6. 응답 메시지 생성
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