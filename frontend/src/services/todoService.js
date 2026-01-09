import api from './api';
import { API_ENDPOINTS } from '../utils/constants';

/**
 * Todo 목록 조회
 */
export const getTodos = async (params = {}) => {
  try {
    const response = await api.get(API_ENDPOINTS.TODOS, { params });
    return response;
  } catch (error) {
    console.error('Failed to fetch todos:', error);
    throw error;
  }
};

/**
 * Todo 상세 조회
 */
export const getTodoById = async (id) => {
  try {
    const response = await api.get(`${API_ENDPOINTS.TODOS}/${id}`);
    return response;
  } catch (error) {
    console.error(`Failed to fetch todo ${id}:`, error);
    throw error;
  }
};

/**
 * Todo 생성
 */
export const createTodo = async (todoData) => {
  try {
    const response = await api.post(API_ENDPOINTS.TODOS, todoData);
    return response;
  } catch (error) {
    console.error('Failed to create todo:', error);
    throw error;
  }
};

/**
 * Todo 수정
 */
export const updateTodo = async (id, todoData) => {
  try {
    const response = await api.put(`${API_ENDPOINTS.TODOS}/${id}`, todoData);
    return response;
  } catch (error) {
    console.error(`Failed to update todo ${id}:`, error);
    throw error;
  }
};

/**
 * Todo 부분 수정 (PATCH)
 */
export const patchTodo = async (id, partialData) => {
  try {
    const response = await api.patch(`${API_ENDPOINTS.TODOS}/${id}`, partialData);
    return response;
  } catch (error) {
    console.error(`Failed to patch todo ${id}:`, error);
    throw error;
  }
};

/**
 * Todo 삭제
 */
export const deleteTodo = async (id) => {
  try {
    const response = await api.delete(`${API_ENDPOINTS.TODOS}/${id}`);
    return response;
  } catch (error) {
    console.error(`Failed to delete todo ${id}:`, error);
    throw error;
  }
};

/**
 * Todo 완료 토글
 */
export const toggleTodoComplete = async (id, completed) => {
  try {
    const response = await patchTodo(id, { completed });
    return response;
  } catch (error) {
    console.error(`Failed to toggle todo ${id} completion:`, error);
    throw error;
  }
};

/**
 * 오늘의 할 일 조회
 */
export const getTodayTodos = async () => {
  try {
    const today = new Date().toISOString().split('T')[0];
    const response = await getTodos({ date: today });
    return response;
  } catch (error) {
    console.error('Failed to fetch today todos:', error);
    throw error;
  }
};

/**
 * 특정 날짜의 할 일 조회
 */
export const getTodosByDate = async (date) => {
  try {
    const response = await getTodos({ date });
    return response;
  } catch (error) {
    console.error(`Failed to fetch todos for ${date}:`, error);
    throw error;
  }
};

/**
 * 카테고리별 할 일 조회
 */
export const getTodosByCategory = async (category) => {
  try {
    const response = await getTodos({ category });
    return response;
  } catch (error) {
    console.error(`Failed to fetch todos for category ${category}:`, error);
    throw error;
  }
};

/**
 * 우선순위별 할 일 조회
 */
export const getTodosByPriority = async (priority) => {
  try {
    const response = await getTodos({ priority });
    return response;
  } catch (error) {
    console.error(`Failed to fetch todos for priority ${priority}:`, error);
    throw error;
  }
};