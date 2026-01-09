import { PRIORITIES } from './constants';

/**
 * 우선순위 점수 계산 (마감일, 중요도 기반)
 */
export const calculatePriorityScore = (todo) => {
  const { dueDate, importance = 5, estimatedTime = 1 } = todo;
  
  // 마감일까지 남은 시간 (시간 단위)
  const now = new Date();
  const due = new Date(dueDate);
  const hoursUntilDue = (due - now) / (1000 * 60 * 60);
  
  // 긴급도 점수 (0-10)
  let urgencyScore = 0;
  if (hoursUntilDue < 0) {
    urgencyScore = 10; // 이미 지남
  } else if (hoursUntilDue < 2) {
    urgencyScore = 9;
  } else if (hoursUntilDue < 6) {
    urgencyScore = 8;
  } else if (hoursUntilDue < 24) {
    urgencyScore = 7;
  } else if (hoursUntilDue < 48) {
    urgencyScore = 6;
  } else if (hoursUntilDue < 72) {
    urgencyScore = 5;
  } else if (hoursUntilDue < 168) {
    urgencyScore = 4;
  } else {
    urgencyScore = 3;
  }
  
  // 중요도 점수 (1-10)
  const importanceScore = importance;
  
  // 예상 소요 시간 가중치 (시간이 오래 걸릴수록 미리 시작해야 함)
  const timeWeight = Math.min(estimatedTime / 5, 2);
  
  // 최종 점수 (가중 평균)
  const finalScore = (urgencyScore * 0.6 + importanceScore * 0.4) * timeWeight;
  
  return Math.round(finalScore * 10) / 10;
};

/**
 * 우선순위 레벨 결정
 */
export const getPriorityLevel = (score) => {
  if (score >= 8) return PRIORITIES.HIGH;
  if (score >= 5) return PRIORITIES.MEDIUM;
  return PRIORITIES.LOW;
};

/**
 * Todo에 우선순위 할당
 */
export const assignPriority = (todo) => {
  const score = calculatePriorityScore(todo);
  const level = getPriorityLevel(score);
  
  return {
    ...todo,
    priorityScore: score,
    priority: level,
  };
};

/**
 * Todo 목록 우선순위 정렬
 */
export const sortByPriority = (todos) => {
  return [...todos].sort((a, b) => {
    // 완료된 항목은 맨 아래로
    if (a.completed && !b.completed) return 1;
    if (!a.completed && b.completed) return -1;
    
    // 우선순위 점수로 정렬
    const scoreA = a.priorityScore || 0;
    const scoreB = b.priorityScore || 0;
    
    return scoreB - scoreA;
  });
};

/**
 * 우선순위별 색상 가져오기
 */
export const getPriorityColor = (priority) => {
  const colors = {
    [PRIORITIES.HIGH]: {
      bg: 'var(--color-priority-high-bg)',
      text: 'var(--color-priority-high-text)',
      border: 'var(--color-priority-high-text)',
    },
    [PRIORITIES.MEDIUM]: {
      bg: 'var(--color-priority-medium-bg)',
      text: 'var(--color-priority-medium-text)',
      border: 'var(--color-priority-medium-text)',
    },
    [PRIORITIES.LOW]: {
      bg: 'var(--color-priority-low-bg)',
      text: 'var(--color-priority-low-text)',
      border: 'var(--color-priority-low-text)',
    },
  };
  
  return colors[priority] || colors[PRIORITIES.LOW];
};

/**
 * 마감 임박 여부 확인
 */
export const isUrgent = (dueDate) => {
  const now = new Date();
  const due = new Date(dueDate);
  const hoursUntilDue = (due - now) / (1000 * 60 * 60);
  
  return hoursUntilDue < 24 && hoursUntilDue > 0;
};

/**
 * 마감 지남 여부 확인
 */
export const isOverdue = (dueDate) => {
  const now = new Date();
  const due = new Date(dueDate);
  
  return due < now;
};