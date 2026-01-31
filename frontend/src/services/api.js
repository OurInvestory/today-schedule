import axios from 'axios';

// Vite 환경 변수 사용 (기본값: http://localhost:8000)
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// 토큰 갱신 중 여부 (중복 갱신 방지)
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

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
    // 로컬 스토리지에서 토큰 가져오기
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
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    if (error.response) {
      const { status, data } = error.response;
      
      // 401 에러이고 토큰 갱신 요청이 아닌 경우
      if (status === 401 && !originalRequest._retry && !originalRequest.url.includes('/api/auth/refresh')) {
        if (isRefreshing) {
          // 이미 갱신 중이면 대기열에 추가
          return new Promise((resolve, reject) => {
            failedQueue.push({ resolve, reject });
          })
            .then((token) => {
              originalRequest.headers.Authorization = `Bearer ${token}`;
              return api(originalRequest);
            })
            .catch((err) => {
              return Promise.reject(err);
            });
        }

        originalRequest._retry = true;
        isRefreshing = true;

        const refreshToken = localStorage.getItem('refreshToken');
        
        if (refreshToken) {
          try {
            const response = await axios.post(
              `${API_BASE_URL}/api/auth/refresh`,
              null,
              { params: { refresh_token: refreshToken } }
            );
            
            if (response.data.status === 200 && response.data.data) {
              const { access_token, refresh_token: newRefreshToken } = response.data.data;
              localStorage.setItem('accessToken', access_token);
              if (newRefreshToken) {
                localStorage.setItem('refreshToken', newRefreshToken);
              }
              
              processQueue(null, access_token);
              originalRequest.headers.Authorization = `Bearer ${access_token}`;
              return api(originalRequest);
            }
          } catch (refreshError) {
            processQueue(refreshError, null);
            // 리프레시 토큰도 만료된 경우 로그아웃 처리
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
            localStorage.removeItem('user');
            window.dispatchEvent(new CustomEvent('auth:logout'));
            return Promise.reject(refreshError);
          } finally {
            isRefreshing = false;
          }
        } else {
          // 리프레시 토큰이 없으면 로그아웃
          localStorage.removeItem('accessToken');
          localStorage.removeItem('user');
          window.dispatchEvent(new CustomEvent('auth:logout'));
        }
      }

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
        case 429:
          console.error('요청이 너무 많습니다. 잠시 후 다시 시도해주세요.');
          break;
        default:
          console.error('서버 에러:', data);
      }
    }
    return Promise.reject(error);
  }
);

export default api;