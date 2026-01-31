/**
 * 비동기 작업 서비스
 * - 작업 제출
 * - 작업 상태 폴링
 */

import api from './api';

/**
 * AI 분석 작업 제출 (비동기)
 * @param {string} message - 분석할 메시지
 * @param {Object} context - 추가 컨텍스트
 * @returns {Promise<{task_id: string, status: string}>}
 */
export const submitAIAnalysis = async (message, context = null) => {
  const response = await api.post('/api/tasks/ai/analyze', {
    message,
    context,
  });
  return response.data;
};

/**
 * 이미지 분석 작업 제출 (비동기)
 * @param {string} imageData - Base64 이미지 데이터
 * @param {string} imageType - 이미지 타입 (timetable, schedule)
 * @returns {Promise<{task_id: string, status: string}>}
 */
export const submitImageAnalysis = async (imageData, imageType = 'timetable') => {
  const response = await api.post('/api/tasks/image/analyze', {
    image_data: imageData,
    image_type: imageType,
  });
  return response.data;
};

/**
 * 우선순위 재계산 작업 제출 (비동기)
 * @returns {Promise<{task_id: string, status: string}>}
 */
export const submitPriorityRecalculation = async () => {
  const response = await api.post('/api/tasks/priorities/recalculate');
  return response.data;
};

/**
 * 리마인더 알림 생성 (비동기)
 * @param {string} scheduleId - 일정 ID
 * @param {number} minutesBefore - 알림 시간 (분 전)
 * @returns {Promise<{task_id: string, status: string}>}
 */
export const submitReminder = async (scheduleId, minutesBefore = 30) => {
  const response = await api.post('/api/tasks/notifications/reminder', {
    schedule_id: scheduleId,
    minutes_before: minutesBefore,
  });
  return response.data;
};

/**
 * 일괄 알림 생성 (비동기)
 * @param {Array} notifications - 알림 데이터 배열
 * @returns {Promise<{task_id: string, status: string}>}
 */
export const submitBatchNotifications = async (notifications) => {
  const response = await api.post('/api/tasks/notifications/batch', {
    notifications,
  });
  return response.data;
};

/**
 * 작업 상태 조회
 * @param {string} taskId - 작업 ID
 * @returns {Promise<{task_id: string, status: string, result?: any}>}
 */
export const getTaskStatus = async (taskId) => {
  const response = await api.get(`/api/tasks/status/${taskId}`);
  return response.data;
};

/**
 * 작업 완료까지 폴링
 * @param {string} taskId - 작업 ID
 * @param {Object} options - 폴링 옵션
 * @param {number} options.interval - 폴링 간격 (ms)
 * @param {number} options.timeout - 최대 대기 시간 (ms)
 * @param {Function} options.onProgress - 진행 상태 콜백
 * @returns {Promise<{status: string, result?: any}>}
 */
export const pollTaskUntilComplete = async (taskId, options = {}) => {
  const {
    interval = 1000,
    timeout = 300000, // 5분
    onProgress = null,
  } = options;

  const startTime = Date.now();

  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        // 타임아웃 체크
        if (Date.now() - startTime > timeout) {
          reject(new Error('작업 시간이 초과되었습니다.'));
          return;
        }

        const response = await getTaskStatus(taskId);
        const { data } = response;

        // 진행 상태 콜백
        if (onProgress) {
          onProgress(data);
        }

        // 완료 또는 실패 확인
        if (data.status === 'completed') {
          resolve(data);
          return;
        }

        if (data.status === 'failed') {
          reject(new Error(data.error || '작업이 실패했습니다.'));
          return;
        }

        // 계속 폴링
        setTimeout(poll, interval);
      } catch (error) {
        reject(error);
      }
    };

    poll();
  });
};

/**
 * 비동기 작업 제출 및 완료 대기 (편의 함수)
 * @param {Function} submitFn - 작업 제출 함수
 * @param {Array} args - 제출 함수 인자
 * @param {Object} pollOptions - 폴링 옵션
 * @returns {Promise<any>} - 작업 결과
 */
export const submitAndWait = async (submitFn, args = [], pollOptions = {}) => {
  // 작업 제출
  const submitResponse = await submitFn(...args);
  
  if (submitResponse.status !== 202 || !submitResponse.data?.task_id) {
    throw new Error('작업 제출에 실패했습니다.');
  }

  const taskId = submitResponse.data.task_id;

  // 완료 대기
  const result = await pollTaskUntilComplete(taskId, pollOptions);
  return result;
};

export default {
  submitAIAnalysis,
  submitImageAnalysis,
  submitPriorityRecalculation,
  submitReminder,
  submitBatchNotifications,
  getTaskStatus,
  pollTaskUntilComplete,
  submitAndWait,
};
