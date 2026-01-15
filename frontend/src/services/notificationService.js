// 알림 설정 관련 서비스

const STORAGE_KEY = 'notification_settings';
const NOTIFICATIONS_KEY = 'app_notifications';
const SCHEDULED_ALERTS_KEY = 'scheduled_deadline_alerts';
const SCHEDULED_REMINDERS_KEY = 'scheduled_reminders'; // 챗봇 알림 예약

// 기본 알림 설정값
const defaultSettings = {
  pushNotification: true,
  notificationSound: true,
  vibration: true,
  doNotDisturb: false,
  dailySummary: true,
  dailySummaryTime: '08:00',
  deadlineAlert: true,
  deadlineAlertMinutes: 60, // 마감 전 알림 시간 (분)
  autoLock: '5',
  analyticsData: false,
  errorReport: true,
};

// 스케줄러 ID 저장
let deadlineCheckInterval = null;
let dailyBriefingTimeout = null;
let reminderCheckInterval = null; // 챗봇 알림 예약 체크

/**
 * 알림 설정 가져오기
 * @returns {Promise<Object>} 알림 설정 객체
 */
export const getNotificationSettings = async () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      return JSON.parse(stored);
    }
    return defaultSettings;
  } catch (error) {
    console.error('Error fetching notification settings:', error);
    return defaultSettings;
  }
};

/**
 * 알림 설정 업데이트
 * @param {Object} updates - 업데이트할 설정값
 * @returns {Promise<Object>} 업데이트된 설정 객체
 */
export const updateNotificationSettings = async (updates) => {
  try {
    const current = await getNotificationSettings();
    const updated = { ...current, ...updates };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    
    // 데일리 브리핑 시간이 변경되면 스케줄러 재설정
    if (updates.dailySummaryTime !== undefined || updates.dailySummary !== undefined) {
      scheduleDailyBriefing();
    }
    
    return updated;
  } catch (error) {
    console.error('Error updating notification settings:', error);
    throw error;
  }
};

/**
 * 알림 설정 초기화
 * @returns {Promise<Object>} 기본 설정 객체
 */
export const resetNotificationSettings = async () => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(defaultSettings));
    return defaultSettings;
  } catch (error) {
    console.error('Error resetting notification settings:', error);
    throw error;
  }
};

// ============ 인앱 알림 관리 ============

/**
 * 저장된 알림 목록 가져오기
 */
