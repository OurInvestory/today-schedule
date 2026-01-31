"""
Syllabus OCR 서비스 - 강의계획서에서 과제/시험 일정 자동 추출
PDF/이미지 업로드 → AI 분석 → 한 학기 일정 일괄 등록
"""

import os
import json
import io
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")

genai.configure(api_key=GOOGLE_API_KEY)


@dataclass
class ExtractedSchedule:
    """추출된 일정"""
    title: str
    category: str  # exam, assignment, quiz, project, presentation
    due_date: datetime
    week_number: Optional[int]
    description: Optional[str]
    weight_percent: Optional[float]  # 성적 비중
    
    def to_dict(self):
        return {
            "title": self.title,
            "category": self.category,
            "due_date": self.due_date.isoformat(),
            "week_number": self.week_number,
            "description": self.description,
            "weight_percent": self.weight_percent
        }


@dataclass
class SyllabusInfo:
    """강의계획서 정보"""
    course_name: str
    professor: Optional[str]
    semester: str  # e.g., "2026-1"
    schedules: List[ExtractedSchedule]
    
    def to_dict(self):
        return {
            "course_name": self.course_name,
            "professor": self.professor,
            "semester": self.semester,
            "schedules": [s.to_dict() for s in self.schedules],
            "total_schedules": len(self.schedules)
        }


