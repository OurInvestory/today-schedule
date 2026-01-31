# 5늘의 일정 - Backend

> FastAPI 기반 AI 학업 스케줄 도우미 백엔드

## 🚀 시작하기

### Docker로 실행 (권장)

```bash
# 프로젝트 루트에서
docker-compose up -d --build
# API 문서: http://localhost:8000/docs
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin123)
```

### 로컬 실행

1. 저장소 클론 및 이동
```bash
git clone https://github.com/OurInvestory/today-schedule.git
cd today-schedule/backend
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
# MySQL Database
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/five_schedule_db

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# JWT Authentication
SECRET_KEY=your-secret-key-change-in-production-very-long-and-secure
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production

# Google Gemini API
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL_NAME=gemini-2.5-flash

# Google OAuth (소셜 로그인)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Kakao OAuth (소셜 로그인)
KAKAO_CLIENT_ID=your_kakao_client_id
KAKAO_CLIENT_SECRET=your_kakao_client_secret

# Frontend
FRONTEND_URL=http://localhost:5173
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
- **Redis**: 캐싱 및 메시지 브로커
- **Celery**: 비동기 작업 큐
- **Alembic**: 데이터베이스 마이그레이션
- **Pydantic**: 데이터 검증
- **Google Gemini AI**: 자연어 처리 및 이미지 분석
- **Prometheus**: 메트릭 수집
- **JWT / OAuth 2.0**: 인증 및 권한 관리

## 📂 프로젝트 구조

```
backend/ 
├── app/                 
│   ├── main.py              # FastAPI 앱 진입점
│   ├── api/                 # API 라우터
│   │   ├── auth_router.py       # 인증/권한 (JWT, OAuth)
│   │   ├── calendar_router.py   # Google Calendar 연동
│   │   ├── chat_router.py       # AI 챗봇 (Gemini)
│   │   ├── events_router.py     # SSE 이벤트 스트림
│   │   ├── lecture_router.py    # 강의/시간표 CRUD
│   │   ├── notification_router.py # 알림 CRUD
│   │   ├── schedule_router.py   # 일정 CRUD
│   │   ├── sub_task_router.py   # 서브태스크 CRUD
│   │   ├── tasks_router.py      # Celery 비동기 작업
│   │   ├── user_router.py       # 사용자
│   │   ├── vision_router.py     # 이미지 분석
│   │   └── advanced_router.py   # 고급 기능 (챌린지, 리포트, OCR 등)
│   ├── core/                # 핵심 기능
│   │   ├── auth.py              # JWT/OAuth 인증
│   │   ├── cache.py             # Redis 캐싱
│   │   ├── celery_app.py        # Celery 설정
│   │   ├── event_bus.py         # Redis Pub/Sub 이벤트 버스
│   │   └── monitoring.py        # Prometheus 메트릭
│   ├── services/            # 비즈니스 로직
│   │   ├── smart_schedule_service.py    # 🆕 AI 스마트 일정 관리
│   │   ├── subtask_recommend_service.py # AI 할일 추천/세분화
│   │   ├── challenge_service.py     # 학습 챌린지 추천
│   │   ├── report_service.py        # 학습 리포트 생성
│   │   ├── syllabus_service.py      # Syllabus OCR
│   │   ├── notice_crawler_service.py # 공지사항 크롤링
│   │   └── integration_service.py   # 외부 서비스 연동
│   ├── db/                  # 데이터베이스
│   │   ├── database.py          # MySQL 연결 설정
│   │   └── seed_data.py         # 시드 데이터
│   ├── models/              # SQLAlchemy 모델
│   │   ├── user.py              # 사용자
│   │   ├── schedule.py          # 일정
│   │   ├── sub_task.py          # 서브태스크
│   │   ├── lecture.py           # 강의
│   │   └── notification.py      # 알림
│   └── schemas/             # Pydantic 스키마
│       ├── common.py            # 공통 응답 DTO
│       ├── schedule.py          # 일정 스키마
│       ├── sub_task.py          # 서브태스크 스키마
│       ├── lecture.py           # 강의 스키마
│       ├── notification.py      # 알림 스키마
│       ├── ai_chat.py           # AI 챗봇 스키마
│       └── calendar.py          # 캘린더 스키마
├── alembic/             # DB 마이그레이션
│   └── versions/        # 마이그레이션 파일들
├── scripts/             # 유틸리티 스크립트
├── .env                 # 환경 변수
├── requirements.txt     # 의존성
└── Dockerfile           # Docker 설정
```

## 📡 주요 API 엔드포인트

### AI 챗봇 (`/api/chat`)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/chat` | AI 챗봇 메시지 처리 (17개 인텐트 지원) |

