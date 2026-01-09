import { WEEKDAYS } from './constants';

/**
 * 날짜를 포맷팅
 */
export const formatDate = (date, format = 'YYYY-MM-DD') => {
  const d = new Date(date);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const hours = String(d.getHours()).padStart(2, '0');
  const minutes = String(d.getMinutes()).padStart(2, '0');

  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('M', d.getMonth() + 1)
    .replace('DD', day)
    .replace('D', d.getDate())
    .replace('HH', hours)
    .replace('mm', minutes);
};

/**
 * 오늘인지 확인
 */
export const isToday = (date) => {
  const today = new Date();
  const targetDate = new Date(date);
  
  return (
    today.getFullYear() === targetDate.getFullYear() &&
    today.getMonth() === targetDate.getMonth() &&
    today.getDate() === targetDate.getDate()
  );
};

/**
 * 같은 날짜인지 확인
 */
export const isSameDay = (date1, date2) => {
  const d1 = new Date(date1);
  const d2 = new Date(date2);
  
  return (
    d1.getFullYear() === d2.getFullYear() &&
    d1.getMonth() === d2.getMonth() &&
    d1.getDate() === d2.getDate()
  );
};

/**
 * 같은 월인지 확인
 */
export const isSameMonth = (date1, date2) => {
  const d1 = new Date(date1);
  const d2 = new Date(date2);
  
  return (
    d1.getFullYear() === d2.getFullYear() &&
    d1.getMonth() === d2.getMonth()
  );
};

/**
 * 월의 첫 날 가져오기
 */
export const getFirstDayOfMonth = (date) => {
  const d = new Date(date);
  return new Date(d.getFullYear(), d.getMonth(), 1);
};

/**
 * 월의 마지막 날 가져오기
 */
export const getLastDayOfMonth = (date) => {
  const d = new Date(date);
  return new Date(d.getFullYear(), d.getMonth() + 1, 0);
};

/**
 * 월의 일수 가져오기
 */
export const getDaysInMonth = (date) => {
  const d = new Date(date);
  return new Date(d.getFullYear(), d.getMonth() + 1, 0).getDate();
};

/**
 * 캘린더 그리드에 표시할 날짜 배열 생성
 */
export const getCalendarDates = (year, month) => {
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const daysInMonth = lastDay.getDate();
  const startDayOfWeek = firstDay.getDay();
  
  const dates = [];
  
  // 이전 달 날짜 채우기
  const prevMonthLastDay = new Date(year, month, 0).getDate();
  for (let i = startDayOfWeek - 1; i >= 0; i--) {
    dates.push({
      date: new Date(year, month - 1, prevMonthLastDay - i),
      isCurrentMonth: false,
    });
  }
  
  // 현재 달 날짜 채우기
  for (let i = 1; i <= daysInMonth; i++) {
    dates.push({
      date: new Date(year, month, i),
      isCurrentMonth: true,
    });
  }
  
  // 다음 달 날짜 채우기 (6주 기준)
  const remainingDays = 42 - dates.length;
  for (let i = 1; i <= remainingDays; i++) {
    dates.push({
      date: new Date(year, month + 1, i),
      isCurrentMonth: false,
    });
  }
  
  return dates;
};

/**
 * 상대적인 날짜 표시 (예: "오늘", "내일", "3일 후")
 */
export const getRelativeDateText = (date) => {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  const targetDate = new Date(date);
  targetDate.setHours(0, 0, 0, 0);
  
  const diffTime = targetDate - today;
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) return '오늘';
  if (diffDays === 1) return '내일';
  if (diffDays === -1) return '어제';
  if (diffDays > 1 && diffDays <= 7) return `${diffDays}일 후`;
  if (diffDays < -1 && diffDays >= -7) return `${Math.abs(diffDays)}일 전`;
  
  return formatDate(date, 'M월 D일');
};

/**
 * 마감일까지 남은 시간 텍스트
 */
export const getTimeUntilText = (dueDate) => {
  const now = new Date();
  const due = new Date(dueDate);
  const diffMs = due - now;
  
  if (diffMs < 0) return '마감됨';
  
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffHours / 24);
  
  if (diffHours < 1) {
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    return `${diffMinutes}분 남음`;
  }
  
  if (diffHours < 24) return `${diffHours}시간 남음`;
  if (diffDays === 1) return '내일까지';
  if (diffDays <= 7) return `${diffDays}일 남음`;
  
  return formatDate(dueDate, 'M월 D일까지');
};

/**
 * 요일 가져오기
 */
export const getWeekday = (date) => {
  const d = new Date(date);
  return WEEKDAYS[d.getDay()];
};

/**
 * 이번 주 날짜 범위 가져오기
 */
export const getWeekRange = (date = new Date()) => {
  const d = new Date(date);
  const day = d.getDay();
  const diff = d.getDate() - day;
  
  const sunday = new Date(d.setDate(diff));
  const saturday = new Date(d.setDate(diff + 6));
  
  return { start: sunday, end: saturday };
};

/**
 * 월 증가/감소
 */
export const addMonths = (date, months) => {
  const d = new Date(date);
  d.setMonth(d.getMonth() + months);
  return d;
};

/**
 * 날짜가 과거인지 확인
 */
export const isPast = (date) => {
  const now = new Date();
  const targetDate = new Date(date);
  return targetDate < now;
};

/**
 * 날짜가 미래인지 확인
 */
export const isFuture = (date) => {
  const now = new Date();
  const targetDate = new Date(date);
  return targetDate > now;
};

/**
 * 마감 지남 여부 확인
 */
export const isOverdue = (date) => {
  const now = new Date();
  const targetDate = new Date(date);
  return targetDate < now;
};