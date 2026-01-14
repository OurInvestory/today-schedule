# 5늘의 일정

> watsonx.ai 기반 대학생 맞춤형 AI 학업 스케줄 도우미

## 📌 프로젝트 소개

대학생이 자연어로 입력한 할 일(과제, 시험, 팀플, 대외활동 등)을 AI가 자동으로 분석·분류하고, 중요도와 마감기한을 고려해 우선순위를 추천하는 스마트 학습 도우미입니다.

## ✨ 주요 기능

### 🤖 AI 챗봇 (watsonx.ai 기반)
- **자연어 일정 추가**: "다음 주 수요일까지 자료구조 과제" → AI가 자동 파싱하여 일정 등록
- **다중 일정 처리**: 여러 일정을 한 번에 인식하고 개별 확인/취소 가능
- **알림 예약**: "내일 오전 9시에 알려줘" → 푸시 알림 자동 예약
- **일정 검색/조회**: "이번 주 일정 알려줘", "오늘 할 일 뭐야?"

### 📷 이미지 인식 (Vision AI)
- **시험/과제 일정표 자동 추출**: 이미지에서 일정을 인식하여 자동 등록
- **공모전 포스터 분석**: 대회 일정, 마감기한, 세부 일정(Sub-task) 자동 생성
- **시간표 인식**: 대학 시간표 이미지 → 주간 강의 시간표 자동 등록

### 📅 캘린더 & 시간표
- **월간 캘린더**: 전체 일정 한눈에 확인
- **주간 시간표**: 강의 시간표 관리, 다중 시간대 지원 (예: 월/목 다른 시간)
- **Google Calendar 연동**: 외부 캘린더와 동기화

### 🔔 스마트 알림
- **마감 임박 알림**: D-day 기반 자동 리마인더
- **커스텀 알림**: 원하는 시간에 맞춤 알림 설정

### 📊 우선순위 관리
- **AI 기반 우선순위 추천**: 마감기한, 소요 시간, 중요도 분석
- **카테고리 분류**: 과제, 시험, 팀플, 대외활동 자동 분류
- **Sub-task 관리**: 큰 일정을 세부 작업으로 분할

## 🛠 기술 스택

### Frontend
- **React 18.2**: UI 라이브러리
- **Vite 5.0**: 빌드 도구 및 개발 서버
- **Axios**: HTTP 클라이언트
- **date-fns**: 날짜 처리

### Backend
- **FastAPI**: Python 웹 프레임워크
- **MySQL**: 관계형 데이터베이스
- **Alembic**: 데이터베이스 마이그레이션
- **SQLAlchemy**: ORM

### AI / Cloud
- **IBM watsonx.ai**: 자연어 처리, 일정 분석
- **IBM Cloud Functions**: 서버리스 백엔드
- **Google Calendar API**: 캘린더 연동

### DevOps
- **Docker & Docker Compose**: 컨테이너화
- **GitHub Actions**: CI/CD

## 👥 팀 구성

| 역할 | 이름 |
|------|------|
| Project Manager | 손민주 |
| Prompt Engineer & Domain Expert | 천지우 |
| Frontend Developer | 김혜영, 손민주 |
| Backend Developer & AI Engineer | 김진영, 조하영 |

## 🚀 시작하기

### Docker로 실행 (권장)

```bash
# 프로젝트 클론
git clone https://github.com/ibm-ai-hackathon/five-today-schedule.git
cd five-today-schedule

# Docker Compose로 실행
docker-compose up --build
```

### 개별 실행

#### Frontend
```bash
cd frontend
npm install
npm run dev
# http://localhost:5173 에서 확인
```

#### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
# http://localhost:8000 에서 확인
```

## 📁 프로젝트 구조

```
five-today-schedule/
├── frontend/           # React 프론트엔드
│   ├── src/
│   │   ├── components/ # 재사용 컴포넌트
│   │   ├── pages/      # 페이지 컴포넌트
│   │   ├── hooks/      # 커스텀 훅
│   │   ├── services/   # API 서비스
│   │   └── utils/      # 유틸리티 함수
│   └── ...
├── backend/            # FastAPI 백엔드
│   ├── app/
│   │   ├── api/        # API 라우터
│   │   ├── models/     # 데이터베이스 모델
│   │   ├── schemas/    # Pydantic 스키마
│   │   └── db/         # 데이터베이스 설정
│   └── ...
├── docs/               # 문서
└── docker-compose.yml  # Docker 설정
```

## 📝 커밋 컨벤션

| 타입 | 설명 |
|------|------|
| `feat` | 새로운 기능 추가 |
| `fix` | 버그 수정 |
| `docs` | 문서 수정 |
| `style` | 코드 포맷팅 |
| `refactor` | 코드 리팩토링 |
| `test` | 테스트 코드 |
| `chore` | 빌드, 패키지 설정 |

## 📄 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.