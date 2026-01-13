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
    const response = await api.get('/calendar/events', {
      params: { startDate, endDate },
    });
    return response;
  } catch (error) {
    console.error('Failed to fetch calendar events:', error);
    throw error;
  }
};

/**
 * 캘린더 이벤트 생성
 */
export const createCalendarEvent = async (eventData) => {
  try {
    const response = await api.post('/calendar/events', eventData);
    return response;
  } catch (error) {
    console.error('Failed to create calendar event:', error);
    throw error;
  }
};

/**
 * 캘린더 이벤트 수정
 */
export const updateCalendarEvent = async (id, eventData) => {
  try {
    const response = await api.put(`/calendar/events/${id}`, eventData);
    return response;
  } catch (error) {
    console.error(`Failed to update calendar event ${id}:`, error);
    throw error;
  }
};

/**
 * 캘린더 이벤트 삭제
 */
export const deleteCalendarEvent = async (id) => {
  try {
    const response = await api.delete(`/calendar/events/${id}`);
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

    const response = await api.get('/schedules', {
      params: { from, to },
    });

    return response.data.data || [];
  } catch (error) {
    console.error(`Failed to fetch monthly events for ${year}-${month}:`, error);
    throw error;
  }
};