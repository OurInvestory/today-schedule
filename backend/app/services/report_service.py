"""
학습 리포트 서비스
- 예상 시간 vs 실제 완료 시간 비교
- 주간/월간 통계
- 카테고리별 분석
- 실천율 계산
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, field

from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import google.generativeai as genai
from dotenv import load_dotenv

from app.models.schedule import Schedule
from app.models.sub_task import SubTask

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")

genai.configure(api_key=GOOGLE_API_KEY)


@dataclass
class CategoryStats:
    """카테고리별 통계"""
    category: str
    category_name: str
    total_count: int
    completed_count: int
    total_estimated_minutes: int
    total_actual_minutes: int  # 실제 소요 시간 (완료된 것만)
    completion_rate: float
    time_accuracy: float  # 예상 대비 실제 시간 정확도
    
    def to_dict(self):
        return {
            "category": self.category,
            "category_name": self.category_name,
            "total_count": self.total_count,
            "completed_count": self.completed_count,
            "total_estimated_minutes": self.total_estimated_minutes,
            "total_actual_minutes": self.total_actual_minutes,
            "completion_rate": round(self.completion_rate, 1),
            "time_accuracy": round(self.time_accuracy, 1),
            "estimated_hours": round(self.total_estimated_minutes / 60, 1),
            "actual_hours": round(self.total_actual_minutes / 60, 1)
        }


@dataclass
class WeeklyReport:
    """주간 리포트"""
    start_date: datetime
    end_date: datetime
    total_schedules: int
    completed_schedules: int
    total_subtasks: int
    completed_subtasks: int
    overall_completion_rate: float
    category_stats: List[CategoryStats]
    daily_completion: Dict[str, Dict]  # 요일별 완료율
    top_category: str  # 가장 많은 시간을 쓴 카테고리
    ai_feedback: str  # AI 피드백 메시지
    improvement_tips: List[str]  # 개선 팁
    
    def to_dict(self):
        return {
            "period": {
                "start_date": self.start_date.strftime("%Y-%m-%d"),
                "end_date": self.end_date.strftime("%Y-%m-%d"),
                "type": "weekly"
            },
            "summary": {
                "total_schedules": self.total_schedules,
                "completed_schedules": self.completed_schedules,
                "total_subtasks": self.total_subtasks,
                "completed_subtasks": self.completed_subtasks,
                "overall_completion_rate": round(self.overall_completion_rate, 1)
            },
            "category_stats": [c.to_dict() for c in self.category_stats],
            "daily_completion": self.daily_completion,
            "insights": {
                "top_category": self.top_category,
                "ai_feedback": self.ai_feedback,
                "improvement_tips": self.improvement_tips
            }
        }


@dataclass
class MonthlyReport:
    """월간 리포트"""
    year: int
    month: int
    weekly_summaries: List[Dict]
    total_hours_studied: float
    average_daily_hours: float
    best_day: str  # 가장 생산적인 요일
    category_trend: Dict[str, List[float]]  # 카테고리별 주차 트렌드
    monthly_goal_progress: float
    ai_monthly_review: str
    
    def to_dict(self):
        return {
            "period": {
                "year": self.year,
                "month": self.month,
                "type": "monthly"
            },
            "summary": {
                "total_hours_studied": round(self.total_hours_studied, 1),
                "average_daily_hours": round(self.average_daily_hours, 1),
                "best_day": self.best_day,
                "monthly_goal_progress": round(self.monthly_goal_progress, 1)
            },
            "weekly_summaries": self.weekly_summaries,
            "category_trend": self.category_trend,
            "ai_monthly_review": self.ai_monthly_review
        }


class LearningReportService:
    """학습 리포트 서비스"""
    
    CATEGORY_NAMES = {
        "class": "수업",
        "assignment": "과제",
        "exam": "시험",
        "contest": "공모전",
        "activity": "대외활동",
        "team": "팀 프로젝트",
        "personal": "개인",
        "other": "기타"
    }
    
    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id
        self.model = genai.GenerativeModel(
            model_name=GEMINI_MODEL_NAME,
            generation_config={
                "temperature": 0.7,
                "response_mime_type": "application/json"
            }
        )
    
    def generate_weekly_report(self, target_date: datetime = None) -> WeeklyReport:
        """주간 리포트 생성"""
        if target_date is None:
            target_date = datetime.now()
        
        # 주의 시작/끝
        start_of_week = target_date - timedelta(days=target_date.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)
        
        # 1. 일정 통계
        schedules = self._get_schedules(start_of_week, end_of_week)
        completed_schedules = [s for s in schedules if self._is_schedule_completed(s)]
        
        # 2. 서브태스크 통계
        subtasks = self._get_subtasks(start_of_week.date(), end_of_week.date())
        completed_subtasks = [t for t in subtasks if t.is_done]
        
        # 3. 카테고리별 통계
        category_stats = self._calculate_category_stats(schedules, subtasks)
        
        # 4. 요일별 완료율
        daily_completion = self._calculate_daily_completion(subtasks, start_of_week)
        
        # 5. 전체 완료율
        total_items = len(schedules) + len(subtasks)
        completed_items = len(completed_schedules) + len(completed_subtasks)
        overall_rate = (completed_items / total_items * 100) if total_items > 0 else 0
        
        # 6. 가장 많은 시간을 쓴 카테고리
        top_category = max(
            category_stats,
            key=lambda x: x.total_actual_minutes,
            default=None
        )
        
        # 7. AI 피드백 생성
        ai_feedback, tips = self._generate_ai_feedback(
            overall_rate, category_stats, daily_completion
        )
        
        return WeeklyReport(
            start_date=start_of_week,
            end_date=end_of_week,
            total_schedules=len(schedules),
            completed_schedules=len(completed_schedules),
            total_subtasks=len(subtasks),
            completed_subtasks=len(completed_subtasks),
            overall_completion_rate=overall_rate,
            category_stats=category_stats,
            daily_completion=daily_completion,
            top_category=top_category.category_name if top_category else "없음",
            ai_feedback=ai_feedback,
            improvement_tips=tips
        )
    
    def generate_monthly_report(self, year: int = None, month: int = None) -> MonthlyReport:
        """월간 리포트 생성"""
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month
        
        # 해당 월의 주간 리포트들 수집
        first_day = datetime(year, month, 1)
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)
        
        weekly_summaries = []
        total_hours = 0
        category_trend = {}
        
        current = first_day
        week_num = 1
        while current <= last_day:
            weekly = self.generate_weekly_report(current)
            
            # 주간 요약
            weekly_summaries.append({
                "week": week_num,
                "completion_rate": weekly.overall_completion_rate,
                "total_tasks": weekly.total_subtasks,
                "completed_tasks": weekly.completed_subtasks
            })
            
            # 총 학습 시간
            for cat in weekly.category_stats:
                total_hours += cat.total_actual_minutes / 60
                
                # 카테고리 트렌드
                if cat.category not in category_trend:
                    category_trend[cat.category] = []
                category_trend[cat.category].append(cat.total_actual_minutes / 60)
            
            current += timedelta(days=7)
            week_num += 1
        
        # 일 수 계산
        days_in_month = (last_day - first_day).days + 1
        avg_daily = total_hours / days_in_month if days_in_month > 0 else 0
        
        # 가장 생산적인 요일 계산
        best_day = self._find_best_day(first_day, last_day)
        
        # AI 월간 리뷰
        ai_review = self._generate_monthly_review(
            weekly_summaries, total_hours, category_trend
        )
        
        return MonthlyReport(
            year=year,
            month=month,
            weekly_summaries=weekly_summaries,
            total_hours_studied=total_hours,
            average_daily_hours=avg_daily,
            best_day=best_day,
            category_trend=category_trend,
            monthly_goal_progress=sum(w["completion_rate"] for w in weekly_summaries) / len(weekly_summaries) if weekly_summaries else 0,
            ai_monthly_review=ai_review
        )
    
    def _get_schedules(self, start: datetime, end: datetime) -> List[Schedule]:
        """기간 내 일정 조회"""
        return self.db.query(Schedule).filter(
            and_(
                Schedule.user_id == self.user_id,
                Schedule.end_at >= start,
                Schedule.end_at <= end
            )
        ).all()
    
    def _get_subtasks(self, start_date, end_date) -> List[SubTask]:
        """기간 내 서브태스크 조회"""
        return self.db.query(SubTask).filter(
            and_(
                SubTask.user_id == self.user_id,
                SubTask.date >= start_date,
                SubTask.date <= end_date
            )
        ).all()
    
    def _is_schedule_completed(self, schedule: Schedule) -> bool:
        """일정 완료 여부 (관련 서브태스크 기준)"""
        if not schedule.sub_tasks:
            return schedule.end_at < datetime.now()
        
        completed = sum(1 for t in schedule.sub_tasks if t.is_done)
        return completed == len(schedule.sub_tasks)
    
    def _calculate_category_stats(
        self, 
        schedules: List[Schedule], 
        subtasks: List[SubTask]
    ) -> List[CategoryStats]:
        """카테고리별 통계 계산"""
        stats = {}
        
        # 일정에서 통계 수집
        for schedule in schedules:
            cat = schedule.category or "other"
            if cat not in stats:
                stats[cat] = {
                    "total": 0,
                    "completed": 0,
                    "estimated": 0,
                    "actual": 0
                }
            
            stats[cat]["total"] += 1
            if self._is_schedule_completed(schedule):
                stats[cat]["completed"] += 1
                stats[cat]["actual"] += schedule.estimated_minute or 0
            
            stats[cat]["estimated"] += schedule.estimated_minute or 0
        
        # 서브태스크에서 통계 수집
        for task in subtasks:
            cat = task.category or "other"
            if cat not in stats:
                stats[cat] = {
                    "total": 0,
                    "completed": 0,
                    "estimated": 0,
                    "actual": 0
                }
            
            stats[cat]["total"] += 1
            stats[cat]["estimated"] += task.estimated_minute or 30  # 기본 30분
            
            if task.is_done:
                stats[cat]["completed"] += 1
                stats[cat]["actual"] += task.estimated_minute or 30
        
        # CategoryStats 객체로 변환
        result = []
        for cat, data in stats.items():
            completion_rate = (data["completed"] / data["total"] * 100) if data["total"] > 0 else 0
            time_accuracy = (data["actual"] / data["estimated"] * 100) if data["estimated"] > 0 else 100
            
            result.append(CategoryStats(
                category=cat,
                category_name=self.CATEGORY_NAMES.get(cat, cat),
                total_count=data["total"],
                completed_count=data["completed"],
                total_estimated_minutes=data["estimated"],
                total_actual_minutes=data["actual"],
                completion_rate=completion_rate,
                time_accuracy=time_accuracy
            ))
        
        return sorted(result, key=lambda x: x.total_actual_minutes, reverse=True)
    
    def _calculate_daily_completion(
        self, 
        subtasks: List[SubTask], 
        start_of_week: datetime
    ) -> Dict[str, Dict]:
        """요일별 완료율 계산"""
        days = ["월", "화", "수", "목", "금", "토", "일"]
        daily = {day: {"total": 0, "completed": 0, "rate": 0} for day in days}
        
        for task in subtasks:
            day_idx = task.date.weekday()
            day_name = days[day_idx]
            
            daily[day_name]["total"] += 1
            if task.is_done:
                daily[day_name]["completed"] += 1
        
        # 완료율 계산
        for day in days:
            if daily[day]["total"] > 0:
                daily[day]["rate"] = round(
                    daily[day]["completed"] / daily[day]["total"] * 100, 1
                )
        
        return daily
    
    def _find_best_day(self, start: datetime, end: datetime) -> str:
        """가장 생산적인 요일 찾기"""
        days = ["월", "화", "수", "목", "금", "토", "일"]
        day_counts = {day: 0 for day in days}
        
        subtasks = self._get_subtasks(start.date(), end.date())
        
        for task in subtasks:
            if task.is_done:
                day_idx = task.date.weekday()
                day_counts[days[day_idx]] += 1
        
        best = max(day_counts, key=day_counts.get)
        return best if day_counts[best] > 0 else "없음"
    
    def _generate_ai_feedback(
        self,
        completion_rate: float,
        category_stats: List[CategoryStats],
        daily_completion: Dict
    ) -> tuple:
        """AI 피드백 생성"""
        
        # 통계 데이터 준비
        stats_data = {
            "completion_rate": completion_rate,
            "categories": [c.to_dict() for c in category_stats[:5]],
            "daily": daily_completion
        }
        
        prompt = f"""
        대학생 학습 코치로서 이번 주 학습 통계를 분석하고 피드백을 제공해주세요.
        
        [통계 데이터]
        {json.dumps(stats_data, ensure_ascii=False)}
        
        [피드백 규칙]
        1. 긍정적이고 격려하는 톤 유지
        2. 구체적인 수치 언급
        3. 개선점은 부드럽게 제안
        4. 이모지 적절히 사용
        
        [OUTPUT JSON FORMAT]
        {{
            "main_feedback": "메인 피드백 메시지 (2-3문장)",
            "tips": ["개선 팁1", "개선 팁2", "개선 팁3"]
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            return result.get("main_feedback", ""), result.get("tips", [])
        except:
            # 폴백 피드백
            if completion_rate >= 80:
                feedback = f"🎉 이번 주 실천율 {completion_rate:.0f}%! 정말 잘하고 있어요!"
            elif completion_rate >= 50:
                feedback = f"💪 이번 주 실천율 {completion_rate:.0f}%. 조금만 더 힘내봐요!"
            else:
                feedback = f"📚 이번 주 실천율 {completion_rate:.0f}%. 다음 주엔 더 잘할 수 있어요!"
            
            return feedback, ["작은 목표부터 시작해보세요", "규칙적인 학습 시간을 정해보세요"]
    
    def _generate_monthly_review(
        self,
        weekly_summaries: List[Dict],
        total_hours: float,
        category_trend: Dict
    ) -> str:
        """월간 AI 리뷰 생성"""
        
        prompt = f"""
        이번 달 학습 통계를 분석하여 월간 리뷰를 작성해주세요.
        
        [주간 요약]
        {json.dumps(weekly_summaries, ensure_ascii=False)}
        
        [총 학습 시간]
        {total_hours:.1f}시간
        
        [카테고리별 트렌드 (주차별 시간)]
        {json.dumps(category_trend, ensure_ascii=False)}
        
        [작성 규칙]
        - 3-4문장으로 요약
        - 성장한 부분 강조
        - 다음 달 목표 제안
        - 격려하는 톤
        
        [OUTPUT JSON FORMAT]
        {{
            "review": "월간 리뷰 메시지"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            return result.get("review", "이번 달도 수고하셨습니다!")
        except:
            avg_rate = sum(w["completion_rate"] for w in weekly_summaries) / len(weekly_summaries) if weekly_summaries else 0
            return f"이번 달 평균 실천율 {avg_rate:.0f}%! 꾸준히 성장하고 있어요. 💪"
