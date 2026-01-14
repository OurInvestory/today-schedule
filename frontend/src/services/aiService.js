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
    // AI 응답 필드를 백엔드 스키마에 맞게 변환
    const startAt = payload.start_at || payload.start_time || null;
    let endAt = payload.end_at || payload.end_time || null;
    
    // start_at만 있고 end_at이 없으면 1시간 후로 설정
    if (startAt && !endAt) {
      const startDate = new Date(startAt);
      startDate.setHours(startDate.getHours() + 1);
      endAt = startDate.toISOString();
    }
    
    // end_at만 있고 start_at이 없으면 1시간 전으로 설정
    let finalStartAt = startAt;
    if (!startAt && endAt) {
      const endDate = new Date(endAt);
      endDate.setHours(endDate.getHours() - 1);
      finalStartAt = endDate.toISOString();
    }
    
    const schedulePayload = {
      title: payload.title,
      type: payload.type || 'task',
      category: payload.category || '기타',
      start_at: finalStartAt,
      end_at: endAt,
      priority_score: payload.importance_score || payload.priority_score || 5,
      original_text: payload.original_text || null,
      estimated_minute: payload.estimated_minute || 60,
      source: 'ai'
    };
    
    const response = await api.post('/api/schedules', schedulePayload);
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
    // AI가 생성한 할 일 데이터를 백엔드 스키마에 맞게 변환
    const subTaskPayload = {
      schedule_id: scheduleId || null, // scheduleId 없으면 독립 할 일
      title: payload.title,
      date: payload.due_date || payload.date || new Date().toISOString().split('T')[0],
      estimated_minute: payload.estimated_minute || 60,
      priority: payload.priority || 'medium',
      category: payload.category || '기타',
      ai_reason: payload.ai_reason || payload.reason || `AI가 추천한 할 일입니다.`,
    };
    
    // 직접 sub-tasks 엔드포인트로 POST
    const response = await api.post('/api/sub-tasks', subTaskPayload);
    return response;
  } catch (error) {
    console.error('Failed to create sub-task from AI:', error);
    throw error;
  }
};

/**
 * 시간표/포스터 이미지 분석 및 일정 추출
 */
export const analyzeTimetableImage = async (imageFile) => {
  try {
    const formData = new FormData();
    formData.append('file', imageFile);
    formData.append('timezone', Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Seoul');
    
    const response = await api.post('/api/analyze', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000, // 이미지 분석은 시간이 걸릴 수 있음
    });
    
    return {
      success: true,
      message: response.data?.data?.assistantMessage || '이미지 분석 완료',
      parsedResult: response.data?.data?.parsedResult,
      imagePreview: URL.createObjectURL(imageFile),
    };
  } catch (error) {
    console.error('Failed to analyze timetable:', error);
    throw error;
  }
};