"""
학교 공지사항 크롤링 및 AI 파싱 서비스
- 대학교 홈페이지 크롤링
- AI 기반 중요 공지 필터링
- 일정에 영향 주는 내용 자동 추출
"""

import os
import json
import re
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")

genai.configure(api_key=GOOGLE_API_KEY)


@dataclass
class Notice:
    """공지사항"""
    title: str
    url: str
    date: datetime
    content: Optional[str]
    source: str  # 학사공지, 장학공지 등
    
    def to_dict(self):
        return {
            "title": self.title,
            "url": self.url,
            "date": self.date.strftime("%Y-%m-%d"),
            "content": self.content,
            "source": self.source
        }


@dataclass
class ImportantNotice:
    """중요 공지 (AI 분석 결과)"""
    notice: Notice
    importance_level: str  # critical, high, medium, low
    category: str  # 휴강, 성적, 수강신청, 장학금, 행사, 기타
    summary: str
    action_required: bool
    deadline: Optional[datetime]
    affects_schedule: bool
    suggested_action: Optional[str]
    
    def to_dict(self):
        return {
            "notice": self.notice.to_dict(),
            "importance_level": self.importance_level,
            "category": self.category,
            "summary": self.summary,
            "action_required": self.action_required,
            "deadline": self.deadline.strftime("%Y-%m-%d") if self.deadline else None,
            "affects_schedule": self.affects_schedule,
            "suggested_action": self.suggested_action
        }


class UniversityNoticeConfig:
    """대학별 크롤링 설정"""
    
    # 샘플 대학 설정 (실제 사용 시 확장)
    UNIVERSITIES = {
        "konkuk": {
            "name": "건국대학교",
            "base_url": "https://www.konkuk.ac.kr",
            "notice_urls": {
                "학사공지": "/do/MessageBoard/ArticleList.do?forum=notice",
                "장학공지": "/do/MessageBoard/ArticleList.do?forum=scholarship"
            },
            "selectors": {
                "list": "table.board-list tbody tr",
                "title": "td.subject a",
                "date": "td.date",
                "link_prefix": "/do/MessageBoard/ArticleRead.do"
            }
        },
        "yonsei": {
            "name": "연세대학교",
            "base_url": "https://www.yonsei.ac.kr",
            "notice_urls": {
                "학사공지": "/sc/support/notice.jsp"
            },
            "selectors": {
                "list": "ul.board-list li",
                "title": "a.title",
                "date": "span.date"
            }
        },
        "snu": {
            "name": "서울대학교",
            "base_url": "https://www.snu.ac.kr",
            "notice_urls": {
                "학사공지": "/snunow/notice/gennotice"
            },
            "selectors": {
                "list": "ul.list-container li",
                "title": "a",
                "date": "span.date"
            }
        },
        # 더 많은 대학 추가 가능
        "custom": {
            "name": "사용자 지정",
            "base_url": "",
            "notice_urls": {},
            "selectors": {}
        }
    }
    
    @classmethod
    def get_config(cls, university_code: str) -> dict:
        return cls.UNIVERSITIES.get(university_code, cls.UNIVERSITIES["custom"])


