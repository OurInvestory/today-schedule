import React, { useState, useRef, useMemo } from 'react';
import { getTimeUntilText, isOverdue } from '../../utils/dateUtils';
import PriorityBadge from './PriorityBadge';
import CategoryBadge from './CategoryBadge';
import './TodoItem.css';

// AI 이유 자동 생성 함수
const generateAIReason = (todo) => {
  if (todo.aiReason) return todo.aiReason;
  
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const dueDate = new Date(todo.dueDate);
  dueDate.setHours(0, 0, 0, 0);
  const daysUntil = Math.ceil((dueDate - today) / (1000 * 60 * 60 * 24));
  const estimatedHours = todo.estimatedMinute ? Math.floor(todo.estimatedMinute / 60) : 0;
  
  // 마감일 기반 이유
  if (daysUntil < 0) {
    return '이미 마감일이 지났습니다. 서둘러 처리하세요!';
  } else if (daysUntil === 0) {
    return '오늘이 마감일입니다. 우선적으로 처리하세요!';
  } else if (daysUntil === 1) {
    if (estimatedHours >= 2) {
      return '내일 마감이고 소요 시간이 길어요. 지금 시작하세요!';
    }
    return '내일까지 완료해야 합니다. 서둡러 준비하세요!';
  } else if (daysUntil <= 3) {
    if (estimatedHours >= 3) {
      return `${daysUntil}일 후 마감이지만 소요 시간이 길어요. 미리 시작하는 게 좋아요.`;
    }
    return `${daysUntil}일 후 마감입니다. 여유를 가지고 처리하세요.`;
  } else if (daysUntil <= 7) {
    if (estimatedHours >= 5) {
      return `${daysUntil}일 후 마감. 소요 시간을 고려해 계획을 세우세요.`;
    }
    return `${daysUntil}일의 여유가 있어요. 계획적으로 진행하세요.`;
  } else {
    if (estimatedHours >= 10) {
      return `장기 프로젝트네요. 단계별로 나눠서 진행하는 것을 추천해요.`;
    }
    return `${daysUntil}일 후 마감. 충분한 시간을 활용하세요.`;
  }
};

const TodoItem = ({ todo, onToggle, onEdit, onDelete }) => {
  const [swipeOffset, setSwipeOffset] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [lastTap, setLastTap] = useState(0);
  const [longPressTimeout, setLongPressTimeout] = useState(null);
  const startXRef = useRef(0);
  const currentXRef = useRef(0);

  // AI 이유 자동 생성
  const aiReason = useMemo(() => generateAIReason(todo), [todo]);

  const handleCheckboxChange = (e) => {
    e.stopPropagation();
    onToggle(todo.id, !todo.completed);
  };

  const handleDoubleTap = () => {
    const now = Date.now();
    if (now - lastTap < 300) {
      if (onEdit) onEdit(todo);
    }
    setLastTap(now);
  };

  // PC 환경에서 더블클릭 핸들러
  const handleDoubleClick = () => {
    if (onEdit) onEdit(todo);
  };

  const handleLongPress = () => {
    if (onEdit) onEdit(todo);
  };

  const handleTouchStart = (e) => {
    if (e.target.closest('.todo-item__checkbox') || e.target.closest('.todo-item__actions')) return;
    handleDragStart(e.touches[0].clientX);

    // Start long press detection
    const timeout = setTimeout(() => handleLongPress(), 500);
    setLongPressTimeout(timeout);
  };

  const handleTouchEnd = () => {
    handleDragEnd();

    // Clear long press timeout
    if (longPressTimeout) {
      clearTimeout(longPressTimeout);
      setLongPressTimeout(null);
    }

    // Detect double tap
    handleDoubleTap();
  };

  const handleDragStart = (clientX) => {
    startXRef.current = clientX;
    currentXRef.current = clientX;
    setIsDragging(true);
  };

  const handleDragMove = (clientX) => {
    if (!isDragging) return;
    currentXRef.current = clientX;
    const diff = clientX - startXRef.current;
    // 왼쪽으로만 스와이프 허용
    if (diff < 0) {
      setSwipeOffset(Math.max(diff, -100));
    }
  };

  const handleDragEnd = () => {
    setIsDragging(false);
    if (swipeOffset < -60) {
      // 삭제 실행
      handleDelete();
    }
    setSwipeOffset(0);
  };

  const handleDelete = () => {
    if (onDelete) onDelete(todo.id);
  };

  const itemClass = [
    'todo-item',
    todo.completed && 'todo-item--completed',
    isOverdue(todo.dueDate) && !todo.completed && 'todo-item--overdue',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className="todo-item__wrapper">
      {/* 삭제 배경 */}
      <div 
        className="todo-item__delete-bg"
        style={{ 
          width: swipeOffset < 0 ? Math.abs(swipeOffset) : 0,
          opacity: swipeOffset < 0 ? 1 : 0 
        }}
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
          <path d="M3 6h18M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
        </svg>
        <span>삭제</span>
      </div>
      
      <div 
        className={itemClass}
        style={{ transform: `translateX(${swipeOffset}px)` }}
        onMouseDown={(e) => handleDragStart(e.clientX)}
        onMouseMove={(e) => handleDragMove(e.clientX)}
        onMouseUp={handleDragEnd}
        onMouseLeave={() => isDragging && handleDragEnd()}
        onTouchStart={handleTouchStart}
        onTouchMove={(e) => handleDragMove(e.touches[0].clientX)}
        onTouchEnd={handleTouchEnd}
        onDoubleClick={handleDoubleClick}
      >
        {/* Checkbox */}
        <label className="todo-item__checkbox" onClick={(e) => e.stopPropagation()}>
          <input
            type="checkbox"
            checked={todo.completed}
            onChange={handleCheckboxChange}
          />
          <span className="todo-item__checkmark">
            {todo.completed && (
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path
                  d="M2 6L5 9L10 3"
                  stroke="white"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            )}
          </span>
        </label>

        {/* Content */}
        <div className="todo-item__content">
          <div className="todo-item__header">
            <h3 className="todo-item__title">{todo.title}</h3>
            <div className="todo-item__badges">
              <CategoryBadge category={todo.category} />
              <PriorityBadge priority={todo.priority} showIcon={false} />
            </div>
          </div>

          {todo.description && (
            <p className="todo-item__description">{todo.description}</p>
          )}

          <div className="todo-item__footer">
            <span className="todo-item__time">
              {getTimeUntilText(todo.dueDate, todo.scheduleId, todo.schedule)}
            </span>
            {todo.estimatedMinute && (
              <span className="todo-item__estimated-time">
                예상 {todo.estimatedMinute >= 60 
                  ? `${Math.floor(todo.estimatedMinute / 60)}시간${todo.estimatedMinute % 60 > 0 ? ` ${todo.estimatedMinute % 60}분` : ''}`
                  : `${todo.estimatedMinute}분`}
              </span>
            )}
          </div>
        </div>
      </div>
      
      {aiReason && (
        <div className="todo-item__ai-reason">
          <div className="ai-reason-icon">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" />
            </svg>
          </div>
          <span className="ai-reason-text">{aiReason}</span>
        </div>
      )}
    </div>
  );
};

export default TodoItem;