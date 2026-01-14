import api from './api';

/**
 * 날짜 기반 우선순위 계산 함수
 * - 날짜가 임박할수록 높은 점수
 * - schedule_id가 있으면 추가 가산점
 */
const calculatePriority = (dueDate, hasSchedule = false) => {
  if (!dueDate) return hasSchedule ? 4 : 3; // 기본 중간 우선순위
  
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  const due = new Date(dueDate);
  due.setHours(0, 0, 0, 0);
  
  const diffDays = Math.ceil((due - today) / (1000 * 60 * 60 * 24));
  
  let priority;
  if (diffDays < 0) {
    // 마감 지남 - 우선순위 5로 낮춤
    priority = 5;
  } else if (diffDays === 0) {
    // 오늘 마감
    priority = 9;
  } else if (diffDays === 1) {
    // 내일 마감
    priority = 8;
  } else if (diffDays <= 3) {
    // 2-3일 남음
    priority = 7;
  } else if (diffDays <= 7) {
    // 4-7일 남음
    priority = 6;
  } else if (diffDays <= 14) {
    // 1-2주 남음
    priority = 5;
  } else if (diffDays <= 30) {
    // 2주-1개월 남음
    priority = 4;
  } else {
    // 1개월 이상 남음
    priority = 3;
  }
  
  // schedule_id가 있으면 +1 가산점
  if (hasSchedule) {
    priority += 1;
  }
  
  // 최소 1, 최대 10으로 제한
  return Math.min(10, Math.max(1, priority));
};

/**
 * 우선순위 점수를 레이블로 변환
 */
const getPriorityLabel = (score) => {
  if (score >= 7) return 'high';
  if (score >= 4) return 'medium';
  return 'low';
};

/**
 * Fetch all todos from the backend.
 */
export const fetchTodos = async () => {
  try {
    const today = new Date();
    const from = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split('T')[0];
    const to = new Date(today.getFullYear(), today.getMonth() + 1, 0).toISOString().split('T')[0];

    const response = await api.get('/api/sub-tasks', {
      params: { from, to },
    });

    // 백엔드 응답을 프론트엔드 형식으로 변환
    return (response.data.data || []).map(todo => {
      // 프론트에서 자체적으로 계산한 우선순위 (1-10 범위 보장)
      const priorityScore = Math.min(10, Math.max(1, calculatePriority(todo.date, !!todo.schedule_id)));
      const priority = getPriorityLabel(priorityScore);
      
      return {
        ...todo,
        id: todo.sub_task_id || todo.id,
        title: todo.title,
        dueDate: todo.date,
        completed: todo.is_done === true, // is_done 필드를 completed로 매핑
        estimatedMinute: todo.estimated_minute,
        scheduleId: todo.schedule_id,
        tip: todo.tip,
        category: todo.category || 'other', // 카테고리 없으면 기타
        priority, // 계산된 우선순위 레이블
        priorityScore, // 우선순위 점수 (1-10)
      };
    });
  } catch (error) {
    console.error('Failed to fetch todos:', error);
    throw error;
  }
};

/**
 * Create a new todo.
 * @param {Object} todoData - The data for the new todo.
 */
export const createTodo = async (todoData) => {
  try {
    // 독립적인 할 일은 sub-tasks API 사용
    // 백엔드 POST API 스펙: schedule_id, title, date, estimated_minute, priority, category 전송
    const payload = {
      title: todoData.title,
      date: todoData.dueDate || todoData.date, // dueDate 또는 date 필드 사용
      estimated_minute: todoData.estimatedMinute || 60,
      priority: todoData.priority || 'medium',
      category: todoData.category || 'other',
    };
    
    // schedule_id가 있을 때만 포함
    if (todoData.scheduleId) {
      payload.schedule_id = todoData.scheduleId;
    }

    console.log('할 일 생성 요청:', payload);
    const response = await api.post('/api/sub-tasks', payload);
    console.log('할 일 생성 응답:', response.data);
    return response;
  } catch (error) {
    console.error('Failed to create todo:', error);
    throw error;
  }
};

/**
 * Update an existing todo.
 * @param {string} id - The ID of the todo to update.
 * @param {Object} todoData - The updated data for the todo.
 */
