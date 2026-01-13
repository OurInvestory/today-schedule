import { PRIORITIES } from './constants';

/**
 * 우선순위 자동 계산 (high, medium, low)
 */
export const calculatePriority = (dueDate, estimatedMinute = 60) => {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  const due = new Date(dueDate);
  due.setHours(0, 0, 0, 0);
  
  const daysUntil = Math.ceil((due - today) / (1000 * 60 * 60 * 24));
  const estimatedHours = Math.floor(estimatedMinute / 60);
  
  // 마감일이 지났거나 당일
  if (daysUntil <= 0) {
    return 'high';
  }
  
  // 내일까지이고 소요 시간이 2시간 이상
  if (daysUntil === 1 && estimatedHours >= 2) {
    return 'high';
  }
  
  // 3일 이내이고 소요 시간이 3시간 이상
  if (daysUntil <= 3 && estimatedHours >= 3) {
    return 'high';
  }
  
  // 7일 이내이고 소요 시간이 5시간 이상
  if (daysUntil <= 7 && estimatedHours >= 5) {
    return 'medium';
  }
  
  // 7일 이내
  if (daysUntil <= 7) {
    return 'medium';
  }
  
  // 그 외
  return 'low';
};

/**
 * 우선순위 점수 계산 (마감일, 중요도, 시작일 기반)
 * AI가 오늘 해야 할 일을 결정하는 핵심 로직
 */
export const calculatePriorityScore = (todo) => {
  const { startDate, dueDate, importance = 5, estimatedTime = 1 } = todo;
  
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  
  // 마감일까지 남은 시간 (시간 단위)
  const due = dueDate ? new Date(dueDate) : new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000); // 마감일 없으면 일주일 후로 가정
  const hoursUntilDue = (due - now) / (1000 * 60 * 60);
  
  // 시작일 체크 (시작일이 미래면 점수 낮춤)
  const start = startDate ? new Date(startDate) : today;
  const canStartNow = start <= today;
  
  // 긴급도 점수 (0-10)
  let urgencyScore = 0;
  if (hoursUntilDue < 0) {
    urgencyScore = 10; // 이미 지남 - 최우선
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
  // 마감까지 남은 시간 대비 예상 소요 시간 비율 고려
  const timeRatio = estimatedTime / Math.max(hoursUntilDue, 1);
  const timeWeight = Math.min(1 + timeRatio, 2);
  
  // 시작 가능 여부 가중치 (시작할 수 없으면 점수 크게 낮춤)
  const startWeight = canStartNow ? 1 : 0.3;
  
  // 최종 점수 (가중 평균)
  const finalScore = (urgencyScore * 0.6 + importanceScore * 0.4) * timeWeight * startWeight;
  
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
 * 1. 완료 여부 (미완료 우선)
 * 2. 우선순위 점수 (높은 순)
 * 3. 중요도 (높은 순)
 * 4. 마감일 (가까운 순)
 */
export const sortByPriority = (todos) => {
  return [...todos].sort((a, b) => {
    // 완료된 항목은 맨 아래로
    if (a.completed && !b.completed) return 1;
    if (!a.completed && b.completed) return -1;
    
    // 우선순위 점수로 정렬
    const scoreA = a.priorityScore || 0;
    const scoreB = b.priorityScore || 0;
    
    if (scoreB !== scoreA) {
      return scoreB - scoreA;
    }
    
    // 동점이면 중요도로 정렬
    const importanceA = a.importance || 5;
    const importanceB = b.importance || 5;
    
    if (importanceB !== importanceA) {
      return importanceB - importanceA;
    }
    
    // 그래도 동점이면 마감일이 가까운 순
    const dueDateA = a.dueDate ? new Date(a.dueDate).getTime() : Infinity;
    const dueDateB = b.dueDate ? new Date(b.dueDate).getTime() : Infinity;
    
    return dueDateA - dueDateB;
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