class NoticeCrawler:
    """공지사항 크롤러"""
    
    def __init__(self, university_code: str = "konkuk"):
        self.config = UniversityNoticeConfig.get_config(university_code)
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
    
    async def crawl_notices(self, notice_type: str = "학사공지", limit: int = 20) -> List[Notice]:
        """공지사항 크롤링"""
        notices = []
        
        url_path = self.config["notice_urls"].get(notice_type)
        if not url_path:
            return notices
        
        full_url = urljoin(self.config["base_url"], url_path)
        
        try:
            response = await self.client.get(full_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            selectors = self.config["selectors"]
            
            items = soup.select(selectors["list"])[:limit]
            
            for item in items:
                try:
                    # 제목과 링크
                    title_elem = item.select_one(selectors["title"])
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    link = title_elem.get("href", "")
                    if link and not link.startswith("http"):
                        link = urljoin(self.config["base_url"], link)
                    
                    # 날짜
                    date_elem = item.select_one(selectors["date"])
                    date_str = date_elem.get_text(strip=True) if date_elem else ""
                    date = self._parse_date(date_str)
                    
                    notices.append(Notice(
                        title=title,
                        url=link,
                        date=date,
                        content=None,
                        source=notice_type
                    ))
                except Exception as e:
                    print(f"Notice parse error: {e}")
                    continue
            
        except Exception as e:
            print(f"Crawl error: {e}")
        
        return notices
    
    async def get_notice_content(self, notice: Notice) -> str:
        """공지사항 본문 조회"""
        try:
            response = await self.client.get(notice.url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 본문 영역 찾기 (일반적인 선택자들)
            content_selectors = [
                "div.board-content",
                "div.view-content",
                "div.content-view",
                "div.article-body",
                "td.content"
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    return content_elem.get_text(strip=True)[:2000]  # 최대 2000자
            
            return ""
        except Exception as e:
            print(f"Content fetch error: {e}")
            return ""
    
    def _parse_date(self, date_str: str) -> datetime:
        """날짜 파싱"""
        # 다양한 날짜 형식 처리
        patterns = [
            r"(\d{4})[.-](\d{1,2})[.-](\d{1,2})",  # 2026-01-31 or 2026.01.31
            r"(\d{1,2})[.-](\d{1,2})",  # 01-31 (올해로 가정)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_str)
            if match:
                groups = match.groups()
                if len(groups) == 3:
                    return datetime(int(groups[0]), int(groups[1]), int(groups[2]))
                elif len(groups) == 2:
                    return datetime(datetime.now().year, int(groups[0]), int(groups[1]))
        
        return datetime.now()
    
    async def close(self):
        await self.client.aclose()


class NoticeAnalyzer:
    """공지사항 AI 분석기"""
    
    def __init__(self):
        self.model = genai.GenerativeModel(
            model_name=GEMINI_MODEL_NAME,
            generation_config={
                "temperature": 0.3,
                "response_mime_type": "application/json"
            }
        )
    
    async def analyze_notices(self, notices: List[Notice]) -> List[ImportantNotice]:
        """공지사항 일괄 분석"""
        if not notices:
            return []
        
        # 공지 데이터 준비
        notice_data = [
            {
                "index": i,
                "title": n.title,
                "date": n.date.strftime("%Y-%m-%d"),
                "content": n.content[:500] if n.content else "",
                "source": n.source
            }
            for i, n in enumerate(notices)
        ]
        
        prompt = f"""
        대학 공지사항을 분석하여 학생 일정에 영향을 주는 중요한 공지를 식별해주세요.
        
        현재 날짜: {datetime.now().strftime("%Y-%m-%d")}
        
        [공지사항 목록]
        {json.dumps(notice_data, ensure_ascii=False)}
        
        [분석 기준]
        - 휴강, 보강: 수업 일정 변경
        - 성적 확인/이의신청 기간: 중요 마감
        - 수강신청/변경 기간: 매우 중요
        - 장학금 신청: 마감일 중요
        - 시험 관련: 일정 영향
        - 행사/특강: 선택적
        
        [중요도 레벨]
        - critical: 수강신청, 성적 이의신청 등 기한 중요
        - high: 휴강, 보강, 시험 변경
        - medium: 장학금, 행사
        - low: 일반 안내
        
        [OUTPUT JSON FORMAT]
        {{
            "important_notices": [
                {{
                    "index": 0,
                    "importance_level": "critical|high|medium|low",
                    "category": "휴강|보강|성적|수강신청|장학금|시험|행사|기타",
                    "summary": "한 줄 요약",
                    "action_required": true|false,
                    "deadline": "YYYY-MM-DD 또는 null",
                    "affects_schedule": true|false,
                    "suggested_action": "추천 행동 또는 null"
                }}
            ]
        }}
        
        중요도 medium 이상만 포함해주세요.
        """
        
        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            
            important_notices = []
            for item in result.get("important_notices", []):
                idx = item.get("index", 0)
                if idx < len(notices):
                    deadline = None
                    if item.get("deadline"):
                        try:
                            deadline = datetime.strptime(item["deadline"], "%Y-%m-%d")
                        except:
                            pass
                    
                    important_notices.append(ImportantNotice(
                        notice=notices[idx],
                        importance_level=item.get("importance_level", "medium"),
                        category=item.get("category", "기타"),
                        summary=item.get("summary", notices[idx].title),
                        action_required=item.get("action_required", False),
                        deadline=deadline,
                        affects_schedule=item.get("affects_schedule", False),
                        suggested_action=item.get("suggested_action")
                    ))
            
            return important_notices
            
        except Exception as e:
            print(f"Notice analysis error: {e}")
            return []
    
    async def summarize_for_user(self, important_notices: List[ImportantNotice]) -> str:
        """사용자용 요약 메시지 생성"""
        if not important_notices:
            return "📢 이번 주 중요 공지사항이 없습니다."
        
        # 중요도별 분류
        critical = [n for n in important_notices if n.importance_level == "critical"]
        high = [n for n in important_notices if n.importance_level == "high"]
        
        summary_parts = ["📢 **중요 공지사항 알림**\n"]
        
        if critical:
            summary_parts.append("🚨 **긴급**")
            for n in critical:
                deadline_str = f" (마감: {n.deadline.strftime('%m/%d')})" if n.deadline else ""
                summary_parts.append(f"- {n.summary}{deadline_str}")
            summary_parts.append("")
        
        if high:
            summary_parts.append("⚠️ **중요**")
            for n in high:
                summary_parts.append(f"- {n.summary}")
        
        return "\n".join(summary_parts)


class NoticeService:
    """공지사항 통합 서비스"""
    
    def __init__(self, university_code: str = "konkuk"):
        self.crawler = NoticeCrawler(university_code)
        self.analyzer = NoticeAnalyzer()
    
    async def get_important_notices(
        self, 
        notice_types: List[str] = None,
        fetch_content: bool = False
    ) -> List[ImportantNotice]:
        """중요 공지사항 조회"""
        if notice_types is None:
            notice_types = ["학사공지"]
        
        all_notices = []
        
        for notice_type in notice_types:
            notices = await self.crawler.crawl_notices(notice_type)
            
            # 최근 2주 이내 공지만
            cutoff = datetime.now() - timedelta(days=14)
            notices = [n for n in notices if n.date >= cutoff]
            
            # 본문 조회 (선택적)
            if fetch_content:
                for notice in notices[:10]:  # 최대 10개만
                    notice.content = await self.crawler.get_notice_content(notice)
            
            all_notices.extend(notices)
        
        # AI 분석
        important = await self.analyzer.analyze_notices(all_notices)
        
        # 중요도 순 정렬
        importance_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        important.sort(key=lambda x: importance_order.get(x.importance_level, 3))
        
        return important
    
    async def get_daily_digest(self) -> Dict:
        """일일 공지 다이제스트"""
        important = await self.get_important_notices(
            notice_types=["학사공지", "장학공지"],
            fetch_content=True
        )
        
        summary = await self.analyzer.summarize_for_user(important)
        
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "summary": summary,
            "notices": [n.to_dict() for n in important],
            "total_count": len(important),
            "action_required_count": sum(1 for n in important if n.action_required)
        }
    
    async def close(self):
        await self.crawler.close()


# 편의 함수
async def fetch_university_notices(university_code: str = "konkuk") -> Dict:
    """대학 공지사항 조회 (편의 함수)"""
    service = NoticeService(university_code)
    try:
        return await service.get_daily_digest()
    finally:
        await service.close()
