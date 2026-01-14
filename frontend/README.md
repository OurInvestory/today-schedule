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
- **date-fns**: 날짜 처리
- **React Router**: 클라이언트 라우팅

## 📁 프로젝트 구조

```
src/
├── api/                  # API 설정
├── assets/               # 이미지, 아이콘
├── components/           # 재사용 컴포넌트
│   ├── calendar/         # 캘린더 관련
│   ├── chatbot/          # AI 챗봇
│   ├── common/           # 공통 UI (Button, Modal, Input 등)
│   ├── layout/           # 레이아웃 (Header, Footer)
│   ├── notification/     # 알림
│   ├── priority/         # 우선순위
│   ├── schedule/         # 일정
│   ├── settings/         # 설정
│   └── todo/             # 할 일 목록
├── context/              # React Context
├── hooks/                # 커스텀 훅
│   ├── useCalendar.js    # 캘린더 상태 관리
│   ├── useChatbot.js     # 챗봇 상태 관리
│   ├── useNotification.js# 알림 상태 관리
│   ├── useTimetable.js   # 시간표 상태 관리
│   ├── useToast.js       # 토스트 알림
│   └── useTodo.js        # 할 일 상태 관리
├── pages/                # 페이지 컴포넌트
│   ├── Home.jsx          # 메인 홈
│   ├── Archive.jsx       # 아카이브
│   ├── FullCalendar.jsx  # 월간 캘린더
│   ├── Timetable.jsx     # 주간 시간표
│   ├── Notifications.jsx # 알림 목록
│   ├── Settings.jsx      # 설정
│   ├── ScheduleDetail.jsx# 일정 상세
│   └── TaskDetail.jsx    # 할 일 상세
├── services/             # API 서비스
│   ├── aiService.js      # AI 챗봇 API
│   ├── api.js            # Axios 인스턴스
│   ├── calendarService.js# 캘린더 API
│   ├── lectureService.js # 강의/시간표 API
│   ├── notificationService.js # 알림 API
│   ├── subTaskService.js # 서브태스크 API
│   └── todoService.js    # 할 일 API
├── styles/               # 전역 스타일
│   ├── global.css        # 전역 CSS
│   ├── theme.js          # 테마 설정
│   └── variables.css     # CSS 변수
├── utils/                # 유틸리티
│   ├── constants.js      # 상수
│   ├── dateUtils.js      # 날짜 유틸
│   ├── i18n.js           # 다국어
│   └── priorityUtils.js  # 우선순위 유틸
├── App.jsx               # 앱 루트
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
