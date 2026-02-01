import React, { useRef, useState } from 'react';
import { isToday } from '../../utils/dateUtils';
import './DateCell.css';

const DateCell = ({ date, isCurrentMonth, isSelected, hasEvents, hasMultiDayEvent = false, hasCompleted, hasPending, hasGoogleEvents, onClick, onDoubleClick, isFullMode = false, events = [], todos = [] }) => {
  // 할 일 존재 여부 확인 (완료 또는 미완료)
  const hasTodos = hasCompleted || hasPending;
  const lastTapRef = useRef(0);
  const [isExpanded, setIsExpanded] = useState(false);
  
  const cellClass = [
    'date-cell',
    !isCurrentMonth && 'date-cell--other-month',
    isToday(date) && 'date-cell--today',
    isSelected && 'date-cell--selected',
    isFullMode && 'date-cell--full-mode',
  ]
    .filter(Boolean)
    .join(' ');

  const handleClick = () => {
    const now = Date.now();
    const DOUBLE_TAP_DELAY = 300;
    
    if (now - lastTapRef.current < DOUBLE_TAP_DELAY) {
      // 더블탭 감지
      if (onDoubleClick) {
        onDoubleClick(date);
      }
      lastTapRef.current = 0;
    } else {
      lastTapRef.current = now;
      onClick(date);
    }
  };

  const handleDoubleClick = () => {
    if (onDoubleClick) {
      onDoubleClick(date);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onClick(date);
    }
  };

  // 전체 모드에서 상세 일정+할일 표시
  const renderDetailedEvents = () => {
    if (events.length === 0 && todos.length === 0) return null;

    // 완료된 할일과 미완료 할일 분리
    const completedTodos = todos.filter(todo => todo.completed);
    const pendingTodos = todos.filter(todo => !todo.completed);

    // 일반 일정과 구글 일정 분리
    const regularEvents = events.filter(event => event.source !== 'google');
    const googleEvents = events.filter(event => event.source === 'google');

    const allItems = [];

    // 표시 순서: 일정(파랑) > 구글 일정(빨강) > 미완료 할일(노란) > 완료한 할일(초록)
    
    // 1. 일반 일정 (파란색)
    regularEvents.forEach(event => {
      allItems.push({ type: 'event', data: event });
    });

    // 2. 구글 캘린더 일정 (빨간색)
    googleEvents.forEach(event => {
      allItems.push({ type: 'event', data: event });
    });

    // 3. 미완료 할일 (노란색)
    pendingTodos.forEach(todo => {
      allItems.push({ type: 'todo', data: todo });
    });

    // 4. 완료한 할일 (초록색)
    completedTodos.forEach(todo => {
      allItems.push({ type: 'todo', data: todo });
    });

    // 모바일과 PC에서 다른 줄 수 제한
    const isMobile = window.innerWidth <= 640;
    const MAX_LINES = isMobile ? 3 : 5;
    const visibleItems = isExpanded ? allItems : allItems.slice(0, MAX_LINES);
    const remainingCount = allItems.length - visibleItems.length;

    return (
      <div className="date-cell__events">
        {visibleItems.map((item, idx) => {
          if (item.type === 'event') {
            const event = item.data;
            const isGoogleEvent = event.source === 'google';
            // 구글 일정: 빨간색, 일반 일정: 파란색
            const eventColor = isGoogleEvent ? '#ea4335' : '#3b82f6';
            
            return (
              <div
                key={`event-${event.id || idx}`}
                className="date-cell__event-bar"
                style={{ backgroundColor: eventColor }}
                title={event.title}
              >
                {isGoogleEvent && <span className="event-bar__google-icon">G</span>}
                <span className="event-bar__title">{event.title}</span>
              </div>
            );
          } else {
            // 할일: 완료=초록색, 미완료=노란색
            const todo = item.data;
            const todoColor = todo.completed ? '#10b981' : '#eab308';
            
            return (
              <div
                key={`todo-${todo.id || idx}`}
                className="date-cell__todo-item"
                style={{ color: todoColor }}
                title={todo.title}
              >
                <span className="todo-item__title">{todo.title}</span>
              </div>
            );
          }
        })}
        {remainingCount > 0 && (
          <button
            className="date-cell__more-btn"
            onClick={(e) => {
              e.stopPropagation();
              setIsExpanded(!isExpanded);
            }}
          >
            {isExpanded ? '접기' : `+${remainingCount}`}
          </button>
        )}
      </div>
    );
  };

  // 인디케이터 렌더링 로직
  // 우선순위: 할 일 존재 여부 > 일정 존재 여부 > 구글 캘린더 연동
  const renderIndicators = () => {
    // 케이스 1: 할 일이 있는 경우 - 완료 여부에 따라 색상 점 표시
    if (hasTodos) {
      return (
        <>
          {hasPending && <span className="date-cell__dot date-cell__dot--pending" />}
          {hasCompleted && <span className="date-cell__dot date-cell__dot--completed" />}
        </>
      );
    }
    
    // 케이스 2: 할 일은 없지만 일정이 있는 경우 - 파란색 원형 아이콘
    if (hasEvents) {
      return <span className="date-cell__schedule-icon" />;
    }
    
    // 케이스 3: 구글 캘린더 연동 일정만 있는 경우 - 빨간색 원형 아이콘
    if (hasGoogleEvents) {
      return <span className="date-cell__google-icon" />;
    }
    
    // 케이스 4: 아무것도 없는 경우 - 아무것도 표시하지 않음
    return null;
  };

  return (
    <button
      type="button"
      className={cellClass}
      onClick={handleClick}
      onDoubleClick={handleDoubleClick}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      aria-label={`${date.getMonth() + 1}월 ${date.getDate()}일`}
      aria-pressed={isSelected}
    >
      <span className="date-cell__number">{date.getDate()}</span>
      {isFullMode ? (
        renderDetailedEvents()
      ) : (
        <div className="date-cell__indicators">
          {renderIndicators()}
        </div>
      )}
    </button>
  );
};

export default DateCell;
