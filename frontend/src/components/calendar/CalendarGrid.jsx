import React, { useMemo } from 'react';
import DateCell from './DateCell';
import { WEEKDAYS } from '../../utils/constants';
import { isSameDay, formatDate } from '../../utils/dateUtils';
import './CalendarGrid.css';

// 멀티데이 이벤트를 주별로 분할하는 함수
const getMultiDayEventsForWeek = (weekDates, events) => {
  const multiDayEvents = [];
  
  events.forEach(event => {
    const startDate = new Date(event.start_at || event.startDate || event.date);
    const endDate = new Date(event.end_at || event.endDate || event.date);
    
    // 시작일과 마감일이 다른 경우만 멀티데이 이벤트로 처리
    if (startDate.toDateString() === endDate.toDateString()) return;
    
    const weekStart = weekDates[0].date;
    const weekEnd = weekDates[6].date;
    
    // 이벤트가 이번 주와 겹치는지 확인
    if (endDate < weekStart || startDate > weekEnd) return;
    
    // 이번 주에서 이벤트가 차지하는 범위 계산
    let startCol = 0;
    let endCol = 6;
    
    for (let i = 0; i < 7; i++) {
      const cellDate = weekDates[i].date;
      if (isSameDay(cellDate, startDate) || (startDate < cellDate && i === 0)) {
        startCol = startDate < weekStart ? 0 : i;
      }
      if (isSameDay(cellDate, endDate) || (endDate > cellDate && i === 6)) {
        endCol = endDate > weekEnd ? 6 : i;
      }
    }
    
    // 시작일이 이번 주 전인지 확인
    const startsBeforeWeek = startDate < weekStart;
    // 마감일이 이번 주 후인지 확인
    const endsAfterWeek = endDate > weekEnd;
    
    multiDayEvents.push({
      ...event,
      startCol,
      endCol,
      span: endCol - startCol + 1,
      isStart: !startsBeforeWeek && weekDates.some(d => isSameDay(d.date, startDate)),
      isEnd: !endsAfterWeek && weekDates.some(d => isSameDay(d.date, endDate)),
      isContinuation: startsBeforeWeek,
      continuesNext: endsAfterWeek,
    });
  });
  
  return multiDayEvents;
};

// 카테고리별 색상 매핑 (일정 색상이 없을 때 기본값)
const getCategoryColor = (category) => {
  const colors = {
    assignment: '#3b82f6',
    exam: '#ef4444',
    class: '#8b5cf6',
    meeting: '#f59e0b',
    personal: '#10b981',
    other: '#6b7280',
  };
  return colors[category] || colors.other;
};

// 이벤트 색상 가져오기 (event.color 우선, 없으면 카테고리 색상)
const getEventColor = (event) => {
  if (event.source === 'google') return '#ea4335';
  if (event.color) return event.color;
  return getCategoryColor(event.category);
};

const CalendarGrid = ({ dates, selectedDate, onDateClick, onDateDoubleClick, hasEventsOnDate, hasCompletedOnDate, hasPendingOnDate, hasGoogleEventsOnDate = () => false, isFullMode = false, getEventsForDate, getTodosForDate, allEvents = [] }) => {
  // 주별로 날짜 분할
  const weeks = useMemo(() => {
    const result = [];
    for (let i = 0; i < dates.length; i += 7) {
      result.push(dates.slice(i, i + 7));
    }
    return result;
  }, [dates]);

  // 각 주의 멀티데이 이벤트 계산
  const multiDayEventsByWeek = useMemo(() => {
    return weeks.map(weekDates => getMultiDayEventsForWeek(weekDates, allEvents));
  }, [weeks, allEvents]);

  // 단일 날짜 이벤트만 필터링 (멀티데이 제외)
  const getSingleDayEventsForDate = (date) => {
    if (!getEventsForDate) return [];
    const events = getEventsForDate(date);
    return events.filter(event => {
      const startDate = new Date(event.start_at || event.startDate || event.date);
      const endDate = new Date(event.end_at || event.endDate || event.date);
      return startDate.toDateString() === endDate.toDateString();
    });
  };

  // 해당 날짜에 멀티데이 이벤트가 있는지 확인
  const hasMultiDayEventOnDate = (date) => {
    return allEvents.some(event => {
      const startDate = new Date(event.start_at || event.startDate || event.date);
      const endDate = new Date(event.end_at || event.endDate || event.date);
      if (startDate.toDateString() === endDate.toDateString()) return false;
      return date >= startDate && date <= endDate;
    });
  };

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

      {/* Date cells with multi-day events */}
      <div className="calendar-grid__weeks">
        {weeks.map((weekDates, weekIndex) => (
          <div key={weekIndex} className="calendar-grid__week">
            {/* 멀티데이 이벤트 바 영역 */}
            {isFullMode && multiDayEventsByWeek[weekIndex]?.length > 0 && (
              <div className="calendar-grid__multiday-events">
                {multiDayEventsByWeek[weekIndex].map((event, eventIndex) => (
                  <div
                    key={`${event.schedule_id || event.id}-${eventIndex}`}
                    className={`calendar-grid__multiday-bar ${event.isStart ? 'calendar-grid__multiday-bar--start' : ''} ${event.isEnd ? 'calendar-grid__multiday-bar--end' : ''}`}
                    style={{
                      gridColumn: `${event.startCol + 1} / span ${event.span}`,
                      backgroundColor: getEventColor(event),
                    }}
                    title={`${event.title} (${formatDate(new Date(event.start_at || event.startDate), 'MM/DD')} ~ ${formatDate(new Date(event.end_at || event.endDate), 'MM/DD')})`}
                  >
                    {event.source === 'google' && <span className="multiday-bar__google-icon">G</span>}
                    <span className="multiday-bar__title">{event.title}</span>
                  </div>
                ))}
              </div>
            )}
            
            {/* 날짜 셀들 */}
            <div className="calendar-grid__dates-row">
              {weekDates.map((dateObj, index) => (
                <DateCell
                  key={index}
                  date={dateObj.date}
                  isCurrentMonth={dateObj.isCurrentMonth}
                  isSelected={isSameDay(dateObj.date, selectedDate)}
                  hasEvents={hasEventsOnDate(dateObj.date)}
                  hasMultiDayEvent={hasMultiDayEventOnDate(dateObj.date)}
                  hasCompleted={hasCompletedOnDate ? hasCompletedOnDate(dateObj.date) : false}
                  hasPending={hasPendingOnDate ? hasPendingOnDate(dateObj.date) : false}
                  hasGoogleEvents={hasGoogleEventsOnDate(dateObj.date)}
                  onClick={onDateClick}
                  onDoubleClick={onDateDoubleClick}
                  isFullMode={isFullMode}
                  events={isFullMode ? getSingleDayEventsForDate(dateObj.date) : (getEventsForDate ? getEventsForDate(dateObj.date) : [])}
                  todos={getTodosForDate ? getTodosForDate(dateObj.date) : []}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CalendarGrid;
