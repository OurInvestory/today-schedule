import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
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

// 휠 피커 컴포넌트
const WheelColumn = ({ items, selectedIndex, onSelect, renderItem }) => {
  const containerRef = useRef(null);
  const itemHeight = 44;
  const visibleItems = 5;
  const centerOffset = Math.floor(visibleItems / 2) * itemHeight;

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = selectedIndex * itemHeight;
    }
  }, [selectedIndex]);

  const handleScroll = (e) => {
    const scrollTop = e.target.scrollTop;
    const newIndex = Math.round(scrollTop / itemHeight);
    if (newIndex >= 0 && newIndex < items.length && newIndex !== selectedIndex) {
      onSelect(newIndex);
    }
  };

  const handleWheel = (e) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 1 : -1;
    const newIndex = Math.min(Math.max(0, selectedIndex + delta), items.length - 1);
    if (newIndex !== selectedIndex) {
      onSelect(newIndex);
      if (containerRef.current) {
        containerRef.current.scrollTop = newIndex * itemHeight;
      }
    }
  };

  return (
    <div 
      className="wheel-picker__column"
      ref={containerRef}
      onScroll={handleScroll}
      onWheel={handleWheel}
    >
      <div style={{ height: centerOffset }} />
      {items.map((item, index) => (
        <div
          key={index}
          className={`wheel-picker__item ${index === selectedIndex ? 'wheel-picker__item--selected' : ''}`}
          onClick={() => {
            onSelect(index);
            if (containerRef.current) {
              containerRef.current.scrollTop = index * itemHeight;
            }
          }}
        >
          {renderItem ? renderItem(item) : item}
        </div>
      ))}
      <div style={{ height: centerOffset }} />
    </div>
  );
};

// 연월 선택 모달 컴포넌트 (휠 피커 방식)
const MonthPicker = ({ currentDate, onSelect, onClose }) => {
  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 21 }, (_, i) => currentYear - 10 + i);
  const months = Array.from({ length: 12 }, (_, i) => i + 1);

  const [selectedYearIndex, setSelectedYearIndex] = useState(
    years.indexOf(currentDate.getFullYear())
  );
  const [selectedMonthIndex, setSelectedMonthIndex] = useState(
    currentDate.getMonth()
  );

  const handleConfirm = () => {
    onSelect(years[selectedYearIndex], selectedMonthIndex);
  };

  return createPortal(
    <>
      <div className="month-picker__overlay" onClick={onClose} />
      <div className="month-picker month-picker--wheel">
        <div className="month-picker__header">
          <button className="month-picker__cancel" onClick={onClose}>
            취소
          </button>
          <h3 className="month-picker__title">날짜 선택</h3>
          <button className="month-picker__confirm" onClick={handleConfirm}>
            확인
          </button>
        </div>

        <div className="wheel-picker">
          <div className="wheel-picker__highlight" />
          <WheelColumn
            items={years}
            selectedIndex={selectedYearIndex}
            onSelect={setSelectedYearIndex}
            renderItem={(year) => `${year}년`}
          />
          <WheelColumn
            items={months}
            selectedIndex={selectedMonthIndex}
            onSelect={setSelectedMonthIndex}
            renderItem={(month) => `${month}월`}
          />
        </div>
      </div>
    </>,
    document.body
  );
};

export default Calendar;
