// Todo 서비스 - 로컬 스토리지 기반 (백엔드 없이 동작)
const STORAGE_KEY = 'todos';

// 샘플 데이터
const sampleTodos = [
  {
    id: '1',
    title: '프로그래밍 과제 제출',
    description: '알고리즘 문제 풀이 과제',
    startDate: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 2일 전부터
    dueDate: new Date(Date.now() + 1 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 내일 마감
    category: 'assignment',
    importance: 9,
    estimatedTime: 3,
    completed: false,
    createdAt: new Date().toISOString(),
  },
  {
    id: '2',
    title: '팀 프로젝트 회의',
    description: '졸업 프로젝트 진행 상황 공유',
    startDate: new Date().toISOString().split('T')[0], // 오늘부터
    dueDate: new Date().toISOString().split('T')[0], // 오늘 마감
    category: 'meeting',
    importance: 7,
    estimatedTime: 2,
    completed: false,
    createdAt: new Date().toISOString(),
  },
  {
    id: '3',
    title: '도서관 책 반납',
    description: '대출 기한 만료 전 반납',
    startDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 일주일 전부터
    dueDate: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 3일 후 마감
    category: 'personal',
    importance: 5,
    estimatedTime: 1,
    completed: true,
    createdAt: new Date().toISOString(),
  },
];

// 지연 시뮬레이션 함수
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// 로컬 스토리지에서 todos 가져오기
const getStoredTodos = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      return JSON.parse(stored);
    }
    // 처음 실행 시 샘플 데이터 저장
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sampleTodos));
    return sampleTodos;
  } catch (error) {
    console.error('Error reading todos from storage:', error);
    return sampleTodos;
  }
};

// 로컬 스토리지에 todos 저장
const saveTodos = (todos) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(todos));
  } catch (error) {
    console.error('Error saving todos to storage:', error);
  }
};

/**
 * Todo 목록 조회
 */
export const getTodos = async (params = {}) => {
  await delay(100);
  let todos = getStoredTodos();

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
  await delay(100);
  const todos = getStoredTodos();
  const todo = todos.find(t => t.id === id);
  if (!todo) {
    throw new Error('Todo not found');
  }
  return todo;
};

/**
 * Todo 생성
 */
export const createTodo = async (todoData) => {
  await delay(100);
  const todos = getStoredTodos();
  
  const newTodo = {
    id: Date.now().toString(),
    ...todoData,
    dueDate: todoData.dueDate || new Date().toISOString().split('T')[0],
    completed: false,
    createdAt: new Date().toISOString(),
  };
  
  todos.push(newTodo);
  saveTodos(todos);
  
  return newTodo;
};

/**
 * Todo 수정
 */
export const updateTodo = async (id, todoData) => {
  await delay(100);
  const todos = getStoredTodos();
  const index = todos.findIndex(t => t.id === id);
  
  if (index === -1) {
    throw new Error('Todo not found');
  }
  
  todos[index] = { ...todos[index], ...todoData, updatedAt: new Date().toISOString() };
  saveTodos(todos);
  
  return todos[index];
};

/**
 * Todo 부분 수정 (PATCH)
 */
export const patchTodo = async (id, partialData) => {
  return updateTodo(id, partialData);
};

/**
 * Todo 삭제
 */
export const deleteTodo = async (id) => {
  await delay(100);
  const todos = getStoredTodos();
  const filteredTodos = todos.filter(t => t.id !== id);
  
  if (filteredTodos.length === todos.length) {
    throw new Error('Todo not found');
  }
  
  saveTodos(filteredTodos);
  return { success: true };
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
  const allTodos = getStoredTodos();
  
  return allTodos.filter(todo => {
    // 완료된 할 일도 표시 (완료 상태는 UI에서 구분)
    // 마감일이 오늘 이후이거나 오늘인 것만 (지난 것은 제외하지 않고 긴급으로 표시)
    // 시작일이 있으면 시작일이 오늘 이전이거나 오늘인 것만
    const startDate = todo.startDate;
    const dueDate = todo.dueDate;
    
    // 시작일 체크: 시작일이 없거나, 시작일이 오늘 이전/오늘이면 OK
    const canStart = !startDate || startDate <= today;
    
    // 마감일 체크: 마감일이 없거나, 마감일이 아직 지나지 않았거나 오늘이면 표시
    // (지난 것도 표시해서 긴급하게 처리하도록)
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
  const allTodos = getStoredTodos();
  
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