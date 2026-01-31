# 5늘의 일정

> Google Gemini AI 기반 대학생 맞춤형 AI 학업 스케줄 도우미

## 📌 프로젝트 소개

대학생이 자연어로 입력한 할 일(과제, 시험, 팀플, 대외활동 등)을 AI가 자동으로 분석·분류하고, 중요도와 마감기한을 고려해 우선순위를 추천하는 스마트 학습 도우미입니다.

> 본 프로젝트는 IBM AI Hackathon에서 시작되었으며, 이후 별도의 레포지토리에서 기능 고도화 및 구조 개선을 지속하고 있습니다.

## ✨ 주요 기능

### 🤖 AI 챗봇 (Google Gemini)
- **자연어 일정 추가**: "다음 주 수요일까지 자료구조 과제" → AI가 자동 파싱하여 일정 등록
- **다중 일정 처리**: 여러 일정을 한 번에 인식하고 개별 확인/취소 가능
- **알림 예약**: "회의 10분 전에 알림 예약해줘" → 일정 선택 후 푸시 알림 자동 예약
- **우선순위 추천**: "우선순위 높은 일정 추천해줘" → 중요 일정 목록 표시
- **일정 검색/조회**: "이번 주 일정 알려줘", "오늘 할 일 뭐야?"

### 📷 이미지 인식 (Vision AI)
- **시간표 인식**: "시간표 사진에 있는 강의 추가해줘" → 대학 시간표 이미지에서 강의 자동 추출
- **시험/과제 일정표 자동 추출**: 이미지에서 일정을 인식하여 자동 등록
- **공모전 포스터 분석**: 대회 일정, 마감기한, 세부 일정(Sub-task) 자동 생성
- **📚 Syllabus OCR**: 강의계획서 PDF/이미지에서 한 학기 과제/시험 일정 일괄 추출

### 📅 캘린더 & 시간표
- **월간 캘린더**: 전체 일정 한눈에 확인, 날짜별 일정 표시
- **주간 시간표**: 강의 시간표 관리, 드래그 앤 드롭으로 시간 수정
- **Google Calendar 연동**: 외부 캘린더와 동기화 (설정에서 연결)

### 🔔 스마트 알림 시스템
- **백엔드 알림 API**: 알림 예약, 조회, 확인 처리
- **실시간 SSE 스트리밍**: Server-Sent Events로 실시간 알림 푸시
- **브라우저 푸시 알림**: Web Notification API 활용
- **마감 임박 알림**: D-day 기반 자동 리마인더
- **토스 스타일 알림 페이지**: 깔끔한 알림 목록 UI

### 📊 학습 리포트 & 챌린지
- **AI 기반 우선순위 추천**: 마감기한, 소요 시간, 중요도 분석
- **🎯 공강 시간 학습 챌린지**: 빈 시간대 분석 후 맞춤 학습 활동 추천
- **📈 학습 리포트 대시보드**: 주간/월간 통계, 예상 vs 실제 시간 비교, AI 피드백
- **카테고리 분류**: 수업, 과제, 시험, 팀플, 대외활동 자동 분류
- **Sub-task 관리**: 큰 일정을 세부 작업으로 분할

### 🔗 외부 서비스 연동
- **Slack 연동**: 일정 알림을 Slack 채널로 전송
- **Discord 연동**: 일정 알림을 Discord 서버로 전송  
- **Notion 연동**: 일정을 Notion 데이터베이스와 동기화
- **학교 공지사항 크롤링**: 대학 공지사항 자동 수집 및 AI 중요도 분류

### 🔐 인증 & 보안
- **JWT 기반 인증**: 액세스/리프레시 토큰 관리
- **OAuth 2.0 소셜 로그인**: Google, Kakao 계정 연동
- **RBAC 권한 관리**: 역할 기반 접근 제어 (admin, user)

### 📊 모니터링
- **Prometheus**: 서버 메트릭 수집 (HTTP 요청, 응답 시간, DB 쿼리)
- **Grafana**: 실시간 시각화 대시보드
- **헬스체크**: 시스템 상태 모니터링

## 🛠 기술 스택

### Frontend
- **React 18.2**: UI 라이브러리
- **Vite 5.0**: 빌드 도구 및 개발 서버
- **Axios**: HTTP 클라이언트
- **React Router**: 클라이언트 라우팅
- **Web Notification API**: 브라우저 푸시 알림

### Backend
- **FastAPI**: Python 웹 프레임워크
- **MySQL 8.0**: 관계형 데이터베이스
- **Redis**: 캐싱 및 메시지 브로커
- **Celery**: 비동기 작업 큐
- **Alembic**: 데이터베이스 마이그레이션
- **SQLAlchemy**: ORM
- **Pydantic**: 데이터 검증

### AI / Cloud
- **Google Gemini AI**: 자연어 처리, 이미지 분석, 일정 추천
- **Google Calendar API**: 캘린더 연동
- **OAuth 2.0**: Google, Kakao 소셜 로그인

### DevOps & Monitoring
- **Docker & Docker Compose**: 컨테이너화
- **Prometheus**: 메트릭 수집
- **Grafana**: 시각화 대시보드
- **GitHub**: 버전 관리

## 👥 팀 구성

### 초기 기획 및 MVP 구현 (IBM AI Hackathon)
- IBM AI Hackathon에서 팀 단위로 참여하여 초기 아이디어 도출 및 MVP 구현

