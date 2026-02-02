import React, { useState, useRef, useMemo } from 'react';
import { getTimeUntilText, isOverdue } from '../../utils/dateUtils';
import PriorityBadge from './PriorityBadge';
import CategoryBadge from './CategoryBadge';
import './TodoItem.css';

// 응원 문구 15개 (AI tip이 없을 때 랜덤 표시)
const ENCOURAGEMENT_TIPS = [
  "💪 조금만 더 하면 됩니다! 파이팅!",
  "🌟 한 걸음씩 나아가면 목표에 도달해요!",
  "✨ 오늘의 노력이 내일의 성과가 됩니다!",
  "🎯 집중하면 금방 끝나요! 할 수 있어요!",
  "🚀 시작이 반이에요! 이미 반은 했네요!",
  "💡 잠깐 쉬었다 해도 괜찮아요, 다시 시작하면 돼요!",
  "🏃 꾸준히 하면 분명 좋은 결과가 있을 거예요!",
  "🌈 힘들 때 조금만 버티면 무지개가 뜹니다!",
  "⭐ 당신은 할 수 있어요! 믿어요!",
  "🔥 열정을 불태워요! 완료까지 얼마 안 남았어요!",
  "🎉 완료하면 뿌듯할 거예요! 조금만 더!",
  "💎 작은 노력이 모여 큰 성과가 됩니다!",
  "🌻 오늘 하루도 수고 많으셨어요!",
  "📚 천천히 하나씩 해결해 나가요!",
  "🏆 끝까지 포기하지 않는 당신이 멋져요!",
];

// 랜덤 응원 문구 가져오기 (todo.id 기반으로 일관성 유지)
const getRandomEncouragement = (todoId) => {
  // todoId를 기반으로 인덱스 계산 (같은 todo에는 항상 같은 문구)
  const hash = todoId ? todoId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) : 0;
  return ENCOURAGEMENT_TIPS[hash % ENCOURAGEMENT_TIPS.length];
};

// tip 가져오기 - 백엔드 tip 우선, 없으면 응원 문구
const getTip = (todo) => {
  // 백엔드에서 받은 tip이 있으면 우선 사용
  if (todo.tip) return todo.tip;
  
  // 없으면 랜덤 응원 문구 (todo.id 기반 일관성)
  return getRandomEncouragement(todo.id);
};

const TodoItem = ({ todo, onToggle, onEdit, onDelete }) => {
  const [swipeOffset, setSwipeOffset] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [lastTap, setLastTap] = useState(0);
  const [longPressTimeout, setLongPressTimeout] = useState(null);
  const startXRef = useRef(0);
  const currentXRef = useRef(0);

  // 팁 (백엔드 tip 우선, 없으면 응원 문구)
  const tip = useMemo(() => getTip(todo), [todo]);

  // 일정 색상 가져오기 (schedule.color 또는 기본 초록색)
  const scheduleColor = useMemo(() => {
    return todo.schedule?.color || todo.scheduleColor || null;
  }, [todo]);

  // 팁 배경색 계산 (일정 색상 기반 파스텔톤)
  const tipStyle = useMemo(() => {
    if (!scheduleColor) {
      // 기본 초록색 스타일
      return {
        background: 'linear-gradient(135deg, #F0FDF4 0%, #ECFDF5 100%)',
        borderColor: '#D1FAE5',
        iconColor: '#10B981',
        textColor: '#047857',
      };
    }
    // 일정 색상 기반 파스텔톤 생성
    return {
      background: `linear-gradient(135deg, ${scheduleColor}15 0%, ${scheduleColor}20 100%)`,
      borderColor: `${scheduleColor}40`,
      iconColor: scheduleColor,
      textColor: scheduleColor,
    };
  }, [scheduleColor]);

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
      
      {tip && (
        <div 
          className="todo-item__tip"
          style={{
            background: tipStyle.background,
            borderColor: tipStyle.borderColor,
          }}
        >
          <div className="tip-icon" style={{ color: tipStyle.iconColor }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="16" x2="12" y2="12" />
              <line x1="12" y1="8" x2="12.01" y2="8" />
            </svg>
          </div>
          <span className="tip-text" style={{ color: tipStyle.textColor }}>{tip}</span>
        </div>
      )}
    </div>
  );
};

export default TodoItem;