export const updateTodo = async (id, todoData) => {
  try {
    const payload = {};
    
    // 백엔드 PUT API 스펙: title, date, estimated_minute, is_done, priority, category 수정 가능
    if (todoData.title !== undefined) payload.title = todoData.title;
    if (todoData.dueDate !== undefined) payload.date = todoData.dueDate;
    if (todoData.completed !== undefined) payload.is_done = todoData.completed;
    if (todoData.estimatedMinute !== undefined) payload.estimated_minute = todoData.estimatedMinute;
    if (todoData.priority !== undefined) payload.priority = todoData.priority;
    if (todoData.category !== undefined) payload.category = todoData.category;

    console.log('Todo 수정 요청:', { id, payload });
    const response = await api.put(`/api/sub-tasks/${id}`, payload);
    return response;
  } catch (error) {
    console.error('Failed to update todo:', error);
    throw error;
  }
};

/**
 * Delete a todo by ID.
 * @param {string} id - The ID of the todo to delete.
 */
export const deleteTodo = async (id) => {
  try {
    const response = await api.delete(`/api/sub-tasks/${id}`);
    return response;
  } catch (error) {
    console.error('Failed to delete todo:', error);
    throw error;
  }
};

/**
 * Todo 목록 조회
 */
export const getTodos = async (params = {}) => {
  let todos = await fetchTodos();

  // 필터 적용
  if (params.date) {
    todos = todos.filter(todo => {
      const todoDate = todo.dueDate ? todo.dueDate.split('T')[0] : null;
      return todoDate === params.date;
    });
  }
  if (params.category) {
    todos = todos.filter(todo => todo.category === params.category);
  }
  if (params.completed !== undefined) {
    todos = todos.filter(todo => todo.completed === params.completed);
  }
  if (params.priority) {
    todos = todos.filter(todo => {
      // priority 필드를 기준으로 필터링
      return todo.priority === params.priority;
    });
  }

  return todos;
};

/**
 * Todo 상세 조회
 */
export const getTodoById = async (id) => {
  const todos = await fetchTodos();
  const todo = todos.find(t => t.id === id);
  if (!todo) {
    throw new Error('Todo not found');
  }
  return todo;
};

/**
 * Todo 부분 수정 (PATCH)
 */
export const patchTodo = async (id, partialData) => {
  return updateTodo(id, partialData);
};

/**
 * Todo 완료 토글
 */
export const toggleTodoComplete = async (id, completed, todoData) => {
  try {
    // 백엔드 PUT API는 모든 필드를 요구할 수 있으므로 기존 데이터와 함께 전송
    const payload = {
      title: todoData?.title,
      date: todoData?.dueDate,
      estimated_minute: todoData?.estimatedMinute,
      is_done: completed
    };
    
    console.log('Todo 완료 토글 요청:', { id, payload });
    const response = await api.put(`/api/sub-tasks/${id}`, payload);
    console.log('Todo 완료 토글 응답:', response.data);
    
    // 응답 성공 여부 확인
    if (response.status !== 200 && response.data?.status !== 200) {
      throw new Error(response.data?.message || 'Todo 완료 상태 변경에 실패했습니다.');
    }
    
    return response;
  } catch (error) {
    console.error('Failed to toggle todo complete:', error);
    console.error('Error response:', error.response?.data);
    throw error;
  }
};

/**
 * 오늘의 할 일 조회
 * - 오늘 날짜에 해당하는 할 일만 표시
 */
export const getTodayTodos = async () => {
  const today = new Date().toISOString().split('T')[0];
  const allTodos = await fetchTodos();

  return allTodos.filter(todo => {
    // 오늘 날짜와 정확히 일치하는 할일만 표시
    const todoDate = todo.dueDate ? todo.dueDate.split('T')[0] : null;
    return todoDate === today;
  });
};

/**
 * 특정 날짜의 할 일 조회 (날짜가 정확히 일치하는 것만)
 */
export const getTodosByDate = async (date) => {
  const allTodos = await fetchTodos();

  return allTodos.filter(todo => {
    // 날짜 필드와 정확히 일치하는 할일만 표시
    const todoDate = todo.dueDate ? todo.dueDate.split('T')[0] : null;
    return todoDate === date;
  });
};

/**
 * 카테고리별 할 일 조회
 */
export const getTodosByCategory = async (category) => {
  return getTodos({ category });
};

/**
 * 우선순위별 할 일 조회
 */
export const getTodosByPriority = async (priority) => {
  return getTodos({ priority });
};

export default {
  getTodos,
  getTodoById,
  createTodo,
  updateTodo,
  patchTodo,
  deleteTodo,
  toggleTodoComplete,
  getTodayTodos,
  getTodosByDate,
  getTodosByCategory,
  getTodosByPriority,
};