### 이후 고도화 및 유지보수
- **[손민주](https://github.com/mango606), [조하영](https://github.com/fanfanduck)**
- **Frontend / Backend / AI 연동을 포함한 Full-Stack 전반을 공동으로 작업**
- 역할 구분 없이 기능 설계, 구현, 리팩토링을 함께 진행

## 🚀 시작하기

### Docker로 실행 (권장)

```bash
# 프로젝트 클론
git clone https://github.com/OurInvestory/today-schedule.git
cd today-schedule

# .env 파일 설정 (아래 환경 변수 참고)

# Docker Compose로 실행
docker-compose up -d --build

# 접속
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API 문서: http://localhost:8000/docs
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin123)
```

### 환경 변수 (.env)

```env
# MySQL Database
MYSQL_ROOT_PASSWORD=root_password
MYSQL_DATABASE=five_schedule_db
MYSQL_USER=five_user
MYSQL_PASSWORD=five_password
DATABASE_URL=mysql+pymysql://five_user:five_password@db:3306/five_schedule_db

# Redis (캐싱 및 Celery 브로커)
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# JWT Authentication
SECRET_KEY=your-secret-key-here

# Google Gemini API
GOOGLE_API_KEY=your_google_api_key
GEMINI_MODEL_NAME=gemini-2.5-flash-preview-04-17

# Google Calendar API (선택)
GOOGLE_CALENDAR_CLIENT_ID=
GOOGLE_CALENDAR_CLIENT_SECRET=

# Frontend
VITE_API_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173

# External Integrations (선택)
SLACK_WEBHOOK_URL=
DISCORD_WEBHOOK_URL=
NOTION_API_KEY=
NOTION_DATABASE_ID=

# Grafana (모니터링)
GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=admin123
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
today-schedule/
├── frontend/               # React 프론트엔드
│   ├── src/
│   │   ├── components/     # 재사용 컴포넌트
│   │   │   ├── calendar/   # 캘린더 관련
│   │   │   ├── chatbot/    # AI 챗봇
│   │   │   ├── common/     # 공통 컴포넌트
│   │   │   ├── layout/     # 레이아웃
│   │   │   └── todo/       # 할 일 관리
│   │   ├── pages/          # 페이지 컴포넌트
│   │   ├── hooks/          # 커스텀 훅
│   │   ├── services/       # API 서비스
│   │   ├── context/        # React Context
│   │   └── utils/          # 유틸리티 함수
│   └── ...
├── backend/                # FastAPI 백엔드
│   ├── app/
│   │   ├── api/            # API 라우터
│   │   ├── core/           # 핵심 기능 (인증, 캐시, Celery, 이벤트버스, 모니터링)
│   │   ├── models/         # SQLAlchemy 모델
│   │   ├── schemas/        # Pydantic 스키마
│   │   ├── services/       # 비즈니스 로직 (챌린지, 리포트, OCR, 크롤러, 연동)
│   │   └── db/             # 데이터베이스 설정
│   ├── alembic/            # DB 마이그레이션
│   └── ...
├── monitoring/             # 모니터링 설정
│   ├── prometheus.yml      # Prometheus 설정
│   └── grafana/
│       └── provisioning/   # Grafana 자동 프로비저닝
│           ├── datasources/
│           └── dashboards/
└── docker-compose.yml      # Docker 설정
```

## 📡 주요 API 엔드포인트

### AI 챗봇 (`/api/chat`)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/chat` | AI 챗봇 메시지 처리 |

### 일정 (`/api/schedules`)
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/schedules` | 일정 목록 조회 |
| POST | `/api/schedules` | 일정 생성 |
| PATCH | `/api/schedules/{id}` | 일정 수정 |
| DELETE | `/api/schedules/{id}` | 일정 삭제 |

### 고급 기능 (`/api/advanced`)
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/advanced/challenges` | 학습 챌린지 추천 |
| GET | `/api/advanced/gap-times` | 공강 시간 분석 |
| POST | `/api/advanced/syllabus/analyze` | Syllabus OCR 분석 |
| GET | `/api/advanced/report/weekly` | 주간 학습 리포트 |
| GET | `/api/advanced/report/monthly` | 월간 학습 리포트 |
| POST | `/api/advanced/notices` | 공지사항 크롤링 |
| GET | `/api/advanced/notices/digest` | 공지사항 다이제스트 |
| POST | `/api/advanced/integrations/send` | 외부 서비스 알림 전송 |

### 인증 (`/api/auth`)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/auth/login` | 로그인 |
| POST | `/api/auth/register` | 회원가입 |
| POST | `/api/auth/refresh` | 토큰 갱신 |
| GET | `/api/auth/google/login` | Google 소셜 로그인 |
| GET | `/api/auth/kakao/login` | Kakao 소셜 로그인 |

### 모니터링
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/metrics` | Prometheus 메트릭 |
| GET | `/api/events/stream` | SSE 이벤트 스트림 |

## 🖥 서비스 포트

| 서비스 | 포트 | 설명 |
|--------|------|------|
| Frontend | 5173 | React 개발 서버 |
| Backend | 8000 | FastAPI 서버 |
| MySQL | 3306 | 데이터베이스 |
| Redis | 6379 | 캐시/메시지 브로커 |
| Prometheus | 9090 | 메트릭 수집 |
| Grafana | 3000 | 시각화 대시보드 |

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

This project is licensed under the MIT License.
