import api from './api';
import { API_ENDPOINTS } from '../utils/constants';

/**
 * 자연어 텍스트를 파싱하여 할 일 추출
 */
export const parseNaturalLanguage = async (text) => {
  try {
    const response = await api.post('/ai/parse', { text });
    return response;
  } catch (error) {
    console.error('Failed to parse natural language:', error);
    throw error;
  }
};

/**
 * AI 기반 우선순위 추천
 */
export const getPriorityRecommendation = async (todoData) => {
  try {
    const response = await api.post('/ai/priority', todoData);
    return response;
  } catch (error) {
    console.error('Failed to get priority recommendation:', error);
    throw error;
  }
};

/**
 * 과제 세분화 (큰 과제를 작은 단위로)
 */
export const breakdownTask = async (taskData) => {
  try {
    const response = await api.post('/ai/breakdown', taskData);
    return response;
  } catch (error) {
    console.error('Failed to breakdown task:', error);
    throw error;
  }
};

/**
 * 챗봇 메시지 전송
 */
export const sendChatMessage = async (message, conversationId = null) => {
  try {
    const response = await api.post('/ai/chat', {
      message,
      conversationId,
    });
    return response;
  } catch (error) {
    console.error('Failed to send chat message:', error);
    throw error;
  }
};

/**
 * 챗봇 대화 히스토리 조회
 */
export const getChatHistory = async (conversationId) => {
  try {
    const response = await api.get(`/ai/chat/${conversationId}`);
    return response;
  } catch (error) {
    console.error('Failed to get chat history:', error);
    throw error;
  }
};