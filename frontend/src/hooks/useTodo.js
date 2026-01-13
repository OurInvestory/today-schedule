import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  getTodos,
  getTodayTodos,
  getTodosByDate,
  createTodo,
  updateTodo,
  deleteTodo,
  toggleTodoComplete,
} from '../services/todoService';
import { assignPriority, sortByPriority } from '../utils/priorityUtils';

export const useTodo = (initialFilter = {}) => {
  const [allTodos, setAllTodos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState(initialFilter);

  // Todo 목록 조회
  const fetchTodos = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      let data;
      if (filter.date === 'today') {
        data = await getTodayTodos();
      } else if (filter.date) {
        data = await getTodosByDate(filter.date);
      } else {
        data = await getTodos({});
      }
      
      // 할 일(Todo)만 필터링 (type이 'todo'이거나 type 필드가 없는 경우)
      // 일정(Schedule)은 캘린더에서만 표시됨
      const todosOnly = data.filter(item => !item.type || item.type === 'todo');
      
      // 우선순위 할당 및 정렬
      const todosWithPriority = todosOnly.map(todo => assignPriority(todo));
      const sortedTodos = sortByPriority(todosWithPriority);
      
      setAllTodos(sortedTodos);
    } catch (err) {
      setError(err.message || '할 일을 불러오는데 실패했습니다.');
      console.error('Failed to fetch todos:', err);
    } finally {
      setLoading(false);
    }
  }, [filter.date]);

  // 클라이언트 사이드 필터링 적용
  const todos = useMemo(() => {
    let filtered = [...allTodos];

    // 카테고리 필터
    if (filter.category) {
      filtered = filtered.filter(todo => todo.category === filter.category);
    }

    // 우선순위 필터
    if (filter.priority) {
      filtered = filtered.filter(todo => todo.priority === filter.priority);
    }

    // 완료 여부 필터
    if (filter.completed !== undefined) {
      filtered = filtered.filter(todo => todo.completed === filter.completed);
    }

    return filtered;
  }, [allTodos, filter.category, filter.priority, filter.completed]);

  // 초기 로드 및 날짜 필터 변경 시 조회
  useEffect(() => {
    fetchTodos();
  }, [fetchTodos]);

  // Todo 추가
  const addTodo = async (todoData) => {
    try {
      setLoading(true);
      setError(null);

      const newTodo = await createTodo({
        title: todoData.title,
        description: todoData.description,
        startDate: todoData.startDate,
        dueDate: todoData.dueDate,
        priority: todoData.priority,
      });

      await fetchTodos(); // 목록 새로고침
      return newTodo;
    } catch (err) {
      setError(err.message || '할 일 추가에 실패했습니다.');
      console.error('Failed to add todo:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Todo 수정
  const editTodo = async (id, todoData) => {
    try {
      setLoading(true);
      setError(null);
      const updatedTodo = await updateTodo(id, todoData);
      await fetchTodos(); // 목록 새로고침
      return updatedTodo;
    } catch (err) {
      setError(err.message || '할 일 수정에 실패했습니다.');
      console.error('Failed to edit todo:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Todo 삭제
  const removeTodo = async (id) => {
    try {
      setLoading(true);
      setError(null);
      await deleteTodo(id);
      await fetchTodos(); // 목록 새로고침
    } catch (err) {
      setError(err.message || '할 일 삭제에 실패했습니다.');
      console.error('Failed to remove todo:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Todo 완료 토글
  const toggleComplete = async (id, completed) => {
    try {
      // 낙관적 업데이트
      setAllTodos(prev =>
        prev.map(todo =>
          todo.id === id ? { ...todo, completed } : todo
        )
      );
      
      await toggleTodoComplete(id, completed);
      await fetchTodos(); // 목록 새로고침 (정렬 반영)
    } catch (err) {
      setError(err.message || '완료 상태 변경에 실패했습니다.');
      console.error('Failed to toggle todo complete:', err);
      await fetchTodos(); // 실패 시 원상복구
      throw err;
    }
  };

  // 필터 변경
  const updateFilter = useCallback((newFilter) => {
    setFilter(prev => ({ ...prev, ...newFilter }));
  }, []);

  // 필터 초기화
  const resetFilter = useCallback(() => {
    setFilter({});
  }, []);

  // 카테고리별 필터링
  const filterByCategory = useCallback((category) => {
    updateFilter({ category });
  }, [updateFilter]);

  // 우선순위별 필터링
  const filterByPriority = useCallback((priority) => {
    updateFilter({ priority });
  }, [updateFilter]);

  // 완료 여부별 필터링
  const filterByCompletion = useCallback((completed) => {
    updateFilter({ completed });
  }, [updateFilter]);

  // 통계 계산
  const stats = {
    total: todos.length,
    completed: todos.filter(t => t.completed).length,
    pending: todos.filter(t => !t.completed).length,
    highPriority: todos.filter(t => t.priority === 'high' && !t.completed).length,
  };

  return {
    todos,
    loading,
    error,
    filter,
    stats,
    fetchTodos,
    addTodo,
    editTodo,
    removeTodo,
    toggleComplete,
    updateFilter,
    resetFilter,
    filterByCategory,
    filterByPriority,
    filterByCompletion,
  };
};