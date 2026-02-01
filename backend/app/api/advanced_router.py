"""
고급 기능 API 라우터
- 학습 챌린지 추천
- Syllabus OCR
- 학습 리포트
- 공지사항 크롤링
- 외부 서비스 연동
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

from app.db.database import get_db
from app.schemas.common import ResponseDTO

# 서비스 임포트
from app.services.challenge_service import LearningChallengeRecommender
from app.services.syllabus_service import syllabus_ocr_service
from app.services.report_service import LearningReportService
from app.services.notice_crawler_service import NoticeService
from app.services.integration_service import (
    IntegrationManager, NotificationPayload, IntegrationType,
    get_default_integration_manager
)


router = APIRouter(prefix="/api/advanced", tags=["Advanced Features"])

TEST_USER_ID = "7822a162-788d-4f36-9366-c956a68393e1"


# =========================================================
# 학습 챌린지 API
# =========================================================

@router.get("/challenges", response_model=ResponseDTO)
async def get_learning_challenges(
    db: Session = Depends(get_db)
):
    """
    공강 시간 기반 학습 챌린지 추천
    
    주간 시간표를 분석하여 빈 시간에 맞는 학습 활동을 추천합니다.
    """
    try:
        recommender = LearningChallengeRecommender(db, TEST_USER_ID)
        challenges = recommender.generate_challenges()
        
        return ResponseDTO(
            status=200,
            message=f"{len(challenges)}개의 학습 챌린지를 추천합니다.",
            data={
                "challenges": [c.to_dict() for c in challenges],
                "generated_at": datetime.now().isoformat()
            }
        )
    except Exception as e:
        return ResponseDTO(status=500, message=f"챌린지 생성 실패: {str(e)}", data=None)


@router.get("/challenges/today", response_model=ResponseDTO)
async def get_today_challenge(
    db: Session = Depends(get_db)
):
    """
    오늘의 추천 챌린지 (1개)
    """
    try:
        recommender = LearningChallengeRecommender(db, TEST_USER_ID)
        challenge = recommender.get_today_challenge()
        
        if challenge:
            return ResponseDTO(
                status=200,
                message="오늘의 챌린지입니다!",
                data=challenge.to_dict()
            )
        else:
            return ResponseDTO(
                status=200,
                message="오늘은 추천할 챌린지가 없습니다.",
                data=None
            )
    except Exception as e:
        return ResponseDTO(status=500, message=f"챌린지 조회 실패: {str(e)}", data=None)


@router.get("/gap-times", response_model=ResponseDTO)
async def get_gap_times(
    db: Session = Depends(get_db)
):
    """
    이번 주 공강 시간대 조회
    """
    try:
        from app.services.challenge_service import GapTimeAnalyzer
        
        analyzer = GapTimeAnalyzer(db, TEST_USER_ID)
        gap_times = analyzer.find_gap_times(datetime.now())
        
        return ResponseDTO(
            status=200,
            message=f"{len(gap_times)}개의 공강 시간대를 찾았습니다.",
            data={
                "gap_times": [g.to_dict() for g in gap_times],
                "total_minutes": sum(g.duration_minutes for g in gap_times)
            }
        )
    except Exception as e:
        return ResponseDTO(status=500, message=f"공강 시간 분석 실패: {str(e)}", data=None)


# =========================================================
# Syllabus OCR API
# =========================================================

@router.post("/syllabus/analyze", response_model=ResponseDTO)
async def analyze_syllabus(
    file: UploadFile = File(...),
    auto_create: bool = Query(False, description="일정 자동 생성 여부")
):
    """
    강의계획서 분석 및 일정 추출
    
    PDF 또는 이미지를 업로드하면 AI가 한 학기 전체의 시험/과제 일정을 추출합니다.
    """
    try:
        contents = await file.read()
        mime_type = file.content_type or "application/octet-stream"
        
        # PDF vs 이미지 구분
        if "pdf" in mime_type.lower():
            syllabus_info = await syllabus_ocr_service.extract_from_pdf(contents)
        else:
            syllabus_info = await syllabus_ocr_service.extract_from_image(contents, mime_type)
        
        # 일정 payload 생성
        schedule_payloads = syllabus_ocr_service.generate_schedule_payloads(syllabus_info)
        
        return ResponseDTO(
            status=200,
            message=f"[{syllabus_info.course_name}] {len(syllabus_info.schedules)}건의 일정을 추출했습니다.",
            data={
                "course_info": syllabus_info.to_dict(),
                "schedule_payloads": schedule_payloads,
                "auto_create": auto_create
            }
        )
    except Exception as e:
        return ResponseDTO(status=500, message=f"강의계획서 분석 실패: {str(e)}", data=None)


# =========================================================
# 학습 리포트 API
# =========================================================

@router.get("/report/weekly", response_model=ResponseDTO)
async def get_weekly_report(
    date: Optional[str] = Query(None, description="기준 날짜 (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    주간 학습 리포트
    
    예상 시간 vs 실제 완료 시간 비교, 카테고리별 통계, AI 피드백 제공
    """
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d") if date else datetime.now()
        
        service = LearningReportService(db, TEST_USER_ID)
        report = service.generate_weekly_report(target_date)
        
        return ResponseDTO(
            status=200,
            message=f"주간 리포트 (실천율: {report.overall_completion_rate:.0f}%)",
            data=report.to_dict()
        )
    except Exception as e:
        return ResponseDTO(status=500, message=f"리포트 생성 실패: {str(e)}", data=None)


