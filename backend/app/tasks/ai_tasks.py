"""
AI 관련 비동기 태스크
- Gemini AI 호출
- 이미지 분석 (Vision)
- 일정 분석
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from app.core.celery_app import celery_app
from app.core.cache import cache_service
from app.db.database import db_session

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_ai_chat(self, user_id: str, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """
    AI 채팅 메시지 비동기 처리
    
    긴 응답 시간이 예상되는 복잡한 쿼리에 사용
    """
    task_id = self.request.id
    
    try:
        # 작업 상태 업데이트: 처리 중
        cache_service.set_task_status(task_id, {
            "status": "processing",
            "message": "AI가 분석 중입니다...",
            "started_at": datetime.now().isoformat(),
        })
        
        # Gemini AI 호출 (여기서는 간단한 예시)
        import google.generativeai as genai
        
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")
        
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel(model_name=GEMINI_MODEL_NAME)
        
        response = model.generate_content(message)
        result_text = response.text
        
        # 작업 완료
        result = {
            "status": "completed",
            "message": "분석이 완료되었습니다.",
            "result": result_text,
            "completed_at": datetime.now().isoformat(),
        }
        cache_service.set_task_status(task_id, result)
        
        return result
        
    except Exception as e:
        logger.error(f"AI Chat Task Error: {e}")
        
        # 재시도
        if self.request.retries < self.max_retries:
            cache_service.set_task_status(task_id, {
                "status": "retrying",
                "message": f"오류 발생, 재시도 중... ({self.request.retries + 1}/{self.max_retries})",
                "error": str(e),
            })
            raise self.retry(exc=e)
        
        # 최종 실패
        error_result = {
            "status": "failed",
            "message": "AI 처리 중 오류가 발생했습니다.",
            "error": str(e),
            "failed_at": datetime.now().isoformat(),
        }
        cache_service.set_task_status(task_id, error_result)
        return error_result


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def analyze_schedule_image(self, user_id: str, image_data: str, image_type: str = "timetable") -> Dict[str, Any]:
    """
    시간표/일정 이미지 분석 비동기 처리
    
    Vision AI를 사용한 이미지 분석은 시간이 걸리므로 비동기 처리
    """
    task_id = self.request.id
    
    try:
        # 작업 상태 업데이트
        cache_service.set_task_status(task_id, {
            "status": "processing",
            "message": "이미지를 분석 중입니다...",
            "image_type": image_type,
            "started_at": datetime.now().isoformat(),
        })
        
        # Gemini Vision 호출
        import google.generativeai as genai
        import base64
        
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=GOOGLE_API_KEY)
        
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # 이미지 분석 프롬프트
        prompt = """
        이 이미지에서 일정/시간표 정보를 추출해주세요.
        JSON 형식으로 반환해주세요:
        {
            "schedules": [
                {"title": "과목명", "day": "요일", "start_time": "시작시간", "end_time": "종료시간"}
            ]
        }
        """
        
        # Base64 이미지 처리
        image_bytes = base64.b64decode(image_data)
        
        response = model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": image_bytes}
        ])
        
        # 결과 파싱
        result_text = response.text
        try:
            # JSON 추출 시도
            import re
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                parsed_result = json.loads(json_match.group())
            else:
                parsed_result = {"raw_text": result_text}
        except json.JSONDecodeError:
            parsed_result = {"raw_text": result_text}
        
        # 작업 완료
        result = {
            "status": "completed",
            "message": "이미지 분석이 완료되었습니다.",
            "result": parsed_result,
            "completed_at": datetime.now().isoformat(),
        }
        cache_service.set_task_status(task_id, result)
        
        return result
        
    except Exception as e:
        logger.error(f"Image Analysis Task Error: {e}")
        
        if self.request.retries < self.max_retries:
            cache_service.set_task_status(task_id, {
                "status": "retrying",
                "message": f"분석 오류, 재시도 중...",
                "error": str(e),
            })
            raise self.retry(exc=e)
        
        error_result = {
            "status": "failed",
            "message": "이미지 분석 중 오류가 발생했습니다.",
            "error": str(e),
            "failed_at": datetime.now().isoformat(),
        }
        cache_service.set_task_status(task_id, error_result)
        return error_result


@celery_app.task(bind=True)
def recalculate_user_priorities(self, user_id: str) -> Dict[str, Any]:
    """
    사용자의 모든 일정 우선순위 재계산 (백그라운드)
    """
    task_id = self.request.id
    
    try:
        cache_service.set_task_status(task_id, {
            "status": "processing",
            "message": "우선순위를 재계산 중입니다...",
            "started_at": datetime.now().isoformat(),
        })
        
        from app.services.schedule_intelligence import ScheduleIntelligenceService
        
        db = db_session()
        try:
            service = ScheduleIntelligenceService(db, user_id)
            updated = service.recalculate_all_priorities()
            
            # 캐시 무효화
            cache_service.invalidate_user_cache(user_id)
            
            result = {
                "status": "completed",
                "message": f"{len(updated)}건의 일정 우선순위가 업데이트되었습니다.",
                "updated_count": len(updated),
                "completed_at": datetime.now().isoformat(),
            }
            cache_service.set_task_status(task_id, result)
            
            return result
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Priority Recalculation Error: {e}")
        
        error_result = {
            "status": "failed",
            "message": "우선순위 재계산 중 오류가 발생했습니다.",
            "error": str(e),
            "failed_at": datetime.now().isoformat(),
        }
        cache_service.set_task_status(task_id, error_result)
        return error_result
