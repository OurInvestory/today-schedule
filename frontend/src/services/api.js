import axios from 'axios';

// Temporarily hardcoded baseURL for debugging
const API_BASE_URL = 'http://localhost:8000/api';

// Axios 인스턴스 생성
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  paramsSerializer: params => {
    return new URLSearchParams(params).toString();
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
    return response; // Return the full response object
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response;
      switch (status) {
        case 401:
          console.error('인증이 필요합니다.');
          break;
        case 403:
          console.error('접근 권한이 없습니다.');
          break;
        case 404:
          console.error('리소스를 찾을 수 없습니다.');
          break;
        default:
          console.error('서버 에러:', data);
      }
    }
    return Promise.reject(error);
  }
);

export default api;