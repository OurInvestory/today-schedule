import api from './api';
import { API_ENDPOINTS } from '../utils/constants';

// Google OAuth 상태 저장 키
const GOOGLE_AUTH_KEY = 'google_calendar_auth';

/**
 * Google OAuth 인증 상태 가져오기
 */
export const getGoogleAuthStatus = () => {
  try {
    const stored = localStorage.getItem(GOOGLE_AUTH_KEY);
    if (stored) {
      return JSON.parse(stored);
    }
    return { connected: false, email: null, expiresAt: null };
  } catch (error) {
    console.error('Error getting Google auth status:', error);
    return { connected: false, email: null, expiresAt: null };
  }
};

/**
 * Google OAuth 인증 상태 저장
 */
export const saveGoogleAuthStatus = (status) => {
  try {
    localStorage.setItem(GOOGLE_AUTH_KEY, JSON.stringify(status));
  } catch (error) {
    console.error('Error saving Google auth status:', error);
  }
};

/**
 * Google OAuth 연결 해제
 */
export const disconnectGoogleCalendar = () => {
  localStorage.removeItem(GOOGLE_AUTH_KEY);
  return { connected: false, email: null };
};

/**
 * Google OAuth 인증 시작 (팝업 방식)
 * 백엔드에 OAuth URL 요청 후 팝업 열기
 */
export const initiateGoogleAuth = async () => {
  try {
    // 백엔드에서 OAuth URL 가져오기 (구현되어 있다면)
    // const response = await api.get('/api/calendar/auth-url');
    // const authUrl = response.data.url;
    
    // 임시: 직접 구현된 OAuth 플로우가 없으므로 모의 연결 처리
    // 실제 구현시 Google OAuth 팝업 열기
    const mockEmail = `user${Date.now().toString().slice(-4)}@gmail.com`;
    const authStatus = {
      connected: true,
      email: mockEmail,
      expiresAt: new Date(Date.now() + 3600 * 1000).toISOString(),
      connectedAt: new Date().toISOString(),
    };
    
    saveGoogleAuthStatus(authStatus);
    return authStatus;
  } catch (error) {
    console.error('Failed to initiate Google auth:', error);
    throw error;
  }
};

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
 * 일정 상세 조회
 */
export const getScheduleById = async (scheduleId) => {
  try {
    // 백엔드에 개별 조회 API가 없다면 전체 일정에서 필터링
    const today = new Date();
    const from = new Date(today.getFullYear(), today.getMonth() - 1, 1).toISOString();
    const to = new Date(today.getFullYear(), today.getMonth() + 2, 0).toISOString();
    
    const response = await api.get('/api/schedules', {
      params: { from, to },
    });

    const schedules = response.data.data || [];
    const schedule = schedules.find(s => s.schedule_id === scheduleId);
    
    if (!schedule) {
      throw new Error('일정을 찾을 수 없습니다.');
    }

    // 백엔드 응답을 프론트엔드 형식으로 변환
    const extractTime = (datetime) => {
      if (!datetime || typeof datetime !== 'string' || !datetime.includes('T')) return null;
      return datetime.split('T')[1]?.substring(0, 5) || null;
    };

    const extractDate = (datetime) => {
      if (!datetime || typeof datetime !== 'string') return null;
      return datetime.split('T')[0] || null;
    };

    return {
      id: schedule.schedule_id,
      title: schedule.title,
      description: schedule.original_text || schedule.update_text || '',
      date: extractDate(schedule.end_at) || extractDate(schedule.start_at),
      startDate: extractDate(schedule.start_at),
      endDate: extractDate(schedule.end_at),
      startTime: extractTime(schedule.start_at),
      endTime: extractTime(schedule.end_at),
      isAllDay: !extractTime(schedule.start_at) && !extractTime(schedule.end_at),
      type: schedule.type || 'schedule',
      category: schedule.category,
      priority_score: schedule.priority_score || 0,
    };
  } catch (error) {
    console.error(`Failed to fetch schedule ${scheduleId}:`, error);
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