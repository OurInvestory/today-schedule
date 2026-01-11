import React, { useRef } from 'react';
import { isToday, isSameDay } from '../../utils/dateUtils';
import './DateCell.css';

const DateCell = ({ date, isCurrentMonth, isSelected, hasEvents, hasCompleted, hasPending, onClick, onDoubleClick }) => {
  // 할 일 존재 여부 확인 (완료 또는 미완료)
  const hasTodos = hasCompleted || hasPending;
  const lastTapRef = useRef(0);
  
  const cellClass = [
    'date-cell',
    !isCurrentMonth && 'date-cell--other-month',
    isToday(date) && 'date-cell--today',
    isSelected && 'date-cell--selected',
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

  // 인디케이터 렌더링 로직
  // 우선순위: 할 일 존재 여부 > 일정 존재 여부
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
    
    // 케이스 3: 둘 다 없는 경우 - 아무것도 표시하지 않음
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
      <div className="date-cell__indicators">
        {renderIndicators()}
      </div>
    </button>
  );
};

export default DateCell;
