# 오늘의 일정

> Gemini AI 기반 대학생 맞춤형 AI 학업 스케줄 도우미

## 📌 프로젝트 소개

대학생이 자연어로 입력한 할 일(과제, 시험, 팀플, 대외활동 등)을 AI가 자동으로 분석·분류하고, 중요도와 마감기한을 고려해 우선순위를 추천하는 스마트 학습 도우미입니다.

> 본 프로젝트는 IBM AI Hackathon에서 시작되었으며, 이후 Gemini API로 마이그레이션하여 기능 고도화 및 구조 개선을 지속하고 있습니다.

## ✨ 주요 기능

### 🔐 회원 인증 시스템
- **회원가입/로그인**: JWT 기반 인증, bcrypt 비밀번호 암호화
- **프로필 관리**: 이름, 학교, 학과, 학년 정보 관리
- **비밀번호 변경**: 현재 비밀번호 확인 후 변경
- **계정 삭제**: 비밀번호 확인 후 계정 및 데이터 영구 삭제

### 🤖 AI 챗봇 (Gemini AI)
- **자연어 일정 추가**: "다음 주 수요일까지 자료구조 과제" → AI가 자동 파싱하여 일정 등록
- **다중 일정 처리**: 여러 일정을 한 번에 인식하고 개별 확인/취소 가능
- **알림 예약**: "회의 10분 전에 알림 예약해줘" → 일정 선택 후 푸시 알림 자동 예약
- **우선순위 추천**: "우선순위 높은 일정 추천해줘" → 중요 일정 목록 표시
- **일정 검색/조회**: "이번 주 일정 알려줘", "오늘 할 일 뭐야?"

### 📷 이미지 인식 (Vision AI)
- **시간표 인식**: 대학 시간표 이미지에서 강의 자동 추출
- **시험/과제 일정표 자동 추출**: 이미지에서 일정을 인식하여 자동 등록
- **공모전 포스터 분석**: 대회 일정, 마감기한, 세부 일정(Sub-task) 자동 생성

### 📅 캘린더 & 시간표
- **월간 캘린더**: 전체 일정 한눈에 확인, 날짜별 일정 표시
- **주간 시간표**: 강의 시간표 관리
- **Google Calendar 연동**: 외부 캘린더와 동기화 (설정에서 연결)

### 🔔 스마트 알림 시스템
- **백엔드 알림 API**: 알림 예약, 조회, 확인 처리
- **브라우저 푸시 알림**: Web Notification API 활용
- **마감 임박 알림**: D-day 기반 자동 리마인더
- **AI 데일리 브리핑**: 매일 설정된 시간에 오늘 일정 요약 알림

### ⚙️ 설정
- **다국어 지원**: 한국어/영어 UI 전환
- **테마**: 라이트/다크/시스템 설정
- **알림 설정**: 푸시 알림, 알림음, 진동, 방해 금지 모드
- **개인정보 설정**: 자동 잠금, 사용 분석 데이터, 오류 보고서

### 📊 우선순위 관리
- **AI 기반 우선순위 추천**: 마감기한, 소요 시간, 중요도 분석
- **카테고리 분류**: 수업, 과제, 시험, 팀플, 대외활동 자동 분류
- **Sub-task 관리**: 큰 일정을 세부 작업으로 분할

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
- **Alembic**: 데이터베이스 마이그레이션
- **SQLAlchemy**: ORM
- **Pydantic**: 데이터 검증
- **JWT (PyJWT)**: 인증 토큰
- **bcrypt**: 비밀번호 암호화

### AI / Cloud
- **Google Gemini AI**: 자연어 처리, 일정 분석, 이미지 인식
- **Google Calendar API**: 캘린더 연동

### DevOps
- **Docker & Docker Compose**: 컨테이너화 (frontend, backend, db)
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
```

### 테스트 계정
```
이메일: demo@five-today.com
비밀번호: demo1234
```

### 환경 변수 (.env)

```env
# Database
DATABASE_URL=mysql+pymysql://root:0000@db:3306/today_schedule
MYSQL_ROOT_PASSWORD=0000
MYSQL_DATABASE=today_schedule

# Google Gemini AI
GOOGLE_API_KEY=your_google_api_key
GEMINI_MODEL_NAME=gemini-2.0-flash

# JWT 인증
SECRET_KEY=your-secret-key-change-in-production

# Google Calendar (선택)
GOOGLE_CALENDAR_CLIENT_ID=your_client_id
GOOGLE_CALENDAR_CLIENT_SECRET=your_client_secret

# Frontend
VITE_API_URL=http://localhost:8000
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
alembic upgrade head  # DB 마이그레이션
uvicorn app.main:app --reload
# http://localhost:8000 에서 확인
```

## 📁 프로젝트 구조

```
today-schedule/
├── .github/            # GitHub 템플릿
│   ├── ISSUE_TEMPLATE/
│   └── PULL_REQUEST_TEMPLATE.md
├── frontend/           # React 프론트엔드
│   ├── src/
│   │   ├── components/ # 재사용 컴포넌트
│   │   ├── pages/      # 페이지 컴포넌트
│   │   ├── hooks/      # 커스텀 훅
│   │   ├── services/   # API 서비스
│   │   ├── context/    # React Context
│   │   └── utils/      # 유틸리티 함수 (i18n 등)
│   └── ...
├── backend/            # FastAPI 백엔드
│   ├── app/
│   │   ├── api/        # API 라우터
│   │   ├── models/     # 데이터베이스 모델
│   │   ├── schemas/    # Pydantic 스키마
│   │   ├── core/       # 인증/보안 모듈
│   │   └── db/         # 데이터베이스 설정
│   ├── alembic/        # DB 마이그레이션
│   └── ...
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

This project is licensed under the MIT License.
