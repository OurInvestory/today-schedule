import api from './api';
import { API_ENDPOINTS } from '../utils/constants';

/**
 * 자연어 텍스트를 파싱하여 할 일 추출
 */
export const parseNaturalLanguage = async (text) => {
  try {
    const response = await api.post('/api/ai/parse', { text });
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
    const response = await api.post('/api/ai/priority', todoData);
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
    const response = await api.post('/api/ai/breakdown', taskData);
    return response;
  } catch (error) {
    console.error('Failed to breakdown task:', error);
    throw error;
  }
};

/**
 * 챗봇 메시지 전송 (새 API 스펙)
 * 이미지, 파일, 링크도 함께 전송 가능
 */
export const sendChatMessage = async (text, baseDate = null, selectedScheduleId = null, userContext = {}, files = null) => {
  try {
    const now = new Date();
    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Seoul';
    
    // FormData를 사용하여 파일과 텍스트를 함께 전송
    if (files && files.length > 0) {
      const formData = new FormData();
      formData.append('text', text);
      formData.append('baseDate', baseDate || now.toISOString().split('T')[0]);
      formData.append('timezone', timezone);
      if (selectedScheduleId) {
        formData.append('selectedScheduleId', selectedScheduleId);
      }
      formData.append('userContext', JSON.stringify(userContext));
      
      // 파일 추가
      for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
      }
      
      const response = await api.post('/api/ai/chat', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response;
    }
    
    // 일반 JSON 요청
    const response = await api.post('/api/ai/chat', {
      text,
      baseDate: baseDate || now.toISOString().split('T')[0],
      timezone,
      selectedScheduleId,
      userContext,
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

/**
 * AI 파싱 결과로 일정 생성
 */
export const createScheduleFromAI = async (payload) => {
  try {
    const response = await api.post('/api/schedule', payload);
    return response;
  } catch (error) {
    console.error('Failed to create schedule from AI:', error);
    throw error;
  }
};

/**
 * AI 파싱 결과로 할 일 생성
 */
export const createSubTaskFromAI = async (scheduleId, payload) => {
  try {
    const response = await api.post(`/api/schedule/${scheduleId}/sub-tasks`, payload);
    return response;
  } catch (error) {
    console.error('Failed to create sub-task from AI:', error);
    throw error;
  }
};