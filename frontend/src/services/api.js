import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://five-schedule-backend:8000/api';

// Axios 인스턴스 생성
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터
api.interceptors.request.use(
  (config) => {
    // 로컬 스토리지에서 토큰 가져오기 (향후 인증 구현 시)
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터
api.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    // 에러 처리
    if (error.response) {
      // 서버 응답이 있는 경우
      const { status, data } = error.response;
      
      switch (status) {
        case 401:
          // 인증 실패
          console.error('인증이 필요합니다.');
          // 로그인 페이지로 리다이렉트 등의 처리
          break;
        case 403:
          console.error('접근 권한이 없습니다.');
          break;
        case 404:
          console.error('요청한 리소스를 찾을 수 없습니다.');
          break;
        case 500:
          console.error('서버 에러가 발생했습니다.');
          break;
        default:
          console.error('에러가 발생했습니다:', data?.message || error.message);
      }
      
      return Promise.reject(data || error);
    } else if (error.request) {
      // 요청은 전송되었으나 응답이 없는 경우
      console.error('서버로부터 응답이 없습니다.');
      return Promise.reject(new Error('서버로부터 응답이 없습니다.'));
    } else {
      // 요청 설정 중 에러 발생
      console.error('요청 중 에러가 발생했습니다:', error.message);
      return Promise.reject(error);
    }
  }
);

export default api;