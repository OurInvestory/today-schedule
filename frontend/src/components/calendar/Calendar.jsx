import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import CalendarHeader from './CalendarHeader';
import CalendarGrid from './CalendarGrid';
import { useCalendar } from '../../hooks/useCalendar';
import { createCalendarEvent } from '../../services/calendarService';
import Loading from '../common/Loading';
import './Calendar.css';

const Calendar = ({ onDateSelect }) => {
  const navigate = useNavigate();
  const [isMonthPickerOpen, setIsMonthPickerOpen] = useState(false);
  const [isScheduleModalOpen, setIsScheduleModalOpen] = useState(false);
  const [selectedScheduleDate, setSelectedScheduleDate] = useState(null);
  
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
    hasCompletedTodosOnDate,
    hasPendingTodosOnDate,
    getEventsForDate,
    refetch,
  } = useCalendar();

  const handleDateClick = (date) => {
    selectDate(date);
    if (onDateSelect) {
      onDateSelect(date);
    }
  };

  // 날짜 더블클릭 시 일정 편집 모달 열기
  const handleDateDoubleClick = (date) => {
    setSelectedScheduleDate(date);
    setIsScheduleModalOpen(true);
  };

  // 일정 클릭 시 일정 편집 페이지로 이동
  const handleScheduleClick = (scheduleId) => {
    navigate(`/schedule/${scheduleId}`);
  };

  // 일정 모달 닫기
  const handleScheduleModalClose = () => {
    setIsScheduleModalOpen(false);
    setSelectedScheduleDate(null);
  };

  // 일정 저장 후 처리
  const handleScheduleSave = () => {
    setIsScheduleModalOpen(false);
    setSelectedScheduleDate(null);
    refetch(); // 캘린더 데이터 새로고침

    // Debugging: Log events after refetch
    setTimeout(() => {
      console.log('Updated events after refetch:', getEventsForDate(selectedScheduleDate));
    }, 1000); // Allow time for refetch to complete
  };

  const handleMonthSelect = (year, month) => {
    goToMonth(year, month);
    setIsMonthPickerOpen(false);
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
        onDateDoubleClick={handleDateDoubleClick}
        hasEventsOnDate={hasEventsOnDate}
        hasCompletedOnDate={hasCompletedTodosOnDate}
        hasPendingOnDate={hasPendingTodosOnDate}
      />

      {/* 연월 선택 모달 */}
      {isMonthPickerOpen && (
        <MonthPicker
          currentDate={currentDate}
          onSelect={handleMonthSelect}
          onClose={() => setIsMonthPickerOpen(false)}
        />
      )}

      {/* 일정 편집 모달 */}
      {isScheduleModalOpen && selectedScheduleDate && (
        <ScheduleEditModal
          date={selectedScheduleDate}
          events={getEventsForDate(selectedScheduleDate)}
          onClose={handleScheduleModalClose}
          onSave={handleScheduleSave}
          onScheduleClick={handleScheduleClick}
          refetch={refetch}
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

// 일정 편집 모달 컴포넌트 (갤럭시 캘린더 스타일)
const ScheduleEditModal = ({ date, events: initialEvents, onClose, onScheduleClick, refetch }) => {
  // 로컬 일정 목록 (추가 시 즉시 반영)
  const [localEvents, setLocalEvents] = useState(initialEvents || []);
  
  // 현재 시간 기준 자동 세팅 함수
  const getDefaultTimes = () => {
    const now = new Date();
    const startHour = now.getHours();
    const startMinute = Math.ceil(now.getMinutes() / 15) * 15; // 15분 단위로 반올림
    const startTime = `${String(startHour).padStart(2, '0')}:${String(startMinute % 60).padStart(2, '0')}`;
    
    const endHour = startMinute >= 45 ? startHour + 2 : startHour + 1;
    const endMinute = startMinute >= 45 ? 0 : startMinute;
    const endTime = `${String(endHour % 24).padStart(2, '0')}:${String(endMinute).padStart(2, '0')}`;
    
    return { startTime, endTime };
  };

  // UTC 변환 없이 로컬 날짜를 YYYY-MM-DD 포맷으로 반환
  const formatDateString = (d) => {
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [startDate, setStartDate] = useState(formatDateString(date));
  const [endDate, setEndDate] = useState(formatDateString(date));
  const [startTime, setStartTime] = useState('09:00');
  const [endTime, setEndTime] = useState('10:00');
  const [isAllDay, setIsAllDay] = useState(false);
  const [showForm, setShowForm] = useState(false);

  const formatDisplayDate = (d) => {
    const dateObj = typeof d === 'string' ? new Date(d) : d;
    const year = dateObj.getFullYear();
    const month = dateObj.getMonth() + 1;
    const day = dateObj.getDate();
    const weekdays = ['일', '월', '화', '수', '목', '금', '토'];
    const weekday = weekdays[dateObj.getDay()];
    return `${year}년 ${month}월 ${day}일 (${weekday})`;
  };

  // + 버튼 클릭 시 현재 시간 기준 자동 세팅
  const handleAddNew = () => {
    const { startTime: defaultStart, endTime: defaultEnd } = getDefaultTimes();
    setStartTime(defaultStart);
    setEndTime(defaultEnd);
    setStartDate(formatDateString(date));
    setEndDate(formatDateString(date));
    setTitle('');
    setDescription('');
    setShowForm(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim()) return;
    
    const scheduleData = {
      title: title.trim(),
      description: description.trim(),
      startDate,
      endDate,
      startTime: isAllDay ? null : startTime,
      endTime: isAllDay ? null : endTime,
      isAllDay,
      type: 'schedule',
      category: '일정',
    };
    
    try {
      console.log('일정 저장 중...', scheduleData);
      const response = await createCalendarEvent(scheduleData);
      console.log('일정 저장 응답:', response.data);
      console.log('일정 저장 성공!');
      
      // 캠린더 새로고침
      await refetch();
      
      setShowForm(false);
      
      // 폼 초기화
      setTitle('');
      setDescription('');
    } catch (error) {
      console.error('일정 저장 실패:', error);
      alert('일정 저장에 실패했습니다. 다시 시도해주세요.');
    }
  };

  const handleCancel = () => {
    if (showForm) {
      setShowForm(false);
    } else {
      onClose();
    }
  };

  return createPortal(
    <>
      <div className="schedule-modal__overlay" onClick={onClose} />
      <div className="schedule-modal schedule-modal--galaxy">
        <div className="schedule-modal__header">
          <button className="schedule-modal__close" onClick={handleCancel}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
          <h3 className="schedule-modal__title">{formatDisplayDate(date)}</h3>
          {showForm ? (
            <button 
              className="schedule-modal__save" 
              onClick={handleSubmit}
              disabled={!title.trim()}
            >
              저장
            </button>
          ) : (
            <button className="schedule-modal__add-btn" onClick={handleAddNew}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
            </button>
          )}
        </div>

        {!showForm ? (
          <>
            {/* 기존 일정 목록 - 종일 먼저, 그 다음 시간순 정렬 */}
            {localEvents && localEvents.length > 0 ? (
              <div className="schedule-modal__events">
                <ul className="schedule-modal__events-list">
                  {[...localEvents]
                    .sort((a, b) => {
                      // 종일 일정을 가장 위에
                      if (a.isAllDay && !b.isAllDay) return -1;
                      if (!a.isAllDay && b.isAllDay) return 1;
                      // 둘 다 종일이면 제목순
                      if (a.isAllDay && b.isAllDay) return a.title.localeCompare(b.title);
                      // 시간순 정렬
                      return (a.startTime || '').localeCompare(b.startTime || '');
                    })
                    .map((event) => (
                    <li 
                      key={event.id} 
                      className="schedule-modal__event-item"
                      onClick={() => onScheduleClick(event.id)}
                    >
                      <div className="schedule-modal__event-indicator" />
                      <div className="schedule-modal__event-content">
                        <span className="schedule-modal__event-title">{event.title}</span>
                        <span className="schedule-modal__event-time">
                          {event.isAllDay ? '종일' : `${event.startTime} - ${event.endTime}`}
                        </span>
                      </div>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="9 18 15 12 9 6" />
                      </svg>
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <div className="schedule-modal__empty">
                <div className="schedule-modal__empty-icon">📅</div>
                <p>등록된 일정이 없습니다</p>
              </div>
            )}
          </>
        ) : (
          /* 새 일정 추가 폼 */
          <form className="schedule-modal__form" onSubmit={handleSubmit}>
            <div className="schedule-modal__field">
              <input
                type="text"
                className="schedule-modal__input schedule-modal__input--title"
                placeholder="일정 제목"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                autoFocus
              />
            </div>

            {/* 종일 토글 */}
            <div className="schedule-modal__toggle-row">
              <span className="schedule-modal__toggle-label">종일</span>
              <label className="schedule-modal__toggle">
                <input 
                  type="checkbox" 
                  checked={isAllDay} 
                  onChange={(e) => setIsAllDay(e.target.checked)} 
                />
                <span className="schedule-modal__toggle-slider" />
              </label>
            </div>

            {/* 시작일/시간 */}
            <div className="schedule-modal__datetime-row">
              <div className="schedule-modal__datetime-label">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <polyline points="12 6 12 12 16 14" />
                </svg>
                <span>시작</span>
              </div>
              <div className="schedule-modal__datetime-inputs">
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => {
                    setStartDate(e.target.value);
                    if (e.target.value > endDate) setEndDate(e.target.value);
                  }}
                  required
                />
                {!isAllDay && (
                  <input
                    type="time"
                    value={startTime}
                    onChange={(e) => setStartTime(e.target.value)}
                    required
                  />
                )}
              </div>
            </div>

            {/* 종료일/시간 */}
            <div className="schedule-modal__datetime-row">
              <div className="schedule-modal__datetime-label">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <polyline points="12 6 12 12 16 14" />
                </svg>
                <span>종료</span>
              </div>
              <div className="schedule-modal__datetime-inputs">
                <input
                  type="date"
                  value={endDate}
                  min={startDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  required
                />
                {!isAllDay && (
                  <input
                    type="time"
                    value={endTime}
                    onChange={(e) => setEndTime(e.target.value)}
                    required
                  />
                )}
              </div>
            </div>

            {/* 메모 */}
            <div className="schedule-modal__field">
              <div className="schedule-modal__memo-header">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="16" y1="13" x2="8" y2="13" />
                  <line x1="16" y1="17" x2="8" y2="17" />
                </svg>
                <span>메모</span>
              </div>
              <textarea
                className="schedule-modal__textarea"
                placeholder="메모 (선택사항)"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
              />
            </div>
          </form>
        )}
      </div>
    </>,
    document.body
  );
};

export default Calendar;
