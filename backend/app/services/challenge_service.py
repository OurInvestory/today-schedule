"""
공강 시간 활용 '학습 챌린지' 추천 서비스
- 주간 시간표 분석
- 빈 시간대 감지
- AI 기반 학습 제안
"""

import os
import json
from datetime import datetime, timedelta, time
from typing import List, Dict, Optional
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import and_
import google.generativeai as genai
from dotenv import load_dotenv

from app.models.lecture import Lecture
from app.models.schedule import Schedule
from app.models.sub_task import SubTask

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")

genai.configure(api_key=GOOGLE_API_KEY)


@dataclass
class TimeSlot:
    """시간 슬롯"""
    day: int  # 0=월, 6=일
    start_time: time
    end_time: time
    duration_minutes: int
    
    def to_dict(self):
        return {
            "day": self.day,
            "day_name": ["월", "화", "수", "목", "금", "토", "일"][self.day],
            "start_time": self.start_time.strftime("%H:%M"),
            "end_time": self.end_time.strftime("%H:%M"),
            "duration_minutes": self.duration_minutes
        }


@dataclass
class LearningChallenge:
    """학습 챌린지 제안"""
    title: str
    description: str
    recommended_time_slot: TimeSlot
    related_schedule_id: Optional[str]
    related_schedule_title: Optional[str]
    estimated_minutes: int
    priority: str  # high, medium, low
    challenge_type: str  # preview, review, assignment, project
    
    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "recommended_time_slot": self.recommended_time_slot.to_dict(),
            "related_schedule_id": self.related_schedule_id,
            "related_schedule_title": self.related_schedule_title,
            "estimated_minutes": self.estimated_minutes,
            "priority": self.priority,
            "challenge_type": self.challenge_type
        }


