// 알림 설정 관련 서비스

const STORAGE_KEY = 'notification_settings';

// 기본 알림 설정값
const defaultSettings = {
  pushNotification: true,
  notificationSound: true,
  vibration: true,
  doNotDisturb: false,
  dailySummary: true,
  dailySummaryTime: '08:00',
  deadlineAlert: true,
  autoLock: '5',
  analyticsData: false,
  errorReport: true,
};

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

export default {
  getNotificationSettings,
  updateNotificationSettings,
  resetNotificationSettings,
};
