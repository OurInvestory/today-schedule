# 오늘의 일정

> watsonx.ai 기반 대학생 맞춤형 AI 학업 스케줄 도우미

## 📌 프로젝트 소개

대학생이 자연어로 입력한 할 일(과제, 시험, 팀플, 대외활동 등)을 AI가 자동으로 분석·분류하고, 중요도와 마감기한을 고려해 우선순위를 추천하는 스마트 학습 도우미입니다.

> 본 프로젝트는 IBM AI Hackathon에서 시작되었으며, 이후 별도의 레포지토리에서 기능 고도화 및 구조 개선을 지속하고 있습니다.

## ✨ 주요 기능

### 🤖 AI 챗봇 (watsonx.ai Llama 3.3 70B)
- **자연어 일정 추가**: "다음 주 수요일까지 자료구조 과제" → AI가 자동 파싱하여 일정 등록
- **다중 일정 처리**: 여러 일정을 한 번에 인식하고 개별 확인/취소 가능
- **알림 예약**: "회의 10분 전에 알림 예약해줘" → 일정 선택 후 푸시 알림 자동 예약
- **우선순위 추천**: "우선순위 높은 일정 추천해줘" → 중요 일정 목록 표시
- **일정 검색/조회**: "이번 주 일정 알려줘", "오늘 할 일 뭐야?"

### 📷 이미지 인식 (Vision AI)
- **시간표 인식**: "시간표 사진에 있는 강의 추가해줘" → 대학 시간표 이미지에서 강의 자동 추출
- **시험/과제 일정표 자동 추출**: 이미지에서 일정을 인식하여 자동 등록
- **공모전 포스터 분석**: 대회 일정, 마감기한, 세부 일정(Sub-task) 자동 생성

### 📅 캘린더 & 시간표
- **월간 캘린더**: 전체 일정 한눈에 확인, 날짜별 일정 표시
- **주간 시간표**: 강의 시간표 관리, 드래그 앤 드롭으로 시간 수정
- **Google Calendar 연동**: 외부 캘린더와 동기화 (설정에서 연결)

### 🔔 스마트 알림 시스템
- **백엔드 알림 API**: 알림 예약, 조회, 확인 처리 (1분 폴링)
- **브라우저 푸시 알림**: Web Notification API 활용
- **마감 임박 알림**: D-day 기반 자동 리마인더
- **AI 데일리 브리핑**: 매일 설정된 시간에 오늘 일정 요약 알림
- **토스 스타일 알림 페이지**: 깔끔한 알림 목록 UI

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

### AI / Cloud
- **IBM watsonx.ai**: Llama 3.3 70B 모델 (자연어 처리, 일정 분석)
- **IBM Cloud**: 클라우드 인프라
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

### 환경 변수 (.env)

```env
# Database
DATABASE_URL=mysql+pymysql://root:0000@db:3306/today_schedule
MYSQL_ROOT_PASSWORD=
MYSQL_DATABASE=today_schedule

# IBM watsonx.ai
WATSONX_API_KEY=your_api_key
WATSONX_URL=https://us-south.ml.cloud.ibm.com/
WATSONX_PROJECT_ID=your_project_id
WATSONX_MODEL_ID=meta-llama/llama-3-3-70b-instruct

# Frontend
VITE_API_BASE_URL=http://localhost:8000/api
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

This project is licensed under the MIT License.
