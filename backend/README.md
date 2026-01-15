# 5늘의 일정 - Backend

> FastAPI 기반 AI 학업 스케줄 도우미 백엔드

## 🚀 시작하기

### Docker로 실행 (권장)

```bash
# 프로젝트 루트에서
docker-compose up -d --build
# API 문서: http://localhost:8000/docs
```

### 로컬 실행

1. 저장소 클론 및 이동
```bash
git clone https://github.com/ibm-ai-hackathon/five-today-schedule.git
cd five-today-schedule/backend
```

2. 가상 환경 설정 및 패키지 설치
```bash
# 가상 환경 설정
python -m venv venv

# 가상 환경 활성화
.\venv\Scripts\activate       # Windows
source venv/bin/activate      # Mac/Linux

# 필수 패키지 설치
pip install -r requirements.txt
```

3. .env 파일 설정
```env
DATABASE_URL=mysql+pymysql://root:1869@localhost:3306/five_today_schedule
WATSONX_API_KEY=your_api_key
WATSONX_URL=https://us-south.ml.cloud.ibm.com/
WATSONX_PROJECT_ID=your_project_id
WATSONX_MODEL_ID=meta-llama/llama-3-3-70b-instruct
```

4. DB 마이그레이션 (Alembic)
```bash
alembic upgrade head
```

5. 서버 실행
```bash
uvicorn app.main:app --reload
# http://localhost:8000/docs 에서 API 문서 확인
```

## 🛠 기술 스택

- **FastAPI**: Python 웹 프레임워크
- **SQLAlchemy**: ORM
- **MySQL 8.0**: 관계형 데이터베이스
- **Alembic**: 데이터베이스 마이그레이션
- **Pydantic**: 데이터 검증
- **IBM watsonx.ai**: Llama 3.3 70B (자연어 처리)

## 📂 프로젝트 구조

```
backend/ 
├── app/                 
│   ├── main.py          # FastAPI 앱 진입점
│   ├── api/             # API 라우터
│   │   ├── calendar_router.py    # Google Calendar 연동
│   │   ├── chat_router.py        # AI 챗봇 (watsonx.ai)
│   │   ├── lecture_router.py     # 강의/시간표 CRUD
│   │   ├── notification_router.py# 알림 CRUD
│   │   ├── schedule_router.py    # 일정 CRUD
│   │   ├── sub_task_router.py    # 서브태스크 CRUD
│   │   ├── user_router.py        # 사용자
│   │   └── vision_router.py      # 이미지 분석
│   ├── db/              # 데이터베이스
│   │   ├── database.py  # MySQL 연결 설정
│   │   └── seed_data.py # 시드 데이터 (데모용)
│   ├── models/          # SQLAlchemy 모델
│   │   ├── user.py      # 사용자
│   │   ├── schedule.py  # 일정
│   │   ├── sub_task.py  # 서브태스크
│   │   ├── lecture.py   # 강의
│   │   └── notification.py # 알림
│   ├── schemas/         # Pydantic 스키마
│   │   ├── common.py    # 공통 응답 DTO
│   │   ├── schedule.py  # 일정 스키마
│   │   ├── sub_task.py  # 서브태스크 스키마
│   │   ├── lecture.py   # 강의 스키마
│   │   ├── notification.py # 알림 스키마
│   │   ├── ai_chat.py   # AI 챗봇 스키마
│   │   └── calendar.py  # 캘린더 스키마
│   └── crud/            # DB 처리 로직
├── alembic/             # DB 마이그레이션
│   └── versions/        # 마이그레이션 파일들
├── scripts/             # 유틸리티 스크립트
├── tests/               # 테스트
├── .env                 # 환경 변수
├── requirements.txt     # 의존성
└── Dockerfile           # Docker 설정
```

## 📡 주요 API 엔드포인트

### AI 챗봇 (`/api/chat`)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/chat` | AI 챗봇 메시지 처리 (자연어 → 일정/알림) |

### 일정 (`/api/schedules`)
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/schedules` | 일정 목록 조회 (기간별) |
| POST | `/api/schedules` | 일정 생성 |
| GET | `/api/schedules/{id}` | 일정 상세 조회 |
| PATCH | `/api/schedules/{id}` | 일정 수정 |
| DELETE | `/api/schedules/{id}` | 일정 삭제 |

### 알림 (`/api/notifications`)
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/notifications` | 내 알림 목록 조회 |
| POST | `/api/notifications` | 알림 생성 |
| GET | `/api/notifications/pending` | 발송할 알림 조회 (폴링용) |
| POST | `/api/notifications/check` | 알림 확인 처리 |
| DELETE | `/api/notifications/{id}` | 알림 삭제 |

### 강의 (`/api/lectures`)
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/lectures` | 강의 목록 조회 |
| POST | `/api/lectures` | 강의 생성 |
| POST | `/api/lectures/bulk` | 강의 일괄 생성 |
| PATCH | `/api/lectures/{id}` | 강의 수정 |
| DELETE | `/api/lectures/{id}` | 강의 삭제 |

### 이미지 분석 (`/api/vision`)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/vision/analyze` | 이미지에서 일정 추출 |
| POST | `/api/vision/timetable` | 시간표 이미지 분석 |

## 🗄 데이터베이스 스키마

### User (사용자)
- `user_id`: UUID (PK)
- `email`: 이메일
- `password`: 비밀번호

### Schedule (일정)
- `schedule_id`: UUID (PK)
- `user_id`: 사용자 FK
- `title`: 제목
- `category`: 카테고리 (class, assignment, exam, team, activity)
- `start_at`, `end_at`: 시작/종료 시간
- `priority_score`: 우선순위 점수 (1-10)
- `estimated_minute`: 예상 소요 시간

### Notification (알림)
- `notification_id`: UUID (PK)
- `user_id`: 사용자 FK
- `schedule_id`: 일정 FK (nullable)
- `message`: 알림 메시지
- `notify_at`: 알림 시간
- `is_sent`: 발송 여부
- `is_checked`: 확인 여부

### Lecture (강의)
- `lecture_id`: UUID (PK)
- `user_id`: 사용자 FK
- `name`: 강의명
- `professor`: 교수명
- `location`: 장소
- `day_of_week`: 요일
- `start_time`, `end_time`: 시작/종료 시간
