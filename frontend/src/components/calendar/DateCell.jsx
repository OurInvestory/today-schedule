import React from 'react';
import { isToday, isSameDay } from '../../utils/dateUtils';
import './DateCell.css';

const DateCell = ({ date, isCurrentMonth, isSelected, hasEvents, hasCompleted, hasPending, onClick }) => {
  const cellClass = [
    'date-cell',
    !isCurrentMonth && 'date-cell--other-month',
    isToday(date) && 'date-cell--today',
    isSelected && 'date-cell--selected',
    hasEvents && 'date-cell--has-events',
  ]
    .filter(Boolean)
    .join(' ');

  const handleClick = () => {
    onClick(date);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onClick(date);
    }
  };

  return (
    <button
      type="button"
      className={cellClass}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      aria-label={`${date.getMonth() + 1}월 ${date.getDate()}일`}
      aria-pressed={isSelected}
    >
      <span className="date-cell__number">{date.getDate()}</span>
      <div className="date-cell__indicators">
        {hasPending && <span className="date-cell__dot date-cell__dot--pending" />}
        {hasCompleted && <span className="date-cell__dot date-cell__dot--completed" />}
        {hasEvents && !hasPending && !hasCompleted && <span className="date-cell__dot" />}
      </div>
    </button>
  );
};

export default DateCell;