export const getNotifications = () => {
  try {
    const stored = localStorage.getItem(NOTIFICATIONS_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch (error) {
    console.error('Error getting notifications:', error);
    return [];
  }
};

/**
 * 알림 저장하기
 */
export const saveNotifications = (notifications) => {
  try {
    localStorage.setItem(NOTIFICATIONS_KEY, JSON.stringify(notifications));
  } catch (error) {
    console.error('Error saving notifications:', error);
  }
};

/**
 * 새 알림 추가
 */
export const addNotification = (notification) => {
  const notifications = getNotifications();
  const newNotification = {
    id: Date.now(),
    ...notification,
    time: formatTimeAgo(new Date()),
    timestamp: new Date().toISOString(),
    isRead: false,
  };
  notifications.unshift(newNotification);
  saveNotifications(notifications);
  return newNotification;
};

/**
 * 알림 읽음 처리
 */
export const markNotificationAsRead = (id) => {
  const notifications = getNotifications();
  const updated = notifications.map(n => 
    n.id === id ? { ...n, isRead: true } : n
  );
  saveNotifications(updated);
  return updated;
};

/**
 * 모든 알림 읽음 처리
 */
export const markAllNotificationsAsRead = () => {
  const notifications = getNotifications();
  const updated = notifications.map(n => ({ ...n, isRead: true }));
  saveNotifications(updated);
  return updated;
};

/**
 * 알림 삭제
 */
export const deleteNotification = (id) => {
  const notifications = getNotifications();
  const updated = notifications.filter(n => n.id !== id);
  saveNotifications(updated);
  return updated;
};

// ============ 브라우저 알림 ============

/**
 * 방해 금지 시간인지 확인
 */
const isDoNotDisturbTime = (settings) => {
  if (!settings.doNotDisturb) return false;
  
  const now = new Date();
  const currentMinutes = now.getHours() * 60 + now.getMinutes();
  
  const startTime = settings.doNotDisturbStart || '22:00';
  const endTime = settings.doNotDisturbEnd || '08:00';
  
  const [startHour, startMin] = startTime.split(':').map(Number);
  const [endHour, endMin] = endTime.split(':').map(Number);
  
  const startMinutes = startHour * 60 + startMin;
  const endMinutes = endHour * 60 + endMin;
  
  // 자정을 넘기는 경우 (예: 22:00 ~ 08:00)
  if (startMinutes > endMinutes) {
    return currentMinutes >= startMinutes || currentMinutes < endMinutes;
  }
  
  // 같은 날 내 범위 (예: 13:00 ~ 15:00)
  return currentMinutes >= startMinutes && currentMinutes < endMinutes;
};

/**
 * 브라우저 알림 보내기
 */
export const sendBrowserNotification = async (title, options = {}) => {
  const settings = await getNotificationSettings();
  
  if (!settings.pushNotification) {
    return null;
  }
  
  // 방해 금지 시간 체크
  if (isDoNotDisturbTime(settings)) {
    console.log('Do Not Disturb mode active, notification suppressed');
    return null;
  }
  
  if (!('Notification' in window)) {
    console.warn('This browser does not support notifications');
    return null;
  }
  
  if (Notification.permission !== 'granted') {
    return null;
  }
  
  const notification = new Notification(title, {
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-72x72.png',
    ...options,
  });
  
  // 인앱 알림도 함께 추가
  addNotification({
    type: options.tag || 'info',
    title,
    message: options.body || '',
  });
  
  return notification;
};

// ============ 마감 전 알림 ============

/**
 * 할 일 마감 전 알림 스케줄링
 */
export const scheduleDeadlineAlerts = async () => {
  const settings = await getNotificationSettings();
  
  if (!settings.deadlineAlert) {
    return;
  }
  
  // 기존 인터벌 정리
  if (deadlineCheckInterval) {
    clearInterval(deadlineCheckInterval);
  }
  
  // 1분마다 마감 체크
  deadlineCheckInterval = setInterval(() => {
    checkDeadlines(settings.deadlineAlertMinutes);
  }, 60000);
  
  // 즉시 한 번 체크
  checkDeadlines(settings.deadlineAlertMinutes);
};

/**
 * 마감 시간 체크 및 알림
 */
const checkDeadlines = async (alertMinutes = 60) => {
  try {
    const todosStr = localStorage.getItem('todos');
    if (!todosStr) return;
    
    const todos = JSON.parse(todosStr);
    const now = new Date();
    const alertedKey = SCHEDULED_ALERTS_KEY;
    const alerted = JSON.parse(localStorage.getItem(alertedKey) || '{}');
    
    todos.forEach(todo => {
      if (todo.completed) return;
      if (!todo.dueDate) return;
      
      // 마감 시간 계산 (시간이 있으면 해당 시간, 없으면 당일 23:59)
      let dueDateTime;
      if (todo.endTime) {
        dueDateTime = new Date(`${todo.dueDate}T${todo.endTime}`);
      } else {
        dueDateTime = new Date(`${todo.dueDate}T23:59:59`);
      }
      
      const timeDiff = dueDateTime.getTime() - now.getTime();
      const minutesUntilDue = timeDiff / (1000 * 60);
      
      // 알림 시간 범위 내이고, 아직 알림을 보내지 않은 경우
      if (minutesUntilDue > 0 && minutesUntilDue <= alertMinutes && !alerted[todo.id]) {
        sendBrowserNotification(`⏰ 마감 임박: ${todo.title}`, {
          body: `${Math.round(minutesUntilDue)}분 후에 마감됩니다.`,
          tag: 'deadline',
          requireInteraction: true,
        });
        
        // 알림 전송 기록
        alerted[todo.id] = new Date().toISOString();
        localStorage.setItem(alertedKey, JSON.stringify(alerted));
      }
    });
    
    // 오래된 알림 기록 정리 (24시간 이상 지난 것)
    const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    Object.keys(alerted).forEach(key => {
      if (new Date(alerted[key]) < oneDayAgo) {
        delete alerted[key];
      }
    });
    localStorage.setItem(alertedKey, JSON.stringify(alerted));
    
  } catch (error) {
    console.error('Error checking deadlines:', error);
  }
};

// ============ AI 데일리 브리핑 ============

/**
 * AI 데일리 브리핑 스케줄링
 */
export const scheduleDailyBriefing = async () => {
  // 기존 타임아웃 정리
  if (dailyBriefingTimeout) {
    clearTimeout(dailyBriefingTimeout);
    dailyBriefingTimeout = null;
  }
  
  const settings = await getNotificationSettings();
  
  if (!settings.dailySummary) {
    console.log('[DailyBriefing] 브리핑이 비활성화되어 있습니다.');
    return;
  }
  
  const now = new Date();
  const [hours, minutes] = settings.dailySummaryTime.split(':').map(Number);
  
  let nextBriefing = new Date();
  nextBriefing.setHours(hours, minutes, 0, 0);
  
  // 이미 지난 시간이면 다음 날로 설정
  if (nextBriefing <= now) {
    nextBriefing.setDate(nextBriefing.getDate() + 1);
  }
  
  const msUntilBriefing = nextBriefing.getTime() - now.getTime();
  
  console.log(`[DailyBriefing] 다음 브리핑 예약: ${nextBriefing.toLocaleString('ko-KR')} (${Math.round(msUntilBriefing / 1000 / 60)}분 후)`);
  
  dailyBriefingTimeout = setTimeout(async () => {
    console.log('[DailyBriefing] 브리핑 전송 시작!');
    await sendDailyBriefing();
    // 다음 브리핑 스케줄 (최신 설정으로 다시 스케줄링)
    scheduleDailyBriefing();
  }, msUntilBriefing);
};

/**
 * AI 데일리 브리핑 생성 및 전송
 */
export const sendDailyBriefing = async () => {
  try {
    // 백엔드 API에서 오늘 일정 가져오기
    let todaySchedules = [];
    let urgentSchedules = [];
    
    try {
      const { default: api } = await import('./api');
      const today = new Date();
      const startDate = today.toISOString().split('T')[0];
      const endDate = startDate;
      
      const response = await api.get('/api/schedules', {
        params: { start_date: startDate, end_date: endDate }
      });
      
      if (response.data?.status === 200 && Array.isArray(response.data?.data)) {
        todaySchedules = response.data.data;
        urgentSchedules = todaySchedules.filter(s => s.priority_score >= 7);
      }
    } catch (apiError) {
      console.warn('[DailyBriefing] API 호출 실패, localStorage 사용:', apiError);
      // API 실패 시 localStorage에서 할 일 가져오기
      const todosStr = localStorage.getItem('todos');
      if (todosStr) {
        const todos = JSON.parse(todosStr);
        const today = new Date().toISOString().split('T')[0];
        todaySchedules = todos.filter(todo => {
          if (todo.completed) return false;
          const start = todo.startDate || todo.dueDate;
          const end = todo.dueDate;
          return start <= today && today <= end;
        });
        urgentSchedules = todaySchedules.filter(t => t.importance >= 7);
      }
    }
    
    // 브리핑 메시지 생성
    let briefingMessage = '';
    const encouragements = [
      '화이팅하세요! 💪',
      '오늘도 파이팅! 🔥',
      '좋은 하루 되세요! ☀️',
      '응원합니다! 🌟',
      '힘내세요! 💯',
    ];
    const randomEncouragement = encouragements[Math.floor(Math.random() * encouragements.length)];
    
    if (todaySchedules.length === 0) {
      briefingMessage = '오늘은 예정된 일정이 없습니다. 여유로운 하루 되세요! 🎉';
    } else {
      briefingMessage = `오늘 일정 ${todaySchedules.length}개`;
      
      if (urgentSchedules.length > 0) {
        briefingMessage += `, 긴급 ${urgentSchedules.length}개`;
      }
      
      briefingMessage += `! ${randomEncouragement}`;
    }
    
    // 브라우저 알림 전송
    sendBrowserNotification('🌅 AI 데일리 브리핑', {
      body: briefingMessage,
      tag: 'daily-briefing',
      requireInteraction: true,
    });
    
    console.log('[DailyBriefing] 전송 완료:', briefingMessage);
    
    return {
      todaySchedules,
      urgentSchedules,
      message: briefingMessage,
    };
  } catch (error) {
    console.error('[DailyBriefing] 오류:', error);
    return null;
  }
};

/**
 * 수동으로 데일리 브리핑 트리거 (테스트용)
 */
export const triggerDailyBriefing = async () => {
  return await sendDailyBriefing();
};

// ============ 유틸리티 ============

/**
 * 상대 시간 포맷팅
 */
const formatTimeAgo = (date) => {
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  if (diffMins < 1) return '방금 전';
  if (diffMins < 60) return `${diffMins}분 전`;
  if (diffHours < 24) return `${diffHours}시간 전`;
  return `${diffDays}일 전`;
};

/**
 * 알림 서비스 초기화 (앱 시작 시 호출)
 */
export const initNotificationService = async () => {
  await scheduleDeadlineAlerts();
  await scheduleDailyBriefing();
  await startReminderChecker(); // 챗봇 알림 예약 체커 시작
};

/**
 * 알림 서비스 정리 (앱 종료 시 호출)
 */
export const cleanupNotificationService = () => {
  if (deadlineCheckInterval) {
    clearInterval(deadlineCheckInterval);
    deadlineCheckInterval = null;
  }
  if (dailyBriefingTimeout) {
    clearTimeout(dailyBriefingTimeout);
    dailyBriefingTimeout = null;
  }
  if (reminderCheckInterval) {
    clearInterval(reminderCheckInterval);
    reminderCheckInterval = null;
  }
};

// ============ 챗봇 알림 예약 ============

/**
 * 예약된 알림 목록 가져오기
 */
export const getScheduledReminders = () => {
  try {
    const stored = localStorage.getItem(SCHEDULED_REMINDERS_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch (error) {
    console.error('Error getting scheduled reminders:', error);
    return [];
  }
};

/**
 * 예약된 알림 저장하기
 */
export const saveScheduledReminders = (reminders) => {
  try {
    localStorage.setItem(SCHEDULED_REMINDERS_KEY, JSON.stringify(reminders));
  } catch (error) {
    console.error('Error saving scheduled reminders:', error);
  }
};

/**
 * 새 알림 예약 추가
 * @param {Object} reminder - { title, message, scheduledTime (ISO string), scheduleId? }
 */
export const scheduleReminder = (reminder) => {
  const reminders = getScheduledReminders();
  const newReminder = {
    id: Date.now(),
    title: reminder.title,
    message: reminder.message || '',
    scheduledTime: reminder.scheduledTime,
    scheduleId: reminder.scheduleId || null,
    createdAt: new Date().toISOString(),
    triggered: false,
  };
  reminders.push(newReminder);
  saveScheduledReminders(reminders);
  return newReminder;
};

/**
 * 알림 예약 삭제
 */
export const cancelScheduledReminder = (reminderId) => {
  const reminders = getScheduledReminders();
  const updated = reminders.filter(r => r.id !== reminderId);
  saveScheduledReminders(updated);
  return updated;
};

/**
 * 예약 알림 체크 및 발송 (1분마다 실행)
 */
const checkScheduledReminders = async () => {
  const settings = await getNotificationSettings();
  
  if (!settings.pushNotification || settings.doNotDisturb) {
    return;
  }
  
  const reminders = getScheduledReminders();
  const now = new Date();
  let hasChanges = false;
  
  reminders.forEach(reminder => {
    if (reminder.triggered) return;
    
    const scheduledTime = new Date(reminder.scheduledTime);
    
    // 예약 시간이 지났거나 1분 이내인 경우 알림 발송
    if (scheduledTime <= now) {
      sendBrowserNotification(`🔔 ${reminder.title}`, {
        body: reminder.message || '예약된 알림입니다.',
        tag: `reminder-${reminder.id}`,
        requireInteraction: true,
      });
      
      reminder.triggered = true;
      hasChanges = true;
    }
  });
  
  if (hasChanges) {
    // 발송된 알림 제거 (24시간 후 자동 정리)
    const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    const cleaned = reminders.filter(r => 
      !r.triggered || new Date(r.scheduledTime) > oneDayAgo
    );
    saveScheduledReminders(cleaned);
  }
};

/**
 * 예약 알림 체커 시작
 */
export const startReminderChecker = async () => {
  // 기존 인터벌 정리
  if (reminderCheckInterval) {
    clearInterval(reminderCheckInterval);
  }
  
  // 1분마다 체크
  reminderCheckInterval = setInterval(() => {
    checkScheduledReminders();
  }, 60000);
  
  // 즉시 한 번 체크
  checkScheduledReminders();
};

/**
 * 일정에 대한 알림 예약 (N분 전 알림)
 * @param {Object} schedule - { id, title, endTime (or end_at) }
 * @param {number} minutesBefore - 몇 분 전에 알림을 보낼지
 */
export const scheduleReminderForSchedule = (schedule, minutesBefore = 60) => {
  const endTime = schedule.endTime || schedule.end_at || schedule.dueDate;
  if (!endTime) return null;
  
  const endDate = new Date(endTime);
  const reminderTime = new Date(endDate.getTime() - minutesBefore * 60 * 1000);
  
  // 이미 지난 시간이면 예약하지 않음
  if (reminderTime <= new Date()) {
    return null;
  }
  
  return scheduleReminder({
    title: schedule.title,
    message: `${minutesBefore}분 후에 "${schedule.title}"이(가) 있습니다.`,
    scheduledTime: reminderTime.toISOString(),
    scheduleId: schedule.id,
  });
};

export default {
  getNotificationSettings,
  updateNotificationSettings,
  resetNotificationSettings,
  getNotifications,
  saveNotifications,
  addNotification,
  markNotificationAsRead,
  markAllNotificationsAsRead,
  deleteNotification,
  sendBrowserNotification,
  scheduleDeadlineAlerts,
  scheduleDailyBriefing,
  sendDailyBriefing,
  triggerDailyBriefing,
  initNotificationService,
  cleanupNotificationService,
  // 챗봇 알림 예약
  getScheduledReminders,
  saveScheduledReminders,
  scheduleReminder,
  cancelScheduledReminder,
  startReminderChecker,
  scheduleReminderForSchedule,
};
