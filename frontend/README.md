# 5늘의 일정 - Frontend

> React 기반 AI 학업 스케줄 도우미 프론트엔드

## 🚀 실행 방법

### 개발 서버 실행

```bash
# 의존성 설치
npm install

# 개발 서버 실행 (http://localhost:5173)
npm run dev
```

### 프로덕션 빌드

```bash
# 빌드
npm run build

# 빌드된 파일 미리보기
npm run preview
```

### Docker로 실행

```bash
# 프로젝트 루트에서
docker-compose up frontend
```

## 🛠 기술 스택

- **React 18.2**: UI 라이브러리
- **Vite 5.0**: 빌드 도구 및 개발 서버
- **Axios**: HTTP 클라이언트
- **React Router**: 클라이언트 라우팅
- **Web Notification API**: 브라우저 푸시 알림

## ✨ 주요 기능

### 🤖 AI 챗봇
- 자연어로 일정 추가/조회
- 우선순위 높은 일정 추천
- 알림 예약 (일정 선택 후 N분 전 알림)
- 시간표 이미지 분석 및 강의 추가

### 🔔 알림 시스템
- 백엔드 API 폴링 (1분 간격)
- 브라우저 푸시 알림
- AI 데일리 브리핑 (설정 시간에 오늘 일정 알림)
- 토스 스타일 알림 페이지

### 📅 캘린더 & 시간표
- 월간 캘린더 (일정 표시)
- 주간 시간표 (강의 관리)
- Google Calendar 연동

## 📁 프로젝트 구조

```
src/
├── components/           # 재사용 컴포넌트
│   ├── calendar/         # 캘린더 관련 (Calendar, CalendarGrid, MiniCalendar)
│   ├── chatbot/          # AI 챗봇 (ChatbotWindow, ChatInput, ChatMessage)
│   ├── common/           # 공통 UI (Button, Modal, Toast, ErrorBoundary)
│   ├── layout/           # 레이아웃 (Header, BottomNav)
│   └── todo/             # 할 일 목록 (TodoList, TodoItem, TodoInput)
├── context/              # React Context
│   └── ToastContext.js   # 토스트 알림 컨텍스트
├── hooks/                # 커스텀 훅
│   ├── useCalendar.js    # 캘린더 상태 관리
│   ├── useChatbot.js     # 챗봇 상태 관리 (메시지, 액션 처리)
│   ├── useNotification.js# 알림 상태 관리
│   ├── useTimetable.js   # 시간표 상태 관리
│   ├── useToast.js       # 토스트 알림
│   └── useTodo.js        # 할 일 상태 관리
├── pages/                # 페이지 컴포넌트
│   ├── Home.jsx          # 메인 홈 (오늘의 할 일)
│   ├── Archive.jsx       # 아카이브 (완료된 일정)
│   ├── FullCalendar.jsx  # 월간 캘린더
│   ├── Timetable.jsx     # 주간 시간표
│   ├── Notifications.jsx # 알림 목록 (토스 스타일)
│   ├── Settings.jsx      # 설정 (알림, 계정 연결)
│   ├── ScheduleDetail.jsx# 일정 상세
│   └── TaskDetail.jsx    # 할 일 상세
├── services/             # API 서비스
│   ├── api.js            # Axios 인스턴스
│   ├── aiService.js      # AI 챗봇 API (sendChatMessage, analyzeTimetableImage)
│   ├── todoService.js    # 할 일 CRUD API
│   ├── calendarService.js# 캘린더/Google 연동 API
│   ├── lectureService.js # 강의/시간표 API
│   ├── notificationService.js     # 로컬 알림 서비스 (브리핑, 마감 알림)
│   ├── notificationApiService.js  # 백엔드 알림 API (폴링, CRUD)
│   └── subTaskService.js # 서브태스크 API
├── styles/               # 전역 스타일
│   ├── global.css        # 전역 CSS
│   ├── theme.js          # 테마 설정
│   └── variables.css     # CSS 변수
├── utils/                # 유틸리티
│   ├── constants.js      # 상수
│   ├── dateUtils.js      # 날짜 유틸
│   ├── i18n.js           # 다국어 지원
│   └── priorityUtils.js  # 우선순위 계산
├── App.jsx               # 앱 루트 (라우팅, 알림 초기화)
├── App.css               # 앱 스타일
├── main.jsx              # 엔트리 포인트
└── index.css             # 기본 스타일
```

## 📱 주요 페이지

| 경로 | 페이지 | 설명 |
|------|--------|------|
| `/` | Home | 메인 홈, 오늘의 할 일 |
| `/calendar` | FullCalendar | 월간 캘린더 |
| `/timetable` | Timetable | 주간 시간표 |
| `/notifications` | Notifications | 알림 목록 |
| `/settings` | Settings | 설정 |
| `/archive` | Archive | 완료된 일정 |
| `/schedule/:id` | ScheduleDetail | 일정 상세 |
| `/task/:id` | TaskDetail | 할 일 상세 |

## 🔧 환경 변수

`.env` 파일을 생성하고 다음 변수를 설정하세요:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## 📝 코드 스타일

- ESLint 설정 적용
- Prettier 코드 포맷팅
- BEM 네이밍 컨벤션 (CSS)
