import os
import json
import logging
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException
from dotenv import load_dotenv

# Google Gemini SDK
import google.generativeai as genai

# 기존 스키마 재사용 (Frontend 호환성 유지)
from app.schemas.ai_chat import APIResponse, ChatResponseData, AIChatParsed

load_dotenv()
router = APIRouter()
logger = logging.getLogger(__name__)

# --- [설정] Google Gemini ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")

if not GOOGLE_API_KEY:
    logger.error("GOOGLE_API_KEY is missing in environment variables.")

genai.configure(api_key=GOOGLE_API_KEY)

# JSON 응답을 강제하기 위한 모델 설정
model = genai.GenerativeModel(
    model_name=GEMINI_MODEL_NAME,
    generation_config={
        "temperature": 0.1,
        "response_mime_type": "application/json"
    }
)

async def analyze_image_with_gemini(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    """
    이미지를 Gemini에게 전송하여 시간표(Schedule) 또는 포스터(Poster) 정보를 추출
    """
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    # 통합 프롬프트: 분류와 추출을 한 번에 수행
    prompt = f"""
    You are an AI Assistant capable of analyzing university timetables and event posters.
    Current Date: {today_str}

    [TASK]
    1. **Classify**: Determine if the image is a 'schedule' (University Timetable) or a 'poster' (Event/Contest/Recruitment).
    2. **Extract**: Based on the classification, extract structured data.

    [CASE 1: SCHEDULE (Timetable)]
    - Extract each class as an object.
    - Merge consecutive slots for the same class on the same day.
    - Day: 0(Mon), 1(Tue), 2(Wed), 3(Thu), 4(Fri), 5(Sat), 6(Sun).
    - Time: 24-hour format (HH:MM).
    - Ignore pure room numbers in titles, put them in location (e.g., '상허관', '공학관').

    [CASE 2: POSTER (Event/Contest)]
    - Extract the main Deadline or Event Date.
    - If it's a 'Context/Competition' (공모전), generate 3~4 preparation 'sub-tasks' (e.g., D-7 Research, D-3 Draft).
    - Importance Score: 1~10.

    [OUTPUT JSON FORMAT]
    {{
      "image_type": "schedule" | "poster",
      "lectures": [  // If schedule
        {{
          "title": "Course Name",
          "start_time": "HH:MM",
          "end_time": "HH:MM",
          "week": 0, // Integer (0=Mon)
          "location": "Room info"
        }}
      ],
      "actions": [ // If poster (Compatible with your existing AIChatParsed schema)
        {{
          "op": "CREATE",
          "payload": {{
             "title": "Event Title",
             "end_at": "YYYY-MM-DDTHH:MM:SS",
             "category": "공모전" | "대외활동" | "기타",
             "importance_score": 8,
             "estimated_minute": 60
          }}
        }}
      ]
    }}
    """

    try:
        response = model.generate_content([
            {"mime_type": mime_type, "data": image_bytes},
            prompt
        ])
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"Gemini Analysis Error: {e}")
        raise HTTPException(status_code=500, detail="AI Analysis Failed")


@router.post("/analyze", response_model=APIResponse)
async def analyze_image_schedule(file: UploadFile = File(...)):
    """
    이미지 업로드 -> Gemini 분석 -> 결과 반환
    """
    try:
        # 1. 파일 읽기
        contents = await file.read()
        mime_type = file.content_type or "image/jpeg"

        # 2. Gemini 호출 (OCR + LLM 통합)
        result_json = await analyze_image_with_gemini(contents, mime_type)
        
        image_type = result_json.get("image_type", "unknown")
        lectures_data = result_json.get("lectures", [])
        actions_data = result_json.get("actions", [])

        # 3. 응답 메시지 및 데이터 구성
        ai_parsed_result = AIChatParsed(
            intent="SCHEDULE_MUTATION",
            type="TASK" if image_type == 'poster' else "UNKNOWN",
            actions=actions_data
        )

        # Assistant Message 생성
        assistant_msg = ""
        if image_type == 'schedule':
            count = len(lectures_data)
            assistant_msg = f"[SCHEDULE] 분석 완료: {count}건의 강의를 시간표에서 발견했습니다."
            # 스케줄 모드일 때는 actions를 비워둡니다 (기존 로직 유지)
            ai_parsed_result.actions = [] 
            
        elif image_type == 'poster':
            main_tasks = [a for a in actions_data if "[준비]" not in a.get('payload', {}).get('title', '')]
            sub_tasks = [a for a in actions_data if "[준비]" in a.get('payload', {}).get('title', '')]
            assistant_msg = f"[POSTER] 분석 완료: 주요 일정 {len(main_tasks)}건"
            if sub_tasks:
                assistant_msg += f"과 준비 단계 {len(sub_tasks)}건을 제안합니다."
        else:
            assistant_msg = "이미지에서 일정 정보를 찾을 수 없습니다."

        # 4. 최종 반환
        return APIResponse(
            status=200, 
            message="Success", 
            data=ChatResponseData(
                parsed_result=ai_parsed_result,
                assistant_message=assistant_msg,
                lectures=lectures_data if image_type == 'schedule' else []
            )
        )

    except Exception as e:
        logger.error(f"Server Error: {str(e)}")
        return APIResponse(status=500, message=f"Server Error: {str(e)}")