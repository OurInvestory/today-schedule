import api from './api';
import { API_ENDPOINTS } from '../utils/constants';

/**
 * Google Calendar 동기화
 */
export const syncGoogleCalendar = async () => {
  try {
    const response = await api.post(API_ENDPOINTS.CALENDAR_SYNC);
    return response;
  } catch (error) {
    console.error('Failed to sync Google Calendar:', error);
    throw error;
  }
};

/**
 * 캘린더 이벤트 가져오기
 */
export const getCalendarEvents = async (startDate, endDate) => {
  try {
    const response = await api.get('/api/calendar/events', {
      params: { startDate, endDate },
    });
    return response;
  } catch (error) {
    console.error('Failed to fetch calendar events:', error);
    throw error;
  }
};

/**
 * 캠린더 이벤트 생성 (일정 추가)
 */
export const createCalendarEvent = async (eventData) => {
  try {
    // 프론트엔드 데이터를 백엔드 SaveScheduleRequest 스키마에 맞게 변환
    const payload = {
      title: eventData.title,
      type: eventData.type || 'schedule',
      category: eventData.category || '일정',
      start_at: eventData.startDate && eventData.startTime 
        ? `${eventData.startDate}T${eventData.startTime}:00`
        : eventData.startDate 
          ? `${eventData.startDate}T00:00:00`
          : null,
      end_at: eventData.endDate && eventData.endTime
        ? `${eventData.endDate}T${eventData.endTime}:00`
        : eventData.endDate
          ? `${eventData.endDate}T23:59:59`
          : `${eventData.startDate}T23:59:59`,
      priority_score: eventData.priority_score || 5,
      original_text: eventData.description || null,
      estimated_minute: eventData.estimated_minute || null,
      ai_reason: eventData.ai_reason || null,
    };

    console.log('API 요청 payload:', payload);
    const response = await api.post('/api/schedules', payload);
    console.log('API 응답:', response.data);
    
    // 백엔드에서 200 OK를 반환하더라도 status가 500이면 실패
    if (response.data && response.data.status !== 200) {
      throw new Error(response.data.message || '일정 저장에 실패했습니다.');
    }
    
    return response;
  } catch (error) {
    console.error('Failed to create calendar event:', error);
    throw error;
  }
};

/**
 * 캠린더 이벤트 수정 (일정 수정)
 */
export const updateCalendarEvent = async (id, eventData) => {
  try {
    // 프론트엔드 데이터를 백엔드 UpdateScheduleRequest 스키마에 맞게 변환
    const payload = {};
    
    if (eventData.title !== undefined) payload.title = eventData.title;
    if (eventData.type !== undefined) payload.type = eventData.type;
    if (eventData.category !== undefined) payload.category = eventData.category;
    if (eventData.startDate !== undefined) {
      payload.start_at = eventData.startTime 
        ? `${eventData.startDate}T${eventData.startTime}:00`
        : `${eventData.startDate}T00:00:00`;
    }
    if (eventData.endDate !== undefined) {
      payload.end_at = eventData.endTime
        ? `${eventData.endDate}T${eventData.endTime}:00`
        : `${eventData.endDate}T23:59:59`;
    }
    if (eventData.priority_score !== undefined) payload.priority_score = eventData.priority_score;
    if (eventData.description !== undefined) payload.update_text = eventData.description;
    if (eventData.estimated_minute !== undefined) payload.estimated_minute = eventData.estimated_minute;

    const response = await api.put(`/api/schedules/${id}`, payload);
    return response;
  } catch (error) {
    console.error(`Failed to update calendar event ${id}:`, error);
    throw error;
  }
};

/**
 * 캠린더 이벤트 삭제 (일정 삭제)
 */
export const deleteCalendarEvent = async (id) => {
  try {
    const response = await api.delete(`/api/schedules/${id}`);
    return response;
  } catch (error) {
    console.error(`Failed to delete calendar event ${id}:`, error);
    throw error;
  }
};

/**
 * 월별 이벤트 조회
 */
export const getMonthlyEvents = async (year, month) => {
  try {
    const from = new Date(year, month - 1, 1).toISOString();
    const to = new Date(year, month, 0, 23, 59, 59).toISOString();

    const response = await api.get('/api/schedules', {
      params: { from, to },
    });

    // 백엔드 응답을 프론트엔드 형식으로 변환
    return (response.data.data || []).map(item => ({
      ...item,
      id: item.schedule_id,              // schedule_id -> id
      startDate: item.start_at,           // start_at -> startDate
      endDate: item.end_at,               // end_at -> endDate
      date: item.end_at ? item.end_at.split('T')[0] : null, // 날짜만 추출
    }));
  } catch (error) {
    console.error(`Failed to fetch monthly events for ${year}-${month}:`, error);
    throw error;
  }
};