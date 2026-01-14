import json
import os
import re
import warnings
from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.concurrency import run_in_threadpool
from dotenv import load_dotenv

# IBM Watsonx SDK
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

from app.schemas.ai_chat import APIResponse, ChatResponseData, AIChatParsed

warnings.filterwarnings("ignore")
load_dotenv()

router = APIRouter()

# --- [초기화] OCR Reader (Optional) ---
try:
    import easyocr
    ocr_reader = easyocr.Reader(['ko', 'en'], gpu=False)
    OCR_AVAILABLE = True
except ImportError:
    ocr_reader = None
    OCR_AVAILABLE = False
    print("Warning: easyocr not installed. Image analysis will be limited.")

# 모델 ID
WATSONX_MODEL_ID_TEXT = os.getenv("WATSONX_MODEL_ID")  # 70b-instruct (OCR 텍스트 분석용)

credentials = {
    "url": os.getenv("WATSONX_URL"),
    "apikey": os.getenv("WATSONX_API_KEY")
}
project_id = os.getenv("WATSONX_PROJECT_ID")

def detect_image_type(ocr_results) -> str:
    """이미지 타입 감지: 'schedule' 또는 'poster'"""
    texts = [text for (_, text, _) in ocr_results]
    text_combined = " ".join(texts).lower()
    text_no_space = text_combined.replace(" ", "")
    
    # 1. [강력한 신호] 포스터 키워드가 명확하면 우선반환
    # 공백 제거 버전에서도 체크 (OCR이 "공 모 전"으로 읽을 수 있음)
    strong_poster_keywords = ['공모전', '대외활동', '서포터즈', '채용', '콘테스트', 'competition', 'recruit',
                              '상금', '상장', '시상', '주최', '후원', '응모']
    if any(kw in text_combined or kw in text_no_space for kw in strong_poster_keywords):
        return 'poster'

    # 2. Schedule 점수 계산
    schedule_keywords = ['시간표', '강의실', '교시', 'timetable', 'class', 'lecture', 'professor', '학기', 'semester']
    schedule_score = sum(1 for kw in schedule_keywords if kw in text_combined)
    
    # [개선] 요일 감지 - 날짜 형식(월), (화)는 제외하고, 독립적인 요일만 카운트
    # 날짜 형식의 괄호 요일 제거 후 체크
    import re
    text_cleaned = re.sub(r'\([월화수목금토일]\)', '', text_combined)
    
    days_kor = ['월', '화', '수', '목', '금']
    days_eng = ['mon', 'tue', 'wed', 'thu', 'fri']
    
    # 독립적인 요일 발견 (공백이나 단어 경계로 구분)
    found_days = 0
    for d in days_kor:
        # 독립적으로 등장하는 요일만 (예: "월 화 수" 또는 단독 셀)
        if re.search(rf'(^|\s){d}($|\s)', text_cleaned):
            found_days += 1
    for d in days_eng:
        if re.search(rf'\b{d}\b', text_cleaned):
            found_days += 1
        
    if found_days >= 3:
        schedule_score += 5  # 강력한 가산점 부여

    # 3. Poster 점수 계산
    poster_keywords = ['모집', '신청', '행사', '마감', '문의', '지원', '기간', '활동', '봉사', '공모', '상담', '접수', '발표']
    poster_score = sum(1 for kw in poster_keywords if kw in text_combined)
    
    # 4. 점수 비교 (동점이면 Schedule 우선으로 변경 - 일반적인 텍스트 없는 문서 등은 시간표 분석 흐름이 더 관대함)
    return 'schedule' if schedule_score >= poster_score else 'poster'

