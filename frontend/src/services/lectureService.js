import api from './api';

/**
 * Lecture(강의/시간표) 관련 API 서비스
 * - lecture는 시간표에만 표시되며, 캘린더나 할일에는 추가되지 않음
 * - schedule/sub_task는 시간표에 추가되지 않음
 */

/**
 * 강의 목록 조회
 * @param {string} from - 시작 날짜 (YYYY-MM-DD)
 * @param {string} to - 종료 날짜 (YYYY-MM-DD)
 */
export const getLectures = async (from, to) => {
  const response = await api.get('/api/lectures', {
    params: { from, to }
  });
  return response.data;
};

/**
 * 강의 생성
 * @param {Object} lectureData - 강의 데이터
 * @param {string} lectureData.title - 강의명
 * @param {string} lectureData.start_time - 시작 시간 (HH:mm:ss)
 * @param {string} lectureData.end_time - 종료 시간 (HH:mm:ss)
 * @param {string} lectureData.start_day - 시작 날짜 (YYYY-MM-DD)
 * @param {string} lectureData.end_day - 종료 날짜 (YYYY-MM-DD)
 * @param {number[]} lectureData.week - 요일 배열 (0=일, 1=월, ..., 6=토)
 */
export const createLecture = async (lectureData) => {
  const response = await api.post('/api/lectures', lectureData);
  return response.data;
};

/**
 * 강의 수정
 * @param {string} lectureId - 강의 ID
 * @param {Object} lectureData - 수정할 강의 데이터
 */
export const updateLecture = async (lectureId, lectureData) => {
  const response = await api.put(`/api/lectures/${lectureId}`, lectureData);
  return response.data;
};

/**
 * 강의 삭제
 * @param {string} lectureId - 강의 ID
 */
export const deleteLecture = async (lectureId) => {
  const response = await api.delete(`/api/lectures/${lectureId}`);
  return response.data;
};

/**
 * 주어진 날짜의 주차 번호 계산
 * @param {Date} date - 날짜
 * @returns {number} - 주차 번호
 */
export const getWeekNumber = (date) => {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  const dayNum = d.getUTCDay() || 7;
  d.setUTCDate(d.getUTCDate() + 4 - dayNum);
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  return Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
};

/**
 * 주어진 날짜가 포함된 주의 시작일(월요일)과 종료일(일요일) 계산
 * @param {Date} date - 기준 날짜
 * @returns {{ startOfWeek: Date, endOfWeek: Date }}
 */
export const getWeekRange = (date) => {
  const d = new Date(date);
  const day = d.getDay();
  const diff = d.getDate() - day + (day === 0 ? -6 : 1); // 월요일로 조정
  
  const startOfWeek = new Date(d);
  startOfWeek.setDate(diff);
  startOfWeek.setHours(0, 0, 0, 0);
  
  const endOfWeek = new Date(startOfWeek);
  endOfWeek.setDate(startOfWeek.getDate() + 6);
  endOfWeek.setHours(23, 59, 59, 999);
  
  return { startOfWeek, endOfWeek };
};

/**
 * 강의 색상 생성 (타이틀 기반 고정 색상)
 * @param {string} title - 강의명
 * @returns {string} - HSL 색상 코드
 */
export const getLectureColor = (title) => {
  let hash = 0;
  for (let i = 0; i < title.length; i++) {
    hash = title.charCodeAt(i) + ((hash << 5) - hash);
  }
  
  // 파스텔 톤 색상 생성 (채도 40-60%, 밝기 70-85%)
  const hue = Math.abs(hash % 360);
  const saturation = 45 + (Math.abs(hash >> 8) % 20);
  const lightness = 75 + (Math.abs(hash >> 16) % 10);
  
  return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
};

/**
 * 강의 텍스트 색상 (배경 기반)
 * @param {string} bgColor - 배경 HSL 색상
 * @returns {string} - 텍스트 색상
 */
export const getLectureTextColor = (bgColor) => {
  // 파스텔 배경이므로 어두운 텍스트 사용
  return 'hsl(0, 0%, 25%)';
};
