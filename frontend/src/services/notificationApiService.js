import api from './api';

/**
 * 알림 등록 (백엔드 API)
 * Chat API의 target: "NOTIFICATION" 액션 수신 후 호출
 */
export const createNotification = async ({
  schedule_id,
  scheduleId,
  schedule_title,
  scheduleTitle,
  message,
  notify_at,
  notifyAt,
  minutes_before,
  minutesBefore
}) => {
  try {
    const payload = {
      schedule_id: schedule_id || scheduleId || null,
      schedule_title: schedule_title || scheduleTitle || null,
      message,
      notify_at: notify_at || notifyAt,
      minutes_before: minutes_before || minutesBefore || null,
    };
    
    const response = await api.post('/api/notifications', payload);
    return response;
  } catch (error) {
    console.error('Failed to create notification:', error);
    throw error;
  }
};

/**
 * 대기 중인 알림 조회 (폴링용)
 * 1분마다 호출하여 발송해야 할 알림 확인
 */
export const getPendingNotifications = async () => {
  try {
    const response = await api.get('/api/notifications/pending');
    return response.data;
  } catch (error) {
    console.error('Failed to get pending notifications:', error);
    throw error;
  }
};

/**
 * 내 알림 목록 조회
 */
export const getMyNotifications = async (limit = 20, includeChecked = true) => {
  try {
    const response = await api.get('/api/notifications', {
      params: { limit, include_checked: includeChecked }
    });
    return response;
  } catch (error) {
    console.error('Failed to get notifications:', error);
    throw error;
  }
};

/**
 * 알림 확인 처리
 */
export const checkNotifications = async (notificationIds) => {
  try {
    const response = await api.post('/api/notifications/check', {
      notification_ids: notificationIds
    });
    return response;
  } catch (error) {
    console.error('Failed to check notifications:', error);
    throw error;
  }
};

// 폴링 인터벌 ID
let pollingInterval = null;

/**
 * 브라우저 알림 권한 요청
 */
export const requestNotificationPermission = async () => {
  if (!('Notification' in window)) {
    console.warn('This browser does not support notifications');
    return false;
  }
  
  if (Notification.permission === 'granted') {
    return true;
  }
  
  if (Notification.permission !== 'denied') {
    const permission = await Notification.requestPermission();
    return permission === 'granted';
  }
  
  return false;
};

/**
 * 브라우저 알림 표시
 */
export const showBrowserNotification = (title, options = {}) => {
  if (Notification.permission !== 'granted') {
    return null;
  }
  
  const notification = new Notification(title, {
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-72x72.png',
    ...options,
  });
  
  return notification;
};

/**
 * 알림 폴링 시작 (1분마다)
 */
export const startNotificationPolling = (onNotification) => {
  // 기존 폴링 중지
  stopNotificationPolling();
  
  const checkPendingNotifications = async () => {
    try {
      const response = await getPendingNotifications();
      // API 응답: { data: { status, message, data: [...] } }
      const responseData = response?.data;
      
      if (responseData?.status === 200 && Array.isArray(responseData?.data) && responseData.data.length > 0) {
        // 각 알림에 대해 브라우저 알림 표시
        responseData.data.forEach(notification => {
          showBrowserNotification('일정 알림', {
            body: notification.message,
            tag: `notification-${notification.notification_id}`,
            requireInteraction: true,
          });
          
          // 콜백 호출 (UI 업데이트용)
          if (onNotification) {
            onNotification(notification);
          }
        });
      }
    } catch (error) {
      console.error('Notification polling error:', error);
    }
  };
  
  // 즉시 한 번 체크
  checkPendingNotifications();
  
  // 1분마다 폴링
  pollingInterval = setInterval(checkPendingNotifications, 60000);
};

/**
 * 알림 폴링 중지
 */
export const stopNotificationPolling = () => {
  if (pollingInterval) {
    clearInterval(pollingInterval);
    pollingInterval = null;
  }
};

export default {
  createNotification,
  getPendingNotifications,
  getMyNotifications,
  checkNotifications,
  requestNotificationPermission,
  showBrowserNotification,
  startNotificationPolling,
  stopNotificationPolling,
};
