import api from './api';

/**
 * 챗봇 메시지 전송
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
      
      const response = await api.post('/api/chat', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response;
    }
    
    // 일반 JSON 요청
    const response = await api.post('/api/chat', {
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

/**
 * 시간표 이미지 분석 및 일정 추출
 */
export const analyzeTimetableImage = async (imageFile) => {
  try {
    const formData = new FormData();
    formData.append('image', imageFile);
    
    // 향후 백엔드 API 연동 예정
    return {
      success: true,
      message: '시간표 분석 기능은 곧 제공될 예정입니다.',
      schedules: [],
      imagePreview: URL.createObjectURL(imageFile),
    };
  } catch (error) {
    console.error('Failed to analyze timetable:', error);
    throw error;
  }
};