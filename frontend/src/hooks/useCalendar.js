import { useState, useEffect, useCallback } from 'react';
import { getCalendarDates, addMonths } from '../utils/dateUtils';
import { getMonthlyEvents } from '../services/calendarService';

export const useCalendar = () => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  // 캘린더 날짜 배열 생성
  const dates = getCalendarDates(year, month);

  // 월별 이벤트 조회
  const fetchMonthlyEvents = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getMonthlyEvents(year, month + 1); // month는 0-based이므로 +1
      setEvents(data || []);
    } catch (err) {
      setError(err.message || '이벤트를 불러오는데 실패했습니다.');
      console.error('Failed to fetch monthly events:', err);
    } finally {
      setLoading(false);
    }
  }, [year, month]);

  // 월 변경 시 이벤트 조회
  useEffect(() => {
    fetchMonthlyEvents();
  }, [fetchMonthlyEvents]);

  // 이전 달로 이동
  const goToPreviousMonth = useCallback(() => {
    setCurrentDate(prev => addMonths(prev, -1));
  }, []);

  // 다음 달로 이동
  const goToNextMonth = useCallback(() => {
    setCurrentDate(prev => addMonths(prev, 1));
  }, []);

  // 특정 연/월로 이동
  const goToMonth = useCallback((year, month) => {
    setCurrentDate(new Date(year, month, 1));
  }, []);

  // 오늘로 이동
  const goToToday = useCallback(() => {
    const today = new Date();
    setCurrentDate(today);
    setSelectedDate(today);
  }, []);

  // 날짜 선택
  const selectDate = useCallback((date) => {
    setSelectedDate(date);
  }, []);

  // 특정 날짜의 이벤트 가져오기
  const getEventsForDate = useCallback((date) => {
    return events.filter(event => {
      const eventDate = new Date(event.date);
      return (
        eventDate.getFullYear() === date.getFullYear() &&
        eventDate.getMonth() === date.getMonth() &&
        eventDate.getDate() === date.getDate()
      );
    });
  }, [events]);

  // 이벤트가 있는 날짜인지 확인
  const hasEventsOnDate = useCallback((date) => {
    return getEventsForDate(date).length > 0;
  }, [getEventsForDate]);

  return {
    currentDate,
    selectedDate,
    dates,
    events,
    loading,
    error,
    goToPreviousMonth,
    goToNextMonth,
    goToMonth,
    goToToday,
    selectDate,
    getEventsForDate,
    hasEventsOnDate,
    refetch: fetchMonthlyEvents,
  };
};