// 카테고리 정의
export const CATEGORIES = {
  CLASS: 'class',
  ASSIGNMENT: 'assignment',
  EXAM: 'exam',
  TEAM: 'team',
  ACTIVITY: 'activity',
};

export const CATEGORY_LABELS = {
  [CATEGORIES.CLASS]: '수업',
  [CATEGORIES.ASSIGNMENT]: '과제',
  [CATEGORIES.EXAM]: '시험',
  [CATEGORIES.TEAM]: '팀플',
  [CATEGORIES.ACTIVITY]: '대외활동',
};

export const CATEGORY_COLORS = {
  [CATEGORIES.CLASS]: '#E0E7FF',
  [CATEGORIES.ASSIGNMENT]: '#FEF3C7',
  [CATEGORIES.EXAM]: '#FEE2E2',
  [CATEGORIES.TEAM]: '#E9D5FF',
  [CATEGORIES.ACTIVITY]: '#D1FAE5',
};

// 우선순위 정의
export const PRIORITIES = {
  HIGH: 'high',
  MEDIUM: 'medium',
  LOW: 'low',
};

export const PRIORITY_LABELS = {
  [PRIORITIES.HIGH]: '높음',
  [PRIORITIES.MEDIUM]: '중간',
  [PRIORITIES.LOW]: '낮음',
};

export const PRIORITY_ICONS = {
  [PRIORITIES.HIGH]: '🔥',
  [PRIORITIES.MEDIUM]: '⚡',
  [PRIORITIES.LOW]: '📝',
};

// 날짜 포맷
export const DATE_FORMATS = {
  DISPLAY: 'YYYY년 M월 D일',
  API: 'YYYY-MM-DD',
  TIME: 'HH:mm',
  DATETIME: 'YYYY-MM-DD HH:mm',
};

// 요일
export const WEEKDAYS = ['일', '월', '화', '수', '목', '금', '토'];
export const WEEKDAYS_SHORT = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];

// API 엔드포인트
export const API_ENDPOINTS = {
  TODOS: '/todos',
  AI_PARSE: '/ai/parse',
  AI_PRIORITY: '/ai/priority',
  CALENDAR_SYNC: '/calendar/sync',
  CHAT: '/chat',
};

// 로컬 스토리지 키
export const STORAGE_KEYS = {
  TODOS: 'todos',
  FILTER: 'todoFilter',
  VIEW_MODE: 'viewMode',
};