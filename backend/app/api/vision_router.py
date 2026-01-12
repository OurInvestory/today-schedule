import io
import os
import json
import re
import warnings
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

warnings.filterwarnings("ignore", message=".*pin_memory.*")

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
    """텍스트에서 정교하게 JSON만 추출합니다."""
    try:
        text = text.split("User Input:")[0]
        
        text = re.sub(r"```(?:json)?\s*", "", text)
        text = re.sub(r"```", "", text)
        
        start_index = text.find('{')
        end_index = text.rfind('}')
        
        if start_index != -1 and end_index != -1:
            return text[start_index : end_index + 1]
        
        return text.strip()
    except Exception:
        return text.strip()

@router.post("/analyze", response_model=APIResponse, response_model_exclude_none=True)
async def analyze_image_schedule(
    file: UploadFile = File(...),
    timezone: str = "Asia/Seoul"
):
    try:
        image_bytes = await file.read()
        result_text_list = await run_in_threadpool(ocr_reader.readtext, image_bytes, detail=0)
        raw_ocr_text = "\n".join(result_text_list)

        if not raw_ocr_text.strip():
            return APIResponse(status=400, message="이미지에서 텍스트를 인식하지 못했습니다.")

        model = get_watson_model()
        current_date_str = datetime.now().strftime("%Y-%m-%d (%A)")

        # 프롬프트를 명령 중심으로 대폭 압축하여 루핑 방지
        vision_system_prompt = f"""Extract schedule data from OCR text into a single JSON object.
       
Today: {current_date_str}, Timezone: {timezone}

[Rules]
1. Classification:
   - If weekdays(월,화...) appear: It's a "Weekly Timetable" -> payload.type="EVENT", category="수업", importance=5, duration=60-120.
   - If specific dates(YYYY.MM.DD) appear: It's an "Event Poster" -> Extract "Application Deadline"(TASK, importance=9) and "Main Event"(EVENT, importance=8).
2. Data: Calculate dates relative to Today. Populate importance_score(1-10) and estimated_minute(int).
3. Exclusion: Ignore administrative info like "심사", "발표", "문의".
4. The 'type' field at the top level of the JSON MUST ALWAYS be "UNKNOWN".

[OCR Text]
{raw_ocr_text}

[Output Format]
{{
  "intent": "SCHEDULE_MUTATION",
  "type": "UNKNOWN",
  "actions": [
    {{
      "op": "CREATE",
      "payload": {{
        "type": "EVENT" or "TASK",
        "category": "수업"|"과제"|"시험"|"공모전"|"대외활동"|"기타",
        "title": "...",
        "start_at": "ISO8601",
        "end_at": "ISO8601",
        "importance_score": 1-10,
        "estimated_minute": 0
      }}
    }}
  ]
}}

JSON Output:"""

        # model.generate_text 호출 시 prompt 전달
        generated_response = model.generate_text(prompt=vision_system_prompt)
        
        # JSON 추출 시 시작 중괄호를 강제로 찾음
        clean_json_str = extract_json_from_text(generated_response)
        
        try:
            parsed_data = json.loads(clean_json_str)
            # 노이즈 필터링 (심사 등 제외)
            exclude_keywords = ["심사", "발표", "선발", "문의"]
            if "actions" in parsed_data:
                parsed_data["actions"] = [
                    a for a in parsed_data["actions"] 
                    if not any(k in a["payload"].get("title", "") for k in exclude_keywords)
                ]
            
            ai_parsed_result = AIChatParsed(**parsed_data)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Parsing Failed. Response: {generated_response}")
            return APIResponse(status=500, message="AI가 올바른 형식의 응답을 생성하지 못했습니다. (Looping/Format Error)")

        action_cnt = len(ai_parsed_result.actions) if ai_parsed_result.actions else 0
        assistant_msg = f"이미지에서 {action_cnt}건의 일정을 발견했습니다. 등록할까요?"

        return APIResponse(status=200, message="Success", data=ChatResponseData(
            parsed_result=ai_parsed_result,
            assistant_message=assistant_msg
        ))

    except Exception as e:
        print(f"Error: {str(e)}")
        return APIResponse(status=500, message=f"Server Error: {str(e)}")