class GapTimeAnalyzer:
    """공강 시간 분석기"""
    
    # 학습 가능 시간대 (기본: 9시~22시)
    STUDY_START = time(9, 0)
    STUDY_END = time(22, 0)
    
    # 최소 공강 시간 (분)
    MIN_GAP_MINUTES = 60
    
    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id
    
    def get_weekly_lectures(self, target_date: datetime) -> Dict[int, List[Dict]]:
        """해당 주의 강의 시간표 조회"""
        # 주의 시작일 (월요일)
        start_of_week = target_date - timedelta(days=target_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        lectures = self.db.query(Lecture).filter(
            and_(
                Lecture.user_id == self.user_id,
                Lecture.start_day <= end_of_week.date(),
                Lecture.end_day >= start_of_week.date()
            )
        ).all()
        
        # 요일별로 그룹화
        weekly_schedule = {i: [] for i in range(7)}
        
        for lecture in lectures:
            # week 필드는 "0,2,4" 형태 (월,수,금)
            days = [int(d) for d in lecture.week.split(",") if d.strip()]
            for day in days:
                weekly_schedule[day].append({
                    "title": lecture.title,
                    "start_time": lecture.start_time,
                    "end_time": lecture.end_time,
                    "type": "lecture"
                })
        
        return weekly_schedule
    
    def get_weekly_schedules(self, target_date: datetime) -> Dict[int, List[Dict]]:
        """해당 주의 일정 조회"""
        start_of_week = target_date - timedelta(days=target_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        schedules = self.db.query(Schedule).filter(
            and_(
                Schedule.user_id == self.user_id,
                Schedule.start_at >= start_of_week,
                Schedule.end_at <= end_of_week + timedelta(days=1)
            )
        ).all()
        
        weekly_schedule = {i: [] for i in range(7)}
        
        for schedule in schedules:
            if schedule.start_at:
                day = schedule.start_at.weekday()
                weekly_schedule[day].append({
                    "title": schedule.title,
                    "start_time": schedule.start_at.time(),
                    "end_time": schedule.end_at.time() if schedule.end_at else schedule.start_at.time(),
                    "type": "schedule",
                    "schedule_id": schedule.schedule_id,
                    "category": schedule.category
                })
        
        return weekly_schedule
    
    def find_gap_times(self, target_date: datetime) -> List[TimeSlot]:
        """공강 시간대 찾기"""
        lectures = self.get_weekly_lectures(target_date)
        schedules = self.get_weekly_schedules(target_date)
        
        gap_times = []
        
        for day in range(7):  # 월~일
            # 해당 요일의 모든 일정 합치기
            day_events = lectures[day] + schedules[day]
            
            # 시작 시간 기준 정렬
            day_events.sort(key=lambda x: x["start_time"])
            
            # 공강 시간 찾기
            current_time = self.STUDY_START
            
            for event in day_events:
                event_start = event["start_time"]
                event_end = event["end_time"]
                
                # 현재 시간과 이벤트 시작 사이에 공백이 있으면
                if event_start > current_time:
                    gap_minutes = (
                        datetime.combine(datetime.today(), event_start) -
                        datetime.combine(datetime.today(), current_time)
                    ).seconds // 60
                    
                    if gap_minutes >= self.MIN_GAP_MINUTES:
                        gap_times.append(TimeSlot(
                            day=day,
                            start_time=current_time,
                            end_time=event_start,
                            duration_minutes=gap_minutes
                        ))
                
                # 현재 시간 업데이트
                if event_end > current_time:
                    current_time = event_end
            
            # 마지막 일정 후 ~ 학습 종료 시간 사이 공백
            if current_time < self.STUDY_END:
                gap_minutes = (
                    datetime.combine(datetime.today(), self.STUDY_END) -
                    datetime.combine(datetime.today(), current_time)
                ).seconds // 60
                
                if gap_minutes >= self.MIN_GAP_MINUTES:
                    gap_times.append(TimeSlot(
                        day=day,
                        start_time=current_time,
                        end_time=self.STUDY_END,
                        duration_minutes=gap_minutes
                    ))
        
        return gap_times
    
    def get_upcoming_deadlines(self, days_ahead: int = 14) -> List[Schedule]:
        """다가오는 마감 일정 조회"""
        now = datetime.now()
        deadline = now + timedelta(days=days_ahead)
        
        return self.db.query(Schedule).filter(
            and_(
                Schedule.user_id == self.user_id,
                Schedule.end_at >= now,
                Schedule.end_at <= deadline,
                Schedule.category.in_(["assignment", "exam", "team", "contest"])
            )
        ).order_by(Schedule.end_at.asc()).all()
    
    def get_incomplete_subtasks(self) -> List[SubTask]:
        """미완료 서브태스크 조회"""
        return self.db.query(SubTask).filter(
            and_(
                SubTask.user_id == self.user_id,
                SubTask.is_done == False,
                SubTask.date >= datetime.now().date()
            )
        ).order_by(SubTask.date.asc()).limit(10).all()


class LearningChallengeRecommender:
    """학습 챌린지 추천 엔진"""
    
    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id
        self.analyzer = GapTimeAnalyzer(db, user_id)
        self.model = genai.GenerativeModel(
            model_name=GEMINI_MODEL_NAME,
            generation_config={
                "temperature": 0.7,
                "response_mime_type": "application/json"
            }
        )
    
    def generate_challenges(self, target_date: datetime = None) -> List[LearningChallenge]:
        """학습 챌린지 생성"""
        if target_date is None:
            target_date = datetime.now()
        
        # 1. 공강 시간 분석
        gap_times = self.analyzer.find_gap_times(target_date)
        
        # 2. 다가오는 마감 일정
        upcoming_deadlines = self.analyzer.get_upcoming_deadlines()
        
        # 3. 미완료 태스크
        incomplete_tasks = self.analyzer.get_incomplete_subtasks()
        
        if not gap_times:
            return []
        
        # 4. AI로 맞춤 챌린지 생성
        challenges = self._generate_ai_challenges(
            gap_times, upcoming_deadlines, incomplete_tasks
        )
        
        return challenges
    
    def _generate_ai_challenges(
        self,
        gap_times: List[TimeSlot],
        deadlines: List[Schedule],
        tasks: List[SubTask]
    ) -> List[LearningChallenge]:
        """AI 기반 챌린지 생성"""
        
        # 프롬프트 데이터 준비
        gap_data = [g.to_dict() for g in gap_times[:10]]  # 최대 10개
        deadline_data = [
            {
                "schedule_id": s.schedule_id,
                "title": s.title,
                "category": s.category,
                "end_at": s.end_at.isoformat(),
                "days_left": (s.end_at - datetime.now()).days,
                "estimated_minute": s.estimated_minute
            }
            for s in deadlines[:5]
        ]
        task_data = [
            {
                "title": t.title,
                "date": t.date.isoformat(),
                "priority": t.priority,
                "category": t.category
            }
            for t in tasks[:5]
        ]
        
        prompt = f"""
        당신은 대학생 학습 코치입니다. 사용자의 공강 시간과 다가오는 일정을 분석하여
        효과적인 학습 챌린지를 추천해주세요.
        
        [공강 시간대]
        {json.dumps(gap_data, ensure_ascii=False)}
        
        [다가오는 마감 일정]
        {json.dumps(deadline_data, ensure_ascii=False)}
        
        [미완료 태스크]
        {json.dumps(task_data, ensure_ascii=False)}
        
        [추천 규칙]
        1. 공강 시간에 맞는 적절한 학습 활동 추천
        2. 마감이 가까운 과제/시험 우선
        3. 2시간 이상 공강은 과제 작업, 1시간은 복습/예습 추천
        4. 동기부여가 되는 친근한 문구 사용
        5. 최대 5개의 챌린지 생성
        
        [OUTPUT JSON FORMAT]
        {{
            "challenges": [
                {{
                    "title": "챌린지 제목",
                    "description": "구체적인 설명과 격려 문구",
                    "day": 0,  // 추천 요일 (0=월)
                    "start_time": "HH:MM",
                    "end_time": "HH:MM",
                    "related_schedule_id": "연관된 일정 ID 또는 null",
                    "related_schedule_title": "연관된 일정 제목 또는 null",
                    "estimated_minutes": 60,
                    "priority": "high|medium|low",
                    "challenge_type": "preview|review|assignment|project"
                }}
            ]
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            
            challenges = []
            for c in result.get("challenges", []):
                # TimeSlot 찾기
                time_slot = None
                for gap in gap_times:
                    if gap.day == c.get("day"):
                        time_slot = gap
                        break
                
                if not time_slot:
                    time_slot = gap_times[0] if gap_times else None
                
                if time_slot:
                    challenges.append(LearningChallenge(
                        title=c.get("title", "학습 챌린지"),
                        description=c.get("description", ""),
                        recommended_time_slot=time_slot,
                        related_schedule_id=c.get("related_schedule_id"),
                        related_schedule_title=c.get("related_schedule_title"),
                        estimated_minutes=c.get("estimated_minutes", 60),
                        priority=c.get("priority", "medium"),
                        challenge_type=c.get("challenge_type", "review")
                    ))
            
            return challenges
            
        except Exception as e:
            print(f"AI Challenge Generation Error: {e}")
            # 폴백: 기본 챌린지 생성
            return self._generate_fallback_challenges(gap_times, deadlines)
    
    def _generate_fallback_challenges(
        self,
        gap_times: List[TimeSlot],
        deadlines: List[Schedule]
    ) -> List[LearningChallenge]:
        """AI 실패 시 기본 챌린지"""
        challenges = []
        
        for i, gap in enumerate(gap_times[:3]):
            if deadlines:
                deadline = deadlines[i % len(deadlines)]
                days_left = (deadline.end_at - datetime.now()).days
                
                challenges.append(LearningChallenge(
                    title=f"📚 {deadline.title} 준비하기",
                    description=f"마감까지 {days_left}일! 지금 {gap.duration_minutes}분 동안 미리 시작해볼까요?",
                    recommended_time_slot=gap,
                    related_schedule_id=deadline.schedule_id,
                    related_schedule_title=deadline.title,
                    estimated_minutes=min(gap.duration_minutes, 90),
                    priority="high" if days_left <= 3 else "medium",
                    challenge_type="assignment"
                ))
            else:
                challenges.append(LearningChallenge(
                    title="✨ 자기계발 시간",
                    description=f"{gap.duration_minutes}분의 여유 시간! 새로운 것을 배워보는 건 어떨까요?",
                    recommended_time_slot=gap,
                    related_schedule_id=None,
                    related_schedule_title=None,
                    estimated_minutes=gap.duration_minutes,
                    priority="low",
                    challenge_type="review"
                ))
        
        return challenges
    
    def get_today_challenge(self) -> Optional[LearningChallenge]:
        """오늘의 챌린지 (가장 적합한 1개)"""
        challenges = self.generate_challenges()
        
        if not challenges:
            return None
        
        # 우선순위 정렬: high > medium > low
        priority_order = {"high": 0, "medium": 1, "low": 2}
        challenges.sort(key=lambda x: priority_order.get(x.priority, 2))
        
        # 오늘 요일에 해당하는 것 우선
        today = datetime.now().weekday()
        for challenge in challenges:
            if challenge.recommended_time_slot.day == today:
                return challenge
        
        return challenges[0]