def is_header_or_noise(text):
    text = text.replace(" ", "").strip()
    if text in ['월', '화', '수', '목', '금', '토', '일', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri']: return True
    if text.isdigit(): return True
    if re.match(r'^[\W_]+$', text): return True
    if text in ['shl', '기', '비고', '시간', '미기재', '상담', '교시', '과목명']: return True 

    # 강의실 번호는 유지 (D309, I311 등) - 제거하지 않음
    # if re.match(r'^[A-Z]\d{3,4}$', text): return True
    
    # 건물+강의실 조합도 유지 (예: 상허관301)
    # if re.search(r'[가-힣]+[\d]{3,4}$', text): return True
    
    building_keywords = ['상허관', '산학', '공학관', '인문관', '과학관', '예술관']
    if any(bk in text for bk in building_keywords): return True

    return False

def get_center(bbox):
    (tl, tr, br, bl) = bbox
    return (tl[0] + tr[0]) / 2, (tl[1] + bl[1]) / 2

def simple_text_dump(ocr_results):
    """포스터/공지사항용 단순 텍스트 변환 (좌상단 -> 우하단)"""
    # Y좌표(상단) 기준 정렬 후, X좌표(좌측) 기준 정렬 (대략적인 문단 순서)
    # bbox[0][1] = top-left y, bbox[0][0] = top-left x
    sorted_data = sorted(ocr_results, key=lambda r: (r[0][0][1], r[0][0][0]))
    
    texts = []
    for (bbox, text, prob) in sorted_data:
        if prob < 0.3: continue
        texts.append(text)
        
    return "\n".join(texts)

def geometric_grid_analysis(ocr_results):
    items = []
    for (bbox, text, prob) in ocr_results:
        if prob < 0.3: continue
        if is_header_or_noise(text): continue
        cx, cy = get_center(bbox)
        items.append({'text': text, 'cx': cx, 'cy': cy})

    if not items: return ""

    x_coords = [i['cx'] for i in items]
    min_x, max_x = min(x_coords), max(x_coords)
    width = max_x - min_x
    col_width = width / 5
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']

    y_coords = [i['cy'] for i in items]
    min_y, max_y = min(y_coords), max(y_coords)
    total_height = max_y - min_y
    if total_height < 50: hour_height = 50 
    else: hour_height = total_height / 10 

    schedule_buckets = defaultdict(list)
    for item in items:
        col_idx = int((item['cx'] - min_x) / col_width)
        if col_idx < 0: col_idx = 0
        if col_idx > 4: col_idx = 4
        
        delta_y = item['cy'] - min_y
        estimated_hour_offset = int(delta_y / hour_height)
        hour = 9 + estimated_hour_offset
        
        clean_txt = item['text'].replace("]", "").replace("[", "").replace("'", "").strip()
        if clean_txt:
            schedule_buckets[(col_idx, hour)].append(clean_txt)

    mapped_data = []
    sorted_keys = sorted(schedule_buckets.keys(), key=lambda k: (k[0], k[1]))
    
    for (col_idx, hour) in sorted_keys:
        texts = schedule_buckets[(col_idx, hour)]
        merged_text = " ".join(texts)
        
        day_str = days[col_idx]
        time_str = f"{hour:02d}:00"
        
        mapped_data.append(f"[{day_str} | {time_str}] {merged_text}")

    return "\n".join(mapped_data)

def aggressive_json_repair(json_str: str) -> dict:
    """JSON 문자열 복구 시도"""
    json_str = re.sub(r'}\s*(?={)', '}, ', json_str)
    json_str = re.sub(r',\s*]', ']', json_str)
    for i in range(10):
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            if "Expecting ',' delimiter" in e.msg:
                json_str = json_str[:e.pos] + ',' + json_str[e.pos:]
            elif "Expecting value" in e.msg:
                if json_str.strip().endswith(','): 
                    json_str = json_str.strip()[:-1]
                else: 
                    break
            elif "Extra data" in e.msg:
                return json.loads(json_str[:e.pos])
            else: 
                break
    raise json.JSONDecodeError("JSON 복구 실패", json_str, 0)

def extract_json_from_text(text: str) -> dict:
    """텍스트에서 JSON 추출"""
    text = re.sub(r"```(?:json)?", "", text)
    text = re.sub(r"```", "", text)
    start = text.find('{')
    if start != -1:
        try:
            return aggressive_json_repair(text[start:])
        except json.JSONDecodeError:
            pass
    return {}

def create_model_inference(model_id: str):
    """지정된 모델 ID로 LLM 인스턴스 생성"""
    params = {
        GenParams.MAX_NEW_TOKENS: 2000,
        GenParams.TEMPERATURE: 0,
    }
    return ModelInference(
        model_id=model_id,
        params=params,
        credentials=credentials,
        project_id=project_id
    )

def parse_llm_response(generated_response: str) -> AIChatParsed:
    """LLM 응답 텍스트를 파싱하여 객체로 변환"""
    extracted_json = extract_json_from_text(generated_response)
    parsed_data = extracted_json if extracted_json else {}
    parsed_data.setdefault("intent", "SCHEDULE_MUTATION")
    parsed_data.setdefault("type", "UNKNOWN")
    parsed_data.setdefault("actions", [])
    
    # 시간 형식 보정 (24:00:00 -> 23:59:59)
    for action in parsed_data.get("actions", []):
        payload = action.get("payload", {})
        for time_field in ["start_at", "end_at"]:
            if time_field in payload and payload[time_field]:
                payload[time_field] = payload[time_field].replace("T24:00:00", "T23:59:59")
    
    return AIChatParsed(**parsed_data)

def process_schedule_mode(ocr_result) -> AIChatParsed:
    """ [모드 1] 시간표 처리 로직 (Grid Analysis + Text Model) """
    # 1. 격자 분석 (좌표 기반) + 전체 텍스트 덤프 (보완용)
    structured_text = geometric_grid_analysis(ocr_result)
    raw_text = simple_text_dump(ocr_result)  # 추가: 누락된 정보 보완용
    
    # 2. 날짜 컨텍스트 (이번 주 월~금)
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    dates_prompt = "\n".join([
        f"- {day}: {(start_of_week + timedelta(days=i)).strftime('%Y-%m-%d')}"
        for i, day in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri"])
    ])

    # 3. 시간표 전용 프롬프트
    instructions = """
    1. **Class Schedule (EVENT)**:
       - Extract EACH class as a separate EVENT.
       - Title: Full class name (correct any OCR typos - see TYPO CORRECTION below).
       - Location: Include room number if visible (e.g., D309, I311, G203, 상허관219, 산학215).
       
    2. **TYPO CORRECTION (CRITICAL)**:
       - "기초베드날에" or "기초베트날어" → "기초베트남어 I"
       - "나름 바꾸는" or "나를 바꾸논" → "나를 바꾸는 글쓰기"
       - "College Engli" → "College English I"
       - "말레 인니학입문" → "말레·인니학입문"
       - "베트남학입문" → "베트남학입문 I"
       - "채플" → "채플 I"
       - "대학생활과 미래 설계" → "대학생활과 미래설계 I"
       - "소프트웨어와 컴퓨터적 사고" → "소프트웨어와 컴퓨터적 사고"
       - "상히관" → "상허관" (building name correction)
       - "CMS진로람색" or "CMS진로탐색" → "CMS진로탐색"
       - "하눈세상" or "하는세상" → "독립영화와함께하는세상바로보기"
       - "경제학원론" → "경제학원론1"
       
    3. **MERGING RULES**: 
       - If the SAME class appears in consecutive time slots on the SAME day, MERGE into ONE event with extended duration.
       - Example: 18:00 'Software...' and 19:00 '...Thinking' on same day → ONE event 18:00~19:30.
       - DO NOT create separate events for room numbers - room is part of location field.
       
    4. **SEPARATION RULES (CRITICAL - MUST FOLLOW)**:
       - "아세안" is a COMPLETELY SEPARATE class from "말레·인니학입문".
       - Room numbers (like 상허관219, 산학215) are NOT class names - they belong in "location" field.
       
    5. **TIME FORMAT**:
       - Use +09:00 timezone for all times.
       - Extract time from the OCR grid position.
    """

    prompt_text = f"""You are an AI Schedule Assistant. Extract class schedules from a university timetable.

[Reference Dates - This Week]
{dates_prompt}

[GRID ANALYSIS DATA]
{structured_text if structured_text else "No grid data."}

[RAW OCR TEXT (for reference)]
{raw_text if raw_text else "No raw text."}

[INSTRUCTIONS]
{instructions}

[OUTPUT FORMAT]
{{
  "intent": "SCHEDULE_MUTATION",
  "type": "UNKNOWN",
  "actions": [
    {{
      "op": "CREATE",
      "payload": {{
        "type": "EVENT",
        "category": "수업",
        "title": "Class Name (corrected)",
        "start_at": "ISO8601 with +09:00 timezone",
        "end_at": "ISO8601 with +09:00 timezone"
      }}
    }}
  ]
}}
OUTPUT ONLY VALID JSON. DO NOT ADD EXPLANATIONS.
"""
    # 4. Text 모델 사용 (70b-instruct 등)
    model = create_model_inference(WATSONX_MODEL_ID_TEXT)
    response = model.generate_text(prompt=prompt_text)
    parsed = parse_llm_response(response)
    
    # 5. 후처리: 오타 교정 및 노이즈 필터링
    typo_corrections = {
        "상히관": "상허관",
        "CMS진로람색": "CMS진로탐색",
        "하눈세상바로보": "독립영화와함께하는세상바로보기",
        "기초베드날에": "기초베트남어 I",
        "기초베트날어": "기초베트남어 I",
        "나름 바꾸는": "나를 바꾸는 글쓰기",
        "College Engli": "College English I",
        "College English Ish I": "College English I",
        "경제학원론": "경제학원론1",
    }
    
    # 강의실 패턴 (이것들이 title로 들어가면 필터링)
    room_patterns = ['상허관', '상히관', '산학', 'D2', 'D3', 'I3', 'G2', 
                     '진A', '진4', '자A', '자B', '종3', '좀3', '문3', '동영상']
    
    filtered_actions = []
    for action in parsed.actions:
        payload = action.payload
        title = payload.get('title', '')
        
        # 강의실이 title로 잘못 들어간 경우 스킵
        is_room_only = any(p in title for p in room_patterns) and len(title) < 12
        if is_room_only:
            continue
        
        # "말레·인니학입문 아세안" 분리 처리
        if "아세안" in title and "말레" in title:
            # 아세안 분리 - 현재 이벤트는 말레·인니학입문으로 변경
            payload['title'] = "말레·인니학입문"
            # 아세안은 금요일이므로, 이 액션이 금요일이면 아세안으로 변경
            end_at = payload.get('end_at', '')
            if '01-16' in end_at or '01-17' in end_at:  # 금요일 체크
                payload['title'] = "아세안"
        
        # 오타 교정 (title)
        for typo, correct in typo_corrections.items():
            title = payload['title']
            if typo in title:
                payload['title'] = title.replace(typo, correct)
        
        # 강의실 정보 제거
        if 'location' in payload:
            del payload['location']
        
        filtered_actions.append(action)
    
    parsed.actions = filtered_actions
    return parsed

def process_poster_mode(ocr_result) -> AIChatParsed:
    """ [모드 2] 포스터 처리 로직 (Text Dump + Text Model) """
    # 1. 단순 텍스트 나열 (문맥 보존)
    structured_text = simple_text_dump(ocr_result)
    
    # 2. 날짜 컨텍스트 (절대 날짜 사용 유도)
    today = datetime.now()
    dates_prompt = f"Today: {today.strftime('%Y-%m-%d')}\nNOTE: Use dates found in text explicitly."

    # 3. 포스터 전용 프롬프트 (핵심 일정만 추출 + Sub-task 생성)
    instructions = """
    This is a POSTER for an event (Contest, Recruitment, Activity).
    
    RULES:
    1. **OUTPUT ONLY 1-2 MEANINGFUL EVENTS** from distinct dates in the poster:
       - 접수/모집 마감일 (Application Deadline) - MOST IMPORTANT
       - 활동 시작일 (Activity Start) - if clearly stated
       - 결과 발표일 (Result Announcement) - if clearly stated
       
    2. **TITLE FORMAT (Korean)**:
       - Include event name + date type (e.g., "서울청년정책네트워크 모집 마감", "K-water 봉사단 활동 시작")
       
    3. **SCORING**:
       - importance_score: 7-9 for deadlines, 5-6 for other dates
       - estimated_minute: 60-180 depending on task complexity
       
    4. **DATES**: Extract EXACT dates from text. Do not guess or use current year if year is specified.
    
    5. **SUB-TASK AUTO-GENERATION (ONLY FOR 공모전)**:
       - IF category is '공모전':
       - YOU MUST generate 3 to 5 'Sub-tasks' (Preparation steps) leading up to the deadline.
       - Sub-task Payload:
         * title: "[준비] {Original Event Title} - {Step Description}"
         * end_at: D-1, D-2, D-3... days before the main deadline.
         * importance_score: 6-8 (lower than main deadline)
         * estimated_minute: 60-180 (reasonable prep time)
         * category: "공모전"
         * tip: "Short, practical advice for this step (Korean, Max 20 chars)"
       - Example Sub-tasks for 공모전:
         * "[준비] OO공모전 마감 - 공모요강 분석" (D-7)
         * "[준비] OO공모전 마감 - 아이디어 구상" (D-5)
         * "[준비] OO공모전 마감 - 초안 작성" (D-3)
         * "[준비] OO공모전 마감 - 최종 검토 및 제출" (D-1)
    """

    prompt_text = f"""You are an AI Event Helper. Extract key schedule dates from the poster.
Output must be in KOREAN. Extract only REAL dates mentioned in the poster.

[Reference Dates]
{dates_prompt}

[TEXT DATA]
{structured_text if structured_text else "No text found."}

[INSTRUCTIONS]
{instructions}

[OUTPUT FORMAT]
{{
  "intent": "SCHEDULE_MUTATION",
  "type": "TASK",
  "actions": [
    {{
      "op": "CREATE",
      "payload": {{
        "title": "이벤트명 + 마감/시작/발표",
        "end_at": "ISO8601",
        "importance_score": 8,
        "estimated_minute": 120,
        "category": "공모전"|"대외활동"|"기타"
      }}
    }},
    {{
      "op": "CREATE",
      "payload": {{
        "title": "[준비] 이벤트명 - 준비단계",
        "end_at": "ISO8601 (D-N before deadline)",
        "importance_score": 7,
        "estimated_minute": 90,
        "category": "공모전"|"대외활동",
        "tip": "실천 팁 (20자 이내)"
      }}
    }}
  ]
}}
OUTPUT ONLY VALID JSON. NO EXPLANATIONS.
"""
    # 4. Text 모델 사용 (70b-instruct) - OCR 텍스트 분석
    model = create_model_inference(WATSONX_MODEL_ID_TEXT)
    response = model.generate_text(prompt=prompt_text)
    
    # 5. 포스터 전용 후처리 (노이즈 제거 - [준비] 태스크는 유지)
    parsed = parse_llm_response(response)
    exclude_keywords = ["심사", "선발", "문의", "면접", "서류", "교육", "OT", "사전", "혜택"]
    if parsed.actions:
        filtered_actions = [
            a for a in parsed.actions 
            if "[준비]" in a.payload.get('title', '') or  # 준비 태스크는 항상 유지
               not any(k in a.payload.get('title', '') for k in exclude_keywords)
        ]
        parsed.actions = filtered_actions
        
    return parsed

@router.post("/analyze", response_model=APIResponse, response_model_exclude_none=True)
async def analyze_image_schedule(
    file: UploadFile = File(...),
    timezone: str = "Asia/Seoul"
):
    # OCR 모듈 체크
    if not OCR_AVAILABLE:
        return APIResponse(
            status=503, 
            message="이미지 분석 기능을 사용할 수 없습니다. OCR 모듈이 설치되지 않았습니다."
        )
    
    try:
        image_bytes = await file.read()
        
        # 1. EasyOCR
        ocr_result = await run_in_threadpool(ocr_reader.readtext, image_bytes, detail=1)
        
        # 2. 이미지 타입 감지
        image_type = detect_image_type(ocr_result)
        
        # 3. 타입별 처리 로직 완전 분리
        if image_type == 'schedule':
            ai_parsed_result = process_schedule_mode(ocr_result)
        else:
            ai_parsed_result = process_poster_mode(ocr_result)
            
        action_cnt = len(ai_parsed_result.actions)
        
        # 개선된 assistant_message 생성 (sub-task 개수 표시)
        if action_cnt > 0:
            if image_type == 'poster':
                # sub-task 개수 계산
                sub_task_count = sum(1 for a in ai_parsed_result.actions if "[준비]" in a.payload.get('title', ''))
                main_task_count = action_cnt - sub_task_count
                
                if sub_task_count > 0:
                    assistant_msg = f"[POSTER] 분석 완료: {main_task_count}건의 일정과 준비 과정 {sub_task_count}건을 함께 등록할까요?"
                elif action_cnt == 1:
                    titles = [a.payload.get('title', '') for a in ai_parsed_result.actions]
                    assistant_msg = f"[POSTER] 분석 완료: '{titles[0]}' 일정을 확인했습니다."
                else:
                    assistant_msg = f"[POSTER] 분석 완료: {action_cnt}건의 주요 일정을 확인했습니다."
            else:
                assistant_msg = f"[{image_type.upper()}] 분석 완료: {action_cnt}건의 일정을 발견했습니다."
        else:
            assistant_msg = "일정을 찾지 못했습니다."

        return APIResponse(status=200, message="Success", data=ChatResponseData(
            parsed_result=ai_parsed_result,
            assistant_message=assistant_msg
        ))

    except Exception as e:
        print(f"Error: {str(e)}")
        return APIResponse(status=500, message=f"Server Error: {str(e)}")