@router.get("/report/monthly", response_model=ResponseDTO)
async def get_monthly_report(
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    월간 학습 리포트
    """
    try:
        service = LearningReportService(db, TEST_USER_ID)
        report = service.generate_monthly_report(year, month)
        
        return ResponseDTO(
            status=200,
            message=f"{report.year}년 {report.month}월 리포트",
            data=report.to_dict()
        )
    except Exception as e:
        return ResponseDTO(status=500, message=f"월간 리포트 생성 실패: {str(e)}", data=None)


# =========================================================
# 공지사항 크롤링 API
# =========================================================

@router.get("/notices", response_model=ResponseDTO)
async def get_university_notices(
    university: str = Query("konkuk", description="대학 코드 (konkuk, yonsei, snu)"),
    fetch_content: bool = Query(False, description="본문 내용 조회 여부")
):
    """
    대학 공지사항 조회 및 AI 분석
    
    중요 공지사항을 자동 필터링하고 요약합니다.
    """
    try:
        service = NoticeService(university)
        important_notices = await service.get_important_notices(
            notice_types=["학사공지"],
            fetch_content=fetch_content
        )
        
        await service.close()
        
        return ResponseDTO(
            status=200,
            message=f"{len(important_notices)}건의 중요 공지사항",
            data={
                "notices": [n.to_dict() for n in important_notices],
                "university": university
            }
        )
    except Exception as e:
        return ResponseDTO(status=500, message=f"공지사항 조회 실패: {str(e)}", data=None)


@router.get("/notices/digest", response_model=ResponseDTO)
async def get_notice_digest(
    university: str = Query("konkuk")
):
    """
    일일 공지사항 다이제스트
    """
    try:
        from app.services.notice_crawler_service import fetch_university_notices
        
        digest = await fetch_university_notices(university)
        
        return ResponseDTO(
            status=200,
            message="일일 공지사항 다이제스트",
            data=digest
        )
    except Exception as e:
        return ResponseDTO(status=500, message=f"다이제스트 생성 실패: {str(e)}", data=None)


# =========================================================
# 외부 서비스 연동 API
# =========================================================

@router.post("/integrations/test", response_model=ResponseDTO)
async def test_integration(
    service: str = Query(..., description="slack, discord, notion"),
    webhook_url: Optional[str] = Query(None),
    api_key: Optional[str] = Query(None),
    database_id: Optional[str] = Query(None)
):
    """
    외부 서비스 연동 테스트
    """
    try:
        manager = IntegrationManager()
        
        if service == "slack" and webhook_url:
            manager.configure_slack(webhook_url)
        elif service == "discord" and webhook_url:
            manager.configure_discord(webhook_url)
        elif service == "notion" and api_key and database_id:
            manager.configure_notion(api_key, database_id)
        else:
            return ResponseDTO(status=400, message="필수 파라미터가 누락되었습니다.", data=None)
        
        # 테스트 알림 전송
        payload = NotificationPayload(
            title="🔔 연동 테스트",
            message="5늘의 일정 앱과 연동이 성공적으로 완료되었습니다!",
            priority="medium"
        )
        
        target = IntegrationType(service)
        results = await manager.send_notification(payload, [target])
        
        await manager.close_all()
        
        success = results.get(service, False)
        
        return ResponseDTO(
            status=200 if success else 500,
            message="연동 테스트 성공!" if success else "연동 테스트 실패",
            data={"service": service, "success": success}
        )
    except Exception as e:
        return ResponseDTO(status=500, message=f"연동 테스트 실패: {str(e)}", data=None)


@router.post("/integrations/send", response_model=ResponseDTO)
async def send_to_integrations(
    title: str,
    message: str,
    services: List[str] = Query(["slack", "discord"]),
    priority: str = Query("medium")
):
    """
    외부 서비스로 알림 전송
    """
    try:
        manager = get_default_integration_manager()
        
        payload = NotificationPayload(
            title=title,
            message=message,
            priority=priority
        )
        
        targets = [IntegrationType(s) for s in services if s in ["slack", "discord", "notion"]]
        results = await manager.send_notification(payload, targets)
        
        await manager.close_all()
        
        return ResponseDTO(
            status=200,
            message="알림 전송 완료",
            data=results
        )
    except Exception as e:
        return ResponseDTO(status=500, message=f"알림 전송 실패: {str(e)}", data=None)


@router.get("/integrations/status", response_model=ResponseDTO)
async def get_integration_status():
    """
    설정된 외부 서비스 연동 상태
    """
    manager = get_default_integration_manager()
    configured = manager.get_configured_integrations()
    
    return ResponseDTO(
        status=200,
        message=f"{len(configured)}개 서비스 연동됨",
        data={
            "configured": configured,
            "available": ["slack", "discord", "notion"]
        }
    )


# =========================================================
# URL 학사일정 파싱 API
# =========================================================

@router.post("/parse-url", response_model=ResponseDTO)
async def parse_url_schedule(
    url: str = Query(..., description="학사일정 또는 공지사항 URL"),
    db: Session = Depends(get_db)
):
    """
    URL에서 학사일정/이벤트 정보 추출
    
    지원 URL:
    - 대학교 학사일정 페이지
    - 공모전 공고 페이지
    - 채용/대외활동 공고
    """
    import aiohttp
    import re
    from bs4 import BeautifulSoup
    import google.generativeai as genai
    import json
    import os
    
    try:
        # 1. URL에서 HTML 가져오기
        async with aiohttp.ClientSession() as session:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            async with session.get(url, headers=headers, timeout=30) as response:
                if response.status != 200:
                    return ResponseDTO(
                        status=400,
                        message=f"URL 접근 실패: HTTP {response.status}",
                        data=None
                    )
                html = await response.text()
        
        # 2. HTML 파싱하여 텍스트 추출
        soup = BeautifulSoup(html, 'html.parser')
        
        # 불필요한 태그 제거
        for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            tag.decompose()
        
        # 본문 텍스트 추출 (최대 5000자)
        text = soup.get_text(separator='\n', strip=True)[:5000]
        title = soup.title.string if soup.title else "제목 없음"
        
        # 3. Gemini로 일정 정보 추출
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel(
            model_name=os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash"),
            generation_config={"temperature": 0.1, "response_mime_type": "application/json"}
        )
        
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        prompt = f"""
        현재 날짜: {today_str}
        페이지 제목: {title}
        URL: {url}
        
        아래 웹페이지 내용에서 일정 정보를 추출해주세요.
        
        [추출 대상]
        - 학사일정 (수강신청, 개강, 휴강, 시험기간 등)
        - 공모전/대회 마감일
        - 채용/대외활동 마감일
        - 행사 일정
        
        [웹페이지 내용]
        {text}
        
        [출력 형식 - JSON]
        {{
            "schedules": [
                {{
                    "title": "일정 제목",
                    "category": "class|exam|assignment|contest|activity|other",
                    "start_at": "YYYY-MM-DDTHH:MM:SS",  // 시작일시 (없으면 null)
                    "end_at": "YYYY-MM-DDTHH:MM:SS",    // 마감일시 (필수)
                    "description": "상세 설명",
                    "priority_score": 5  // 1-10 중요도
                }}
            ],
            "summary": "페이지 요약 (1-2문장)",
            "source_type": "academic_calendar|contest|job|event|other"
        }}
        
        주의:
        - 날짜가 불명확하면 현재 연도({datetime.now().year}) 기준으로 추정
        - 시간이 없으면 23:59:59로 설정
        - 이미 지난 일정은 제외
        """
        
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        
        schedules = result.get("schedules", [])
        summary = result.get("summary", "")
        source_type = result.get("source_type", "other")
        
        # 4. 일정 데이터 정리
        parsed_schedules = []
        for s in schedules:
            parsed_schedules.append({
                "title": s.get("title", ""),
                "category": s.get("category", "other"),
                "start_at": s.get("start_at"),
                "end_at": s.get("end_at"),
                "description": s.get("description", ""),
                "priority_score": s.get("priority_score", 5),
                "source": url
            })
        
        return ResponseDTO(
            status=200,
            message=f"URL에서 {len(parsed_schedules)}건의 일정을 발견했습니다.",
            data={
                "schedules": parsed_schedules,
                "summary": summary,
                "source_type": source_type,
                "source_url": url,
                "page_title": title
            }
        )
        
    except aiohttp.ClientError as e:
        return ResponseDTO(status=400, message=f"URL 접근 실패: {str(e)}", data=None)
    except json.JSONDecodeError as e:
        return ResponseDTO(status=500, message=f"AI 응답 파싱 실패: {str(e)}", data=None)
    except Exception as e:
        return ResponseDTO(status=500, message=f"URL 파싱 실패: {str(e)}", data=None)
