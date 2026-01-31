/**
 * 인증 서비스
 * - 로그인/로그아웃
 * - 토큰 관리
 * - 소셜 로그인
 * - 권한 확인
 */

import api from './api';

const TOKEN_KEY = 'auth_tokens';
const USER_KEY = 'auth_user';

// =========================================================
// 토큰 관리
// =========================================================

/**
 * 저장된 토큰 가져오기
 */
export const getTokens = () => {
  try {
    const stored = localStorage.getItem(TOKEN_KEY);
    return stored ? JSON.parse(stored) : null;
  } catch {
    return null;
  }
};

/**
 * 토큰 저장
 */
export const saveTokens = (tokens) => {
  localStorage.setItem(TOKEN_KEY, JSON.stringify(tokens));
};

/**
 * 토큰 삭제
 */
export const clearTokens = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
};

/**
 * 액세스 토큰 가져오기
 */
export const getAccessToken = () => {
  const tokens = getTokens();
  return tokens?.access_token || null;
};

/**
 * 리프레시 토큰 가져오기
 */
export const getRefreshToken = () => {
  const tokens = getTokens();
  return tokens?.refresh_token || null;
};

/**
 * 저장된 사용자 정보 가져오기
 */
export const getStoredUser = () => {
  try {
    const stored = localStorage.getItem(USER_KEY);
    return stored ? JSON.parse(stored) : null;
  } catch {
    return null;
  }
};

/**
 * 사용자 정보 저장
 */
export const saveUser = (user) => {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
};

// =========================================================
// 인증 API
// =========================================================

/**
 * 회원가입
 */
export const register = async (email, password) => {
  try {
    const response = await api.post('/api/auth/register', { email, password });
    
    if (response.data.status === 200) {
      const { access_token, refresh_token, user_id, email: userEmail, role } = response.data.data;
      
      saveTokens({ access_token, refresh_token });
      saveUser({ user_id, email: userEmail, role });
      
      return { success: true, data: response.data.data };
    }
    
    return { success: false, message: response.data.message };
  } catch (error) {
    return { 
      success: false, 
      message: error.response?.data?.message || '회원가입에 실패했습니다.' 
    };
  }
};

/**
 * 로그인
 */
export const login = async (email, password) => {
  try {
    const response = await api.post('/api/auth/login', { email, password });
    
    if (response.data.status === 200) {
      const { access_token, refresh_token, user_id, email: userEmail, role } = response.data.data;
      
      saveTokens({ access_token, refresh_token });
      saveUser({ user_id, email: userEmail, role });
      
      return { success: true, data: response.data.data };
    }
    
    return { success: false, message: response.data.message };
  } catch (error) {
    return { 
      success: false, 
      message: error.response?.data?.message || '로그인에 실패했습니다.' 
    };
  }
};

/**
 * 로그아웃
 */
