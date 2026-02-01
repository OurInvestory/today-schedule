import { useState, useEffect, useCallback } from 'react';
import { getCalendarDates, addMonths } from '../utils/dateUtils';
import { getMonthlyEvents } from '../services/calendarService';
import { getTodos } from '../services/todoService';

export const useCalendar = () => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [events, setEvents] = useState([]);
  const [googleEvents, setGoogleEvents] = useState([]);
  const [todos, setTodos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  // 캘린더 날짜 배열 생성
  const dates = getCalendarDates(year, month);

  // 월별 일정(Schedule) 조회 - 구글 포함 모든 일정
  const fetchMonthlyEvents = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const schedules = await getMonthlyEvents(year, month + 1); // month는 0-based이므로 +1

      // 일정 필터링 (event, task, schedule 타입 모두 포함)
      // 구글 일정도 포함 (source 필터링 제거)
      const allSchedules = schedules.filter(item => {
        // type이 'event', 'task', 'schedule' 또는 type이 없는 경우
        const isScheduleType = !item.type || ['event', 'task', 'schedule'].includes(item.type);
        return isScheduleType;
      });

      console.log('가져온 일정 목록 (구글 포함):', allSchedules);
      setEvents(allSchedules);
      
      // 구글 일정만 별도로 저장 (indicator용)
      const googleOnly = allSchedules.filter(item => item.source === 'google' || item.isGoogleEvent);
      setGoogleEvents(googleOnly);
    } catch (error) {
      setError(error);
    } finally {
      setLoading(false);
    }
  }, [year, month]);

  // 할 일(Todo) 조회 - 캘린더에서 할 일 아이콘 표시용
  const fetchTodos = useCallback(async () => {
    try {
      // 현재 캘린더에서 보는 달의 할 일 조회
      const from = new Date(year, month, 1).toISOString().split('T')[0];
      const to = new Date(year, month + 1, 0).toISOString().split('T')[0];
      
      const data = await getTodos({ from, to });
      // 할 일(Todo)만 필터링 (type이 'todo'이거나 type 필드가 없는 경우)
      const todosOnly = (data || []).filter(item => !item.type || item.type === 'todo');
      console.log('캘린더 할 일 조회:', todosOnly);
      setTodos(todosOnly);
    } catch (err) {
      console.error('Failed to fetch todos for calendar:', err);
      setTodos([]);
    }
  }, [year, month]);

  // 구글 캘린더 일정은 fetchMonthlyEvents에서 함께 처리됨
  // 별도 호출 불필요

  // 월 변경 시 데이터 조회
  useEffect(() => {
    fetchMonthlyEvents();
    fetchTodos();
  }, [fetchMonthlyEvents, fetchTodos]);

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

  // 특정 날짜의 이벤트 가져오기 (시작일~마감일 사이 모든 날짜 포함)
  const getEventsForDate = useCallback((date) => {
    const targetDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());
    
    return events.filter(event => {
      // startDate, date, start_at 순서로 시작일 추출
      const startDateStr = event.start_at || event.startDate || event.date;
      // endDate, end_at 순서로 마감일 추출
      const endDateStr = event.end_at || event.endDate || startDateStr;
      
      if (!startDateStr) return false;
      
      // 날짜 파싱
      const startDate = new Date(startDateStr);
      const endDate = new Date(endDateStr);
      
      // 시간 부분 제거하여 날짜만 비교
      const startOnly = new Date(startDate.getFullYear(), startDate.getMonth(), startDate.getDate());
      const endOnly = new Date(endDate.getFullYear(), endDate.getMonth(), endDate.getDate());
      
      // targetDate가 시작일과 마감일 사이에 있는지 확인
      return targetDate >= startOnly && targetDate <= endOnly;
    });
  }, [events]);

  // 특정 날짜의 할 일 가져오기
  const getTodosForDate = useCallback((date) => {
    return todos.filter(todo => {
      // dueDate 또는 date 필드 사용
      const todoDateStr = todo.dueDate || todo.date;
      if (!todoDateStr) return false;
      
      // 날짜 문자열에서 날짜 부분만 추출 (YYYY-MM-DD)
      const datePart = typeof todoDateStr === 'string' ? todoDateStr.split('T')[0] : null;
      if (!datePart) return false;
      
      const [yearStr, monthStr, dayStr] = datePart.split('-');
      return (
        parseInt(yearStr) === date.getFullYear() &&
        parseInt(monthStr) === date.getMonth() + 1 &&
        parseInt(dayStr) === date.getDate()
      );
    });
  }, [todos]);

  // 이벤트(일정)가 있는 날짜인지 확인
  const hasEventsOnDate = useCallback((date) => {
    return getEventsForDate(date).length > 0;
  }, [getEventsForDate]);

  // 특정 날짜에 할 일이 있는지 확인
  const hasTodosOnDate = useCallback((date) => {
    return getTodosForDate(date).length > 0;
  }, [getTodosForDate]);

  // 특정 날짜에 완료된 할 일이 있는지 확인
  const hasCompletedTodosOnDate = useCallback((date) => {
    return getTodosForDate(date).some(todo => todo.completed);
  }, [getTodosForDate]);

  // 특정 날짜에 미완료 할 일이 있는지 확인
  const hasPendingTodosOnDate = useCallback((date) => {
    return getTodosForDate(date).some(todo => !todo.completed);
  }, [getTodosForDate]);

  // 특정 날짜에 구글 캘린더 일정이 있는지 확인
  const hasGoogleEventsOnDate = useCallback((date) => {
    return googleEvents.some(event => {
      const eventDate = new Date(event.date || event.end_at);
      return (
        eventDate.getFullYear() === date.getFullYear() &&
        eventDate.getMonth() === date.getMonth() &&
        eventDate.getDate() === date.getDate()
      );
    });
  }, [googleEvents]);

  // 일정과 할 일 모두 새로고침
  const refetch = useCallback(() => {
    fetchMonthlyEvents();
    fetchTodos();
  }, [fetchMonthlyEvents, fetchTodos]);

  return {
    currentDate,
    selectedDate,
    dates,
    events,
    todos,
    loading,
    error,
    goToPreviousMonth,
    goToNextMonth,
    goToMonth,
    goToToday,
    selectDate,
    getEventsForDate,
    getTodosForDate,
    hasEventsOnDate,
    hasTodosOnDate,
    hasCompletedTodosOnDate,
    hasPendingTodosOnDate,
    hasGoogleEventsOnDate,
    refetch,
  };
};