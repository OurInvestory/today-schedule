/**
 * SSE (Server-Sent Events) 클라이언트
 * 실시간 알림 수신을 위한 이벤트 스트림 연결
 * 
 * 사용법:
 * import { connectSSE, disconnectSSE, onEvent } from './eventService';
 * 
 * // 연결
 * connectSSE();
 * 
 * // 이벤트 리스너 등록
 * onEvent('notification:created', (data) => {
 *   console.log('새 알림:', data);
 * });
 * 
 * // 연결 해제
 * disconnectSSE();
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

let eventSource = null;
let reconnectAttempts = 0;
let reconnectTimeout = null;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY = 3000; // 3초

// 이벤트 리스너 저장소
const eventListeners = new Map();

/**
 * SSE 연결
 */
export const connectSSE = () => {
  if (eventSource && eventSource.readyState !== EventSource.CLOSED) {
    console.log('🔌 SSE: 이미 연결되어 있습니다.');
    return eventSource;
  }

  const url = `${API_URL}/api/events/stream`;
  
  try {
    eventSource = new EventSource(url);
    
    eventSource.onopen = () => {
      console.log('🔌 SSE: 연결 성공');
      reconnectAttempts = 0;
    };
    
    eventSource.onerror = (error) => {
      console.error('❌ SSE: 연결 에러', error);
      
      if (eventSource.readyState === EventSource.CLOSED) {
        attemptReconnect();
      }
    };
    
    // 연결 확인 이벤트
    eventSource.addEventListener('connected', (event) => {
      const data = JSON.parse(event.data);
      console.log('✅ SSE: 연결 확인됨', data);
      dispatchEvent('connected', data);
    });
    
    // 하트비트 이벤트
    eventSource.addEventListener('heartbeat', (event) => {
      const data = JSON.parse(event.data);
      console.debug('💓 SSE: heartbeat', data.timestamp);
    });
    
    // 알림 관련 이벤트
    const notificationEvents = [
      'notification:created',
      'notification:sent',
      'schedule:reminder',
      'system:deadline_alert',
      'system:daily_summary'
    ];
    
    notificationEvents.forEach(eventType => {
      eventSource.addEventListener(eventType, (event) => {
        const data = JSON.parse(event.data);
        console.log(`📥 SSE: ${eventType}`, data);
        dispatchEvent(eventType, data);
      });
    });
    
    // 일정 관련 이벤트
    const scheduleEvents = [
      'schedule:created',
      'schedule:updated',
      'schedule:deleted'
    ];
    
    scheduleEvents.forEach(eventType => {
      eventSource.addEventListener(eventType, (event) => {
        const data = JSON.parse(event.data);
        console.log(`📥 SSE: ${eventType}`, data);
        dispatchEvent(eventType, data);
      });
    });
    
    return eventSource;
  } catch (error) {
    console.error('❌ SSE: 연결 실패', error);
    return null;
  }
};

/**
 * SSE 연결 해제
 */
export const disconnectSSE = () => {
  if (reconnectTimeout) {
    clearTimeout(reconnectTimeout);
    reconnectTimeout = null;
  }
  
  if (eventSource) {
    eventSource.close();
    eventSource = null;
    console.log('🔌 SSE: 연결 해제됨');
  }
  
  reconnectAttempts = 0;
};

/**
 * 재연결 시도
 */
const attemptReconnect = () => {
  if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
    console.error('❌ SSE: 최대 재연결 시도 횟수 초과');
    dispatchEvent('reconnect_failed', { attempts: reconnectAttempts });
    return;
  }
  
  reconnectAttempts++;
  console.log(`🔄 SSE: 재연결 시도 (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})...`);
  
  reconnectTimeout = setTimeout(() => {
    connectSSE();
  }, RECONNECT_DELAY * reconnectAttempts); // 점진적 지연
};

/**
 * 이벤트 리스너 등록
 * @param {string} eventType - 이벤트 타입
 * @param {function} callback - 콜백 함수
 * @returns {function} 리스너 제거 함수
 */
export const onEvent = (eventType, callback) => {
  if (!eventListeners.has(eventType)) {
    eventListeners.set(eventType, []);
  }
  
  eventListeners.get(eventType).push(callback);
  
  // 리스너 제거 함수 반환
  return () => {
    const listeners = eventListeners.get(eventType);
    if (listeners) {
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  };
};

/**
 * 이벤트 리스너 제거
 */
export const offEvent = (eventType, callback) => {
  const listeners = eventListeners.get(eventType);
  if (listeners) {
    const index = listeners.indexOf(callback);
    if (index > -1) {
      listeners.splice(index, 1);
    }
  }
};

/**
 * 이벤트 디스패치
 */
const dispatchEvent = (eventType, data) => {
  const listeners = eventListeners.get(eventType);
  if (listeners) {
    listeners.forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error(`이벤트 리스너 에러 (${eventType}):`, error);
      }
    });
  }
  
  // 와일드카드 리스너도 호출
  const wildcardListeners = eventListeners.get('*');
  if (wildcardListeners) {
    wildcardListeners.forEach(callback => {
      try {
        callback({ type: eventType, data });
      } catch (error) {
        console.error('와일드카드 리스너 에러:', error);
      }
    });
  }
};

/**
 * 연결 상태 확인
 */
export const isConnected = () => {
  return eventSource && eventSource.readyState === EventSource.OPEN;
};

/**
 * 연결 상태 가져오기
 */
export const getConnectionState = () => {
  if (!eventSource) return 'disconnected';
  
  switch (eventSource.readyState) {
    case EventSource.CONNECTING: return 'connecting';
    case EventSource.OPEN: return 'connected';
    case EventSource.CLOSED: return 'disconnected';
    default: return 'unknown';
  }
};

// =========================================================
// React Hook용 유틸리티
// =========================================================

/**
 * 알림 이벤트 리스너 (편의 함수)
 */
export const onNotification = (callback) => {
  const unsubscribes = [
    onEvent('notification:created', callback),
    onEvent('notification:sent', callback),
    onEvent('schedule:reminder', callback),
    onEvent('system:deadline_alert', callback),
    onEvent('system:daily_summary', callback),
  ];
  
  // 모든 리스너 제거 함수 반환
  return () => unsubscribes.forEach(unsub => unsub());
};

/**
 * 일정 변경 이벤트 리스너 (편의 함수)
 */
export const onScheduleChange = (callback) => {
  const unsubscribes = [
    onEvent('schedule:created', callback),
    onEvent('schedule:updated', callback),
    onEvent('schedule:deleted', callback),
  ];
  
  return () => unsubscribes.forEach(unsub => unsub());
};

export default {
  connectSSE,
  disconnectSSE,
  onEvent,
  offEvent,
  isConnected,
  getConnectionState,
  onNotification,
  onScheduleChange,
};
