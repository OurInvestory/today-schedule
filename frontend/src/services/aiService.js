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
      type: payload.type === 'EVENT' ? 'event' : 'task',
      category: payload.category || '기타',
      start_at: finalStartAt,
      end_at: endAt,
      priority_score: payload.importance_score || payload.priority_score || 5,
      original_text: payload.original_text || null,
      estimated_minute: payload.estimated_minute || 60,
      source: 'ai'
    };
    
    console.log('Creating schedule:', schedulePayload);
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
    // end_at에서 date 추출
    const endAt = payload.end_at || payload.due_date || payload.date;
    const dateStr = endAt ? (typeof endAt === 'string' ? endAt.split('T')[0] : endAt) : new Date().toISOString().split('T')[0];
    
    // importance_score를 priority로 변환
    let priority = payload.priority || 'medium';
    if (!payload.priority && payload.importance_score) {
      if (payload.importance_score >= 7) priority = 'high';
      else if (payload.importance_score <= 3) priority = 'low';
      else priority = 'medium';
    }
    
    // AI가 생성한 할 일 데이터를 백엔드 스키마에 맞게 변환
    const subTaskPayload = {
      schedule_id: scheduleId || null, // scheduleId 없으면 독립 할 일
      title: payload.title,
      date: dateStr,
      estimated_minute: payload.estimated_minute || 60,
      priority: priority,
      category: payload.category || '기타',
      tip: payload.tip || payload.reason || null,
    };
    
    console.log('Creating sub-task:', subTaskPayload);
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
    
    const data = response.data?.data;
    const parsedResult = data?.parsed_result || data?.parsedResult;
    const assistantMessage = data?.assistant_message || data?.assistantMessage || '이미지 분석 완료';
    const actions = parsedResult?.actions || [];
    
    // 사용자에게 보여줄 메시지 생성
    let displayMessage = assistantMessage;
    if (actions.length > 0) {
      displayMessage += `\n\n📋 ${actions.length}개의 일정을 발견했습니다. 추가하시겠습니까?`;
    }
    
    return {
      success: true,
      message: displayMessage,
      parsedResult: parsedResult,
      actions: actions,
      imagePreview: URL.createObjectURL(imageFile),
    };
  } catch (error) {
    console.error('Failed to analyze timetable:', error);
    throw error;
  }
};

/**
 * AI 파싱 결과로 강의(Lecture) 생성
 */
export const createLectureFromAI = async (payload) => {
  try {
    const lecturePayload = {
      title: payload.title,
      start_time: payload.start_time,
      end_time: payload.end_time,
      start_day: payload.start_day,
      end_day: payload.end_day,
      week: payload.week || [],
    };
    
    console.log('Creating lecture:', lecturePayload);
    const response = await api.post('/api/lectures', lecturePayload);
    return response;
  } catch (error) {
    console.error('Failed to create lecture from AI:', error);
    throw error;
  }
};