class SyllabusOCRService:
    """강의계획서 OCR 및 일정 추출 서비스"""
    
    def __init__(self):
        self.model = genai.GenerativeModel(
            model_name=GEMINI_MODEL_NAME,
            generation_config={
                "temperature": 0.1,  # 정확한 추출을 위해 낮은 temperature
                "response_mime_type": "application/json"
            }
        )
        
        # 현재 학기 정보 (자동 계산)
        now = datetime.now()
        if now.month >= 3 and now.month <= 8:
            self.current_semester = f"{now.year}-1"
            self.semester_start = datetime(now.year, 3, 1)
        else:
            year = now.year if now.month >= 9 else now.year - 1
            self.current_semester = f"{year}-2"
            self.semester_start = datetime(year, 9, 1)
    
    async def extract_from_image(
        self, 
        image_bytes: bytes, 
        mime_type: str = "image/jpeg"
    ) -> SyllabusInfo:
        """이미지에서 강의계획서 정보 추출"""
        
        prompt = self._build_extraction_prompt()
        
        try:
            response = self.model.generate_content([
                {"mime_type": mime_type, "data": image_bytes},
                prompt
            ])
            
            result = json.loads(response.text)
            return self._parse_result(result)
            
        except Exception as e:
            print(f"Syllabus OCR Error: {e}")
            raise
    
    async def extract_from_pdf(self, pdf_bytes: bytes) -> SyllabusInfo:
        """
        PDF에서 강의계획서 정보 추출
        Gemini 1.5+ 는 PDF를 직접 처리 가능
        """
        prompt = self._build_extraction_prompt()
        
        try:
            response = self.model.generate_content([
                {"mime_type": "application/pdf", "data": pdf_bytes},
                prompt
            ])
            
            result = json.loads(response.text)
            return self._parse_result(result)
            
        except Exception as e:
            print(f"PDF OCR Error: {e}")
            raise
    
    def _build_extraction_prompt(self) -> str:
        """추출용 프롬프트 생성"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        return f"""
        당신은 대학교 강의계획서(Syllabus) 분석 전문가입니다.
        업로드된 강의계획서에서 다음 정보를 추출해주세요.
        
        현재 날짜: {today}
        현재 학기: {self.current_semester}
        학기 시작일: {self.semester_start.strftime("%Y-%m-%d")}
        
        [추출 대상]
        1. 과목명 (Course Name)
        2. 담당 교수 (Professor)
        3. 모든 과제, 시험, 퀴즈, 프로젝트, 발표 일정
        
        [날짜 추론 규칙]
        - "N주차"로 표시된 경우: 학기 시작일로부터 N주 후 금요일로 계산
        - 구체적인 날짜가 있으면 그대로 사용
        - "중간고사 기간", "기말고사 기간"은 일반적으로 8주차, 16주차
        - 날짜가 불명확하면 best effort로 추정
        
        [OUTPUT JSON FORMAT]
        {{
            "course_name": "과목명",
            "professor": "교수 이름 또는 null",
            "semester": "{self.current_semester}",
            "schedules": [
                {{
                    "title": "중간고사" | "기말고사" | "과제1" | "퀴즈" 등,
                    "category": "exam" | "assignment" | "quiz" | "project" | "presentation",
                    "due_date": "YYYY-MM-DD",
                    "week_number": 8,  // 주차 (있으면)
                    "description": "상세 설명 (있으면)",
                    "weight_percent": 20  // 성적 비중 (있으면)
                }}
            ]
        }}
        
        [주의사항]
        - 성적 평가 항목에서 비중(%)도 함께 추출
        - 날짜가 없는 항목도 주차 정보로 추정하여 포함
        - 중간/기말고사는 반드시 포함
        - 조별 과제, 개인 과제 구분
        """
    
    def _parse_result(self, result: dict) -> SyllabusInfo:
        """AI 결과 파싱"""
        schedules = []
        
        for s in result.get("schedules", []):
            # 날짜 파싱
            due_date_str = s.get("due_date")
            due_date = None
            
            if due_date_str:
                try:
                    due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
                except:
                    # 주차 정보로 계산
                    week = s.get("week_number")
                    if week:
                        due_date = self.semester_start + timedelta(weeks=week-1, days=4)  # 금요일
            
            if not due_date:
                continue  # 날짜 없으면 스킵
            
            schedules.append(ExtractedSchedule(
                title=s.get("title", "일정"),
                category=s.get("category", "assignment"),
                due_date=due_date,
                week_number=s.get("week_number"),
                description=s.get("description"),
                weight_percent=s.get("weight_percent")
            ))
        
        return SyllabusInfo(
            course_name=result.get("course_name", "알 수 없는 과목"),
            professor=result.get("professor"),
            semester=result.get("semester", self.current_semester),
            schedules=schedules
        )
    
    def generate_schedule_payloads(self, syllabus: SyllabusInfo) -> List[dict]:
        """
        추출된 정보를 Schedule 생성 payload로 변환
        기존 API 스키마와 호환
        """
        payloads = []
        
        for schedule in syllabus.schedules:
            # 예상 소요 시간 추정
            estimated_minutes = self._estimate_minutes(schedule)
            
            # 중요도 계산
            priority = self._calculate_priority(schedule)
            
            payloads.append({
                "title": f"[{syllabus.course_name}] {schedule.title}",
                "category": self._map_category(schedule.category),
                "end_at": schedule.due_date.isoformat(),
                "start_at": (schedule.due_date - timedelta(days=7)).isoformat(),  # 1주일 전부터
                "type": "task",
                "priority_score": priority,
                "estimated_minute": estimated_minutes,
                "original_text": schedule.description or f"{schedule.title} - {syllabus.course_name}",
                "source": "syllabus_ocr"
            })
        
        return payloads
    
    def _estimate_minutes(self, schedule: ExtractedSchedule) -> int:
        """예상 소요 시간 추정"""
        category = schedule.category
        weight = schedule.weight_percent or 10
        
        # 비중에 따른 기본 시간
        base_minutes = weight * 6  # 1% = 6분
        
        # 카테고리별 배수
        multipliers = {
            "exam": 3.0,      # 시험 준비
            "project": 2.5,   # 프로젝트
            "assignment": 1.5,
            "presentation": 2.0,
            "quiz": 0.5
        }
        
        multiplier = multipliers.get(category, 1.0)
        return int(base_minutes * multiplier)
    
    def _calculate_priority(self, schedule: ExtractedSchedule) -> int:
        """우선순위 계산 (1-10)"""
        base = 5
        
        # 비중이 높을수록 우선순위 증가
        if schedule.weight_percent:
            if schedule.weight_percent >= 30:
                base += 3
            elif schedule.weight_percent >= 15:
                base += 2
            elif schedule.weight_percent >= 5:
                base += 1
        
        # 시험은 추가 우선순위
        if schedule.category == "exam":
            base += 2
        elif schedule.category == "project":
            base += 1
        
        return min(base, 10)
    
    def _map_category(self, category: str) -> str:
        """카테고리 매핑"""
        mapping = {
            "exam": "exam",
            "assignment": "assignment",
            "quiz": "exam",
            "project": "team",
            "presentation": "team"
        }
        return mapping.get(category, "assignment")


# 서비스 인스턴스
syllabus_ocr_service = SyllabusOCRService()
