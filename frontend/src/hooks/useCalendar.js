import { useState, useEffect, useCallback } from 'react';
import { getCalendarDates, addMonths } from '../utils/dateUtils';
import { getMonthlyEvents } from '../services/calendarService';
import { getTodos } from '../services/todoService';

export const useCalendar = () => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [events, setEvents] = useState([]);
  const [todos, setTodos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  // 캘린더 날짜 배열 생성
  const dates = getCalendarDates(year, month);

  // 월별 일정(Schedule) 조회
  const fetchMonthlyEvents = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const schedules = await getMonthlyEvents(year, month + 1); // month는 0-based이므로 +1

      // 모든 일정 표시 (백엔드 응답 확인을 위해 필터 제거)
      console.log('가져온 일정 목록:', schedules);
      setEvents(schedules);
    } catch (error) {
      setError(error);
    } finally {
      setLoading(false);
    }
  }, [year, month]);

  // 할 일(Todo) 조회 - 캘린더에서 할 일 아이콘 표시용
  const fetchTodos = useCallback(async () => {
    try {
      const data = await getTodos({});
      // 할 일(Todo)만 필터링 (type이 'todo'이거나 type 필드가 없는 경우)
      const todosOnly = (data || []).filter(item => !item.type || item.type === 'todo');
      setTodos(todosOnly);
    } catch (err) {
      console.error('Failed to fetch todos for calendar:', err);
      setTodos([]);
    }
  }, []);

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

  // 이벤트(일정)가 있는 날짜인지 확인
  const hasEventsOnDate = useCallback((date) => {
    return getEventsForDate(date).length > 0;
  }, [getEventsForDate]);

  // 특정 날짜에 할 일이 있는지 확인
  const hasTodosOnDate = useCallback((date) => {
    return todos.some(todo => {
      const todoDate = todo.dueDate ? new Date(todo.dueDate) : null;
      if (!todoDate) return false;
      return (
        todoDate.getFullYear() === date.getFullYear() &&
        todoDate.getMonth() === date.getMonth() &&
        todoDate.getDate() === date.getDate()
      );
    });
  }, [todos]);

  // 특정 날짜에 완료된 할 일이 있는지 확인
  const hasCompletedTodosOnDate = useCallback((date) => {
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
  }, [todos]);

  // 특정 날짜에 미완료 할 일이 있는지 확인
  const hasPendingTodosOnDate = useCallback((date) => {
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
  }, [todos]);

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
    hasEventsOnDate,
    hasTodosOnDate,
    hasCompletedTodosOnDate,
    hasPendingTodosOnDate,
    refetch,
  };
};