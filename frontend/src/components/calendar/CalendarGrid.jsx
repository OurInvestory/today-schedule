import React from 'react';
import DateCell from './DateCell';
import { WEEKDAYS } from '../../utils/constants';
import { isSameDay } from '../../utils/dateUtils';
import './CalendarGrid.css';

const CalendarGrid = ({ dates, selectedDate, onDateClick, onDateDoubleClick, hasEventsOnDate, hasCompletedOnDate, hasPendingOnDate, hasGoogleEventsOnDate = () => false, isFullMode = false, getEventsForDate, getTodosForDate }) => {
  return (
    <div className={`calendar-grid ${isFullMode ? 'calendar-grid--full-mode' : ''}`}>
      {/* Weekday headers */}
      <div className="calendar-grid__weekdays">{WEEKDAYS.map((day, index) => (
          <div
            key={index}
            className={`calendar-grid__weekday ${
              index === 0 ? 'calendar-grid__weekday--sunday' : ''
            } ${index === 6 ? 'calendar-grid__weekday--saturday' : ''}`}
          >
            {day}
          </div>
        ))}
      </div>

      {/* Date cells */}
      <div className="calendar-grid__dates">
        {dates.map((dateObj, index) => (
          <DateCell
            key={index}
            date={dateObj.date}
            isCurrentMonth={dateObj.isCurrentMonth}
            isSelected={isSameDay(dateObj.date, selectedDate)}
            hasEvents={hasEventsOnDate(dateObj.date)}
            hasCompleted={hasCompletedOnDate ? hasCompletedOnDate(dateObj.date) : false}
            hasPending={hasPendingOnDate ? hasPendingOnDate(dateObj.date) : false}
            hasGoogleEvents={hasGoogleEventsOnDate(dateObj.date)}
            onClick={onDateClick}
            onDoubleClick={onDateDoubleClick}
            isFullMode={isFullMode}
            events={getEventsForDate ? getEventsForDate(dateObj.date) : []}
            todos={getTodosForDate ? getTodosForDate(dateObj.date) : []}
          />
        ))}
      </div>
    </div>
  );
};

export default CalendarGrid;
