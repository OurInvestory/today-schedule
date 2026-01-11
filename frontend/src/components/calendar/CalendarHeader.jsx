import React from 'react';
import { formatDate } from '../../utils/dateUtils';
import Button from '../common/Button';
import './CalendarHeader.css';

const CalendarHeader = ({ currentDate, onPrevMonth, onNextMonth, onToday }) => {
  return (
    <div className="calendar-header">
      <div className="calendar-header__nav">
        <Button variant="ghost" size="sm" onClick={onPrevMonth} aria-label="이전 달">
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </Button>
        <h2 className="calendar-header__title">
          {formatDate(currentDate, 'YYYY년 M월')}
        </h2>
        <Button variant="ghost" size="sm" onClick={onNextMonth} aria-label="다음 달">
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </Button>
      </div>
      <Button variant="outline" size="sm" onClick={onToday}>
        오늘
      </Button>
    </div>
  );
};

export default CalendarHeader;
