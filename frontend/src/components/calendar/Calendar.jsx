import React, { useState } from 'react';
import CalendarHeader from './CalendarHeader';
import CalendarGrid from './CalendarGrid';
import { useCalendar } from '../../hooks/useCalendar';
import Loading from '../common/Loading';
import './Calendar.css';

const Calendar = ({ onDateSelect, todos = [] }) => {
  const [isMonthPickerOpen, setIsMonthPickerOpen] = useState(false);
  
  const {
    currentDate,
    selectedDate,
    dates,
    loading,
    goToPreviousMonth,
    goToNextMonth,
    goToMonth,
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

  const handleMonthSelect = (year, month) => {
    goToMonth(year, month);
    setIsMonthPickerOpen(false);
  };

  // 특정 날짜에 완료된 할 일이 있는지 확인
  const hasCompletedOnDate = (date) => {
    return todos.some(todo => {
      if (!todo.completed) return false;
      const todoDate = todo.dueDate ? new Date(todo.dueDate) : null;
      if (!todoDate) return false;
      return (
        todoDate.getFullYear() === date.getFullYear() &&
        todoDate.getMonth() === date.getMonth() &&
        todoDate.getDate() === date.getDate()
      );
    });
  };

  // 특정 날짜에 미완료 할 일이 있는지 확인
  const hasPendingOnDate = (date) => {
    return todos.some(todo => {
      if (todo.completed) return false;
      const todoDate = todo.dueDate ? new Date(todo.dueDate) : null;
      if (!todoDate) return false;
      return (
        todoDate.getFullYear() === date.getFullYear() &&
        todoDate.getMonth() === date.getMonth() &&
        todoDate.getDate() === date.getDate()
      );
    });
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
        onTitleClick={() => setIsMonthPickerOpen(true)}
      />
      <CalendarGrid
        dates={dates}
        selectedDate={selectedDate}
        onDateClick={handleDateClick}
        hasEventsOnDate={hasEventsOnDate}
        hasCompletedOnDate={hasCompletedOnDate}
        hasPendingOnDate={hasPendingOnDate}
      />

      {/* 연월 선택 모달 */}
      {isMonthPickerOpen && (
        <MonthPicker
          currentDate={currentDate}
          onSelect={handleMonthSelect}
          onClose={() => setIsMonthPickerOpen(false)}
        />
      )}
    </div>
  );
};

// 연월 선택 모달 컴포넌트
const MonthPicker = ({ currentDate, onSelect, onClose }) => {
  const [selectedYear, setSelectedYear] = useState(currentDate.getFullYear());
  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 21 }, (_, i) => currentYear - 10 + i);
  const months = [
    '1월', '2월', '3월', '4월', '5월', '6월',
    '7월', '8월', '9월', '10월', '11월', '12월'
  ];

  return (
    <>
      <div className="month-picker__overlay" onClick={onClose} />
      <div className="month-picker">
        <div className="month-picker__header">
          <h3 className="month-picker__title">날짜 선택</h3>
          <button className="month-picker__close" onClick={onClose}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div className="month-picker__year-section">
          <button 
            className="month-picker__year-nav"
            onClick={() => setSelectedYear(prev => prev - 1)}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="15 18 9 12 15 6" />
            </svg>
          </button>
          <select 
            className="month-picker__year-select"
            value={selectedYear}
            onChange={(e) => setSelectedYear(Number(e.target.value))}
          >
            {years.map(year => (
              <option key={year} value={year}>{year}년</option>
            ))}
          </select>
          <button 
            className="month-picker__year-nav"
            onClick={() => setSelectedYear(prev => prev + 1)}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </button>
        </div>

        <div className="month-picker__months">
          {months.map((month, index) => (
            <button
              key={index}
              className={`month-picker__month ${
                selectedYear === currentDate.getFullYear() && index === currentDate.getMonth() 
                  ? 'month-picker__month--current' 
                  : ''
              }`}
              onClick={() => onSelect(selectedYear, index)}
            >
              {month}
            </button>
          ))}
        </div>
      </div>
    </>
  );
};

export default Calendar;
