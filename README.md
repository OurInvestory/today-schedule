# 5늘의 일정

> watsonx.ai 기반 대학생 맞춤형 AI 학업 스케줄 도우미

## 📌 프로젝트 소개

대학생이 자연어로 입력한 할 일(과제, 시험, 팀플, 대외활동 등)을 AI가 자동으로 분석·분류하고, 중요도와 마감기한을 고려해 우선순위를 추천하는 스마트 학습 도우미입니다.

### 주요 기능

- **자연어 일정 입력**: "다음 주 수요일까지 자료구조 과제" → AI가 자동 파싱
- **지능형 우선순위 추천**: 마감기한, 소요 시간, 중요도 기반 AI 우선순위 산정
- **캘린더 연동**: Google Calendar 동기화 및 통합 관리
- **챗봇 인터페이스**: 대화형으로 일정 추가/수정/조회
- **실시간 알림**: 마감 임박 알림, 일정 요약

## 🛠 기술 스택

### Frontend
- React.js
- Vite

### Backend
- FastAPI
- MySQL

### AI
- watsonx.ai (자연어 처리, 우선순위 추천)
- Google Calendar API

## 👥 팀 구성

- **PM + 프론트엔드**: 손민주
- **Prompt Engineer + 도메인 전문가**: 천지우
- **프론트엔드**: 김혜영
- **백엔드 + AI Engineer**: 김진영, 조하영

## 🚀 시작하기

### 프론트엔드

```bash
cd frontend
npm install
npm run dev
```

### 백엔드

```bash
cd backend
# TBD
```

## 📝 문서

- [API 명세서](./docs/API.md) (TBD)
- [데이터베이스 스키마](./docs/DATABASE.md) (TBD)
- [프롬프트 가이드](./docs/PROMPT.md) (TBD)

### 커밋 컨벤션

- `feat`: 새로운 기능 추가
- `fix`: 버그 수정
- `docs`: 문서 수정
- `style`: 코드 포맷팅, 세미콜론 누락 등
- `refactor`: 코드 리팩토링
- `test`: 테스트 코드
- `chore`: 빌드 업무, 패키지 매니저 설정 등