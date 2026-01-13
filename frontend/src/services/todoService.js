import api from './api';

/**
 * Fetch all todos from the backend.
 */
export const fetchTodos = async () => {
  try {
    const today = new Date();
    const from = new Date(today.getFullYear(), today.getMonth(), 1).toISOString();
    const to = new Date(today.getFullYear(), today.getMonth() + 1, 0).toISOString();

    const response = await api.get('/schedules', {
      params: { from, to },
    });

    return (response.data.data || []).map(todo => ({
      ...todo,
      priority: mapPriority(todo.priority_score),
    }));
  } catch (error) {
    console.error('Failed to fetch todos:', error);
    throw error;
  }
};

const mapPriority = (score) => {
  if (score >= 8) return 'high';
  if (score >= 4) return 'medium';
  return 'low';
}

/**
 * Create a new todo.
 * @param {Object} todoData - The data for the new todo.
 */
export const createTodo = async (todoData) => {
  try {
    const response = await api.post('/schedules', {
      title: todoData.title,
      description: todoData.description,
      priority_score: todoData.priority, // API 명세서에 맞게 수정
      due_date: todoData.dueDate,       // API 명세서에 맞게 수정
    });
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
    const response = await api.put(`/schedules/${id}`, todoData);
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
    const response = await api.delete(`/schedules/${id}`);
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
    todos = todos.filter(todo => todo.dueDate === params.date);
  }
  if (params.category) {
    todos = todos.filter(todo => todo.category === params.category);
  }
  if (params.completed !== undefined) {
    todos = todos.filter(todo => todo.completed === params.completed);
  }
  if (params.priority) {
    todos = todos.filter(todo => {
      if (params.priority === 'high') return todo.importance >= 7;
      if (params.priority === 'medium') return todo.importance >= 4 && todo.importance < 7;
      if (params.priority === 'low') return todo.importance < 4;
      return true;
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
export const toggleTodoComplete = async (id, completed) => {
  return patchTodo(id, { completed });
};

/**
 * 오늘의 할 일 조회 (AI 우선순위 기반)
 * - 마감일이 지나지 않은 미완료 할 일
 * - 시작일이 오늘 이전인 할 일 (시작일이 없으면 포함)
 * - 우선순위 점수로 정렬 (useTodo에서 처리)
 */
export const getTodayTodos = async () => {
  const today = new Date().toISOString().split('T')[0];
  const allTodos = await fetchTodos();

  return allTodos.filter(todo => {
    const startDate = todo.startDate;
    const dueDate = todo.dueDate;

    const canStart = !startDate || startDate <= today;
    const isRelevant = !dueDate || dueDate >= today || !todo.completed;

    return canStart && (isRelevant || !todo.completed);
  });
};

/**
 * 특정 날짜의 할 일 조회 (AI 우선순위 기반)
 * - 해당 날짜에 할 수 있는 할 일 (시작일 <= 해당 날짜 <= 마감일)
 * - 미완료 상태인 것
 */
export const getTodosByDate = async (date) => {
  const allTodos = await fetchTodos();

  return allTodos.filter(todo => {
    const startDate = todo.startDate;
    const dueDate = todo.dueDate;

    // 시작일 체크: 시작일이 없거나, 시작일이 해당 날짜 이전/같으면 OK
    const canStart = !startDate || startDate <= date;

    // 마감일 체크: 마감일이 없거나, 마감일이 해당 날짜 이후/같으면 OK
    // 마감일이 지났어도 미완료면 표시
    const isRelevant = !dueDate || dueDate >= date || !todo.completed;

    return canStart && isRelevant;
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