import React from 'react';
import CalendarHeader from './CalendarHeader';
import CalendarGrid from './CalendarGrid';
import { useCalendar } from '../../hooks/useCalendar';
import Loading from '../common/Loading';
import './Calendar.css';

const Calendar = ({ onDateSelect }) => {
  const {
    currentDate,
    selectedDate,
    dates,
    loading,
    goToPreviousMonth,
    goToNextMonth,
    goToToday,
    selectDate,
    hasEventsOnDate,
  } = useCalendar();

  const handleDateClick = (date) => {
    selectDate(date);
    if (onDateSelect) {
      onDateSelect(date);
    }
  };

  if (loading && dates.length === 0) {
    return (
      <div className="calendar calendar--loading">
        <Loading text="캘린더를 불러오는 중..." />
      </div>
    );
  }

  return (
    <div className="calendar">
      <CalendarHeader
        currentDate={currentDate}
        onPrevMonth={goToPreviousMonth}
        onNextMonth={goToNextMonth}
        onToday={goToToday}
      />
      <CalendarGrid
        dates={dates}
        selectedDate={selectedDate}
        onDateClick={handleDateClick}
        hasEventsOnDate={hasEventsOnDate}
      />
    </div>
  );
};

export default Calendar;