export const logout = async () => {
  try {
    const token = getAccessToken();
    if (token) {
      await api.post('/api/auth/logout', {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
    }
  } catch (error) {
    console.error('Logout error:', error);
  } finally {
    clearTokens();
  }
};

/**
 * 토큰 갱신
 */
export const refreshAccessToken = async () => {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    return null;
  }
  
  try {
    const response = await api.post('/api/auth/refresh', { 
      refresh_token: refreshToken 
    });
    
    if (response.data.status === 200) {
      const tokens = getTokens();
      tokens.access_token = response.data.data.access_token;
      saveTokens(tokens);
      return response.data.data.access_token;
    }
    
    // 리프레시 토큰도 만료됨
    clearTokens();
    return null;
  } catch (error) {
    clearTokens();
    return null;
  }
};

/**
 * 현재 사용자 정보 조회
 */
export const getCurrentUser = async () => {
  try {
    const token = getAccessToken();
    if (!token) return null;
    
    const response = await api.get('/api/auth/me', {
      headers: { Authorization: `Bearer ${token}` }
    });
    
    if (response.data.status === 200) {
      saveUser(response.data.data);
      return response.data.data;
    }
    
    return null;
  } catch (error) {
    if (error.response?.status === 401) {
      // 토큰 만료 시 갱신 시도
      const newToken = await refreshAccessToken();
      if (newToken) {
        return getCurrentUser();
      }
    }
    return null;
  }
};

/**
 * 로그인 상태 확인
 */
export const isAuthenticated = () => {
  return !!getAccessToken();
};

// =========================================================
// 소셜 로그인
// =========================================================

/**
 * Google 로그인 시작
 */
export const startGoogleLogin = async () => {
  try {
    const response = await api.get('/api/auth/google');
    if (response.data.status === 200) {
      window.location.href = response.data.data.auth_url;
    }
  } catch (error) {
    console.error('Google login error:', error);
    throw error;
  }
};

/**
 * Google 로그인 콜백 처리
 */
export const handleGoogleCallback = async (code) => {
  try {
    const response = await api.post('/api/auth/google/callback', null, {
      params: { code }
    });
    
    if (response.data.status === 200) {
      const { access_token, refresh_token, user_id, email, role } = response.data.data;
      
      saveTokens({ access_token, refresh_token });
      saveUser({ user_id, email, role });
      
      return { success: true, data: response.data.data };
    }
    
    return { success: false, message: response.data.message };
  } catch (error) {
    return { 
      success: false, 
      message: error.response?.data?.message || 'Google 로그인에 실패했습니다.' 
    };
  }
};

/**
 * Kakao 로그인 시작
 */
export const startKakaoLogin = async () => {
  try {
    const response = await api.get('/api/auth/kakao');
    if (response.data.status === 200) {
      window.location.href = response.data.data.auth_url;
    }
  } catch (error) {
    console.error('Kakao login error:', error);
    throw error;
  }
};

/**
 * Kakao 로그인 콜백 처리
 */
export const handleKakaoCallback = async (code) => {
  try {
    const response = await api.post('/api/auth/kakao/callback', null, {
      params: { code }
    });
    
    if (response.data.status === 200) {
      const { access_token, refresh_token, user_id, email, role } = response.data.data;
      
      saveTokens({ access_token, refresh_token });
      saveUser({ user_id, email, role });
      
      return { success: true, data: response.data.data };
    }
    
    return { success: false, message: response.data.message };
  } catch (error) {
    return { 
      success: false, 
      message: error.response?.data?.message || 'Kakao 로그인에 실패했습니다.' 
    };
  }
};

// =========================================================
// 권한 확인
// =========================================================

/**
 * 사용자 역할 확인
 */
export const hasRole = (requiredRoles) => {
  const user = getStoredUser();
  if (!user) return false;
  
  const roles = Array.isArray(requiredRoles) ? requiredRoles : [requiredRoles];
  return roles.includes(user.role);
};

/**
 * 관리자 여부 확인
 */
export const isAdmin = () => hasRole('admin');

/**
 * 프리미엄 사용자 여부 확인
 */
export const isPremium = () => hasRole(['premium', 'admin']);

/**
 * 권한 확인
 */
export const hasPermission = (permission) => {
  const user = getStoredUser();
  if (!user?.permissions) return false;
  return user.permissions.includes(permission);
};

// =========================================================
// 프로필 관리
// =========================================================

/**
 * 사용자 프로필 조회
 */
export const getProfile = async (userId) => {
  try {
    const response = await api.get(`/api/users/${userId}/profile`);
    
    if (response.data.status === 200) {
      return { success: true, data: response.data.data };
    }
    
    return { success: false, message: response.data.message };
  } catch (error) {
    return { 
      success: false, 
      message: error.response?.data?.message || '프로필 조회에 실패했습니다.' 
    };
  }
};

/**
 * 사용자 프로필 업데이트
 */
export const updateProfile = async (userId, profileData) => {
  try {
    const response = await api.put(`/api/users/${userId}/profile`, profileData);
    
    if (response.data.status === 200) {
      // 로컬 스토리지의 사용자 정보 업데이트
      const currentUser = getStoredUser();
      if (currentUser && currentUser.user_id === userId) {
        saveUser({ ...currentUser, ...response.data.data });
      }
      
      return { success: true, data: response.data.data };
    }
    
    return { success: false, message: response.data.message };
  } catch (error) {
    return { 
      success: false, 
      message: error.response?.data?.message || '프로필 업데이트에 실패했습니다.' 
    };
  }
};

/**
 * 계정 삭제 (탈퇴)
 */
export const deleteAccount = async (userId) => {
  try {
    const response = await api.delete(`/api/users/${userId}`);
    
    if (response.data.status === 200) {
      clearTokens();
      return { success: true, message: '계정이 삭제되었습니다.' };
    }
    
    return { success: false, message: response.data.message };
  } catch (error) {
    return { 
      success: false, 
      message: error.response?.data?.message || '계정 삭제에 실패했습니다.' 
    };
  }
};

/**
 * 비밀번호 변경
 */
export const changePassword = async (currentPassword, newPassword) => {
  try {
    const user = getStoredUser();
    if (!user?.user_id) {
      return { success: false, message: '로그인이 필요합니다.' };
    }
    
    const response = await api.put(`/api/users/${user.user_id}/password`, {
      current_password: currentPassword,
      new_password: newPassword,
    });
    
    if (response.data.status === 200) {
      return { success: true, message: '비밀번호가 변경되었습니다.' };
    }
    
    return { success: false, message: response.data.message };
  } catch (error) {
    return { 
      success: false, 
      message: error.response?.data?.message || '비밀번호 변경에 실패했습니다.' 
    };
  }
};

// =========================================================
// Axios 인터셉터 설정
// =========================================================

/**
 * API 인터셉터 설정 (토큰 자동 첨부 및 갱신)
 */
export const setupAuthInterceptor = () => {
  // 요청 인터셉터 - 토큰 자동 첨부
  api.interceptors.request.use(
    (config) => {
      const token = getAccessToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );
  
  // 응답 인터셉터 - 401 시 토큰 갱신
  api.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;
      
      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;
        
        const newToken = await refreshAccessToken();
        if (newToken) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return api(originalRequest);
        }
        
        // 토큰 갱신 실패 시 로그인 페이지로 이동
        clearTokens();
        window.location.href = '/login';
      }
      
      return Promise.reject(error);
    }
  );
};

export default {
  register,
  login,
  logout,
  getCurrentUser,
  isAuthenticated,
  startGoogleLogin,
  handleGoogleCallback,
  startKakaoLogin,
  handleKakaoCallback,
  hasRole,
  isAdmin,
  isPremium,
  hasPermission,
  getProfile,
  updateProfile,
  deleteAccount,
  changePassword,
  setupAuthInterceptor,
  getAccessToken,
  getRefreshToken,
  getStoredUser,
  saveUser,
  saveTokens,
  clearTokens,
};