**지원 인텐트**: `SCHEDULE_MUTATION`, `SCHEDULE_QUERY`, `CLARIFY`, `NOTIFICATION_REQUEST`, `PRIORITY_QUERY`, `SUBTASK_RECOMMEND`, `SCHEDULE_BREAKDOWN`, `GAP_FILL`, `PATTERN_ANALYSIS`, `RECURRING_SCHEDULE`, `AUTO_MODE_TOGGLE`, `SCHEDULE_UPDATE`, `DAILY_BRIEFING`, `WEEKLY_SUMMARY`, `CONFLICT_CHECK`, `SMART_SUGGEST`, `BATCH_CREATE`, `PRIORITY_ADJUST`

### AI 스마트 기능 (`/api/ai`)
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/ai/briefing` | 일일 브리핑 (오늘 일정 요약) |
| GET | `/api/ai/weekly-summary` | 주간 요약 (통계, 완료율) |
| GET | `/api/ai/suggestions` | 컨텍스트 기반 스마트 제안 |
| GET | `/api/ai/conflict-check` | 일정 충돌 확인 |
| POST | `/api/ai/priority-adjust` | 우선순위 자동 조정 |

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
| GET | `/api/notifications/pending` | 발송할 알림 조회 |
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

### 인증 (`/api/auth`)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/auth/login` | JWT 로그인 |
| POST | `/api/auth/register` | 회원가입 |
| POST | `/api/auth/refresh` | 토큰 갱신 |
| GET | `/api/auth/google/login` | Google OAuth 로그인 |
| GET | `/api/auth/kakao/login` | Kakao OAuth 로그인 |
| GET | `/api/auth/me` | 현재 사용자 정보 |

### 고급 기능 (`/api/advanced`)
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/advanced/challenges` | 학습 챌린지 추천 |
| GET | `/api/advanced/challenges/today` | 오늘의 챌린지 |
| GET | `/api/advanced/gap-times` | 공강 시간 분석 |
| POST | `/api/advanced/syllabus/analyze` | Syllabus OCR 분석 |
| GET | `/api/advanced/report/weekly` | 주간 학습 리포트 |
| GET | `/api/advanced/report/monthly` | 월간 학습 리포트 |
| POST | `/api/advanced/notices` | 공지사항 크롤링 |
| GET | `/api/advanced/notices/digest` | 공지사항 다이제스트 |
| POST | `/api/advanced/integrations/test` | 외부 연동 테스트 |
| POST | `/api/advanced/integrations/send` | 외부 서비스 알림 전송 |
| GET | `/api/advanced/integrations/status` | 연동 상태 확인 |

### 비동기 작업 (`/api/tasks`)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/tasks/process` | 비동기 작업 요청 |
| GET | `/api/tasks/{task_id}` | 작업 상태 조회 |

### 이벤트 스트림 (`/api/events`)
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/events/stream` | SSE 실시간 이벤트 |

### 모니터링
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/metrics` | Prometheus 메트릭 |

## 🗄 데이터베이스 스키마

### User (사용자)
- `user_id`: UUID (PK)
- `email`: 이메일
- `password`: 비밀번호 (해시)
- `role`: 권한 (admin, user)

### Schedule (일정)
- `schedule_id`: UUID (PK)
- `user_id`: 사용자 FK
- `title`: 제목
- `category`: 카테고리 (class, assignment, exam, team, activity)
- `type`: 유형 (task, event)
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

### SubTask (서브태스크)
- `sub_task_id`: UUID (PK)
- `schedule_id`: 일정 FK
- `title`: 제목
- `is_completed`: 완료 여부
- `priority`: 우선순위
- `category`: 카테고리

