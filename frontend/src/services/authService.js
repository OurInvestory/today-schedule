/**
 * 인증 서비스 (회원가입, 로그인, 로그아웃)
 */

import api from './api';

// 로컬 스토리지 키
const TOKEN_KEY = 'accessToken';
const REFRESH_TOKEN_KEY = 'refreshToken';
const USER_KEY = 'user';

/**
 * 회원가입
 */
export const signup = async (email, password, passwordConfirm) => {
  const response = await api.post('/api/auth/signup', {
    email,
    password,
    password_confirm: passwordConfirm,
  });
  return response.data;
};

/**
 * 로그인
 */
export const login = async (email, password) => {
  const response = await api.post('/api/auth/login', {
    email,
    password,
  });
  
  // 성공 시 토큰 및 사용자 정보 저장
  if (response.data.status === 200 && response.data.data) {
    const { access_token, refresh_token, user } = response.data.data;
    setToken(access_token);
    if (refresh_token) {
      setRefreshToken(refresh_token);
    }
    setUser(user);
  }
  
  return response.data;
};

/**
 * 로그아웃
 */
export const logout = async () => {
  try {
    await api.post('/api/auth/logout');
  } catch (error) {
    console.error('Logout error:', error);
  } finally {
    // 로컬 스토리지 정리
    removeToken();
    removeRefreshToken();
    removeUser();
  }
};

/**
 * 토큰 갱신
 */
export const refreshAccessToken = async () => {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }
  
  const response = await api.post('/api/auth/refresh', null, {
    params: { refresh_token: refreshToken },
  });
  
  if (response.data.status === 200 && response.data.data) {
    const { access_token, refresh_token: newRefreshToken } = response.data.data;
    setToken(access_token);
    if (newRefreshToken) {
      setRefreshToken(newRefreshToken);
    }
    return access_token;
  }
  
  throw new Error('Token refresh failed');
};

/**
 * 현재 사용자 정보 조회
 */
export const getMe = async () => {
  const response = await api.get('/api/auth/me');
  return response.data;
};

/**
 * 비밀번호 변경
 */
export const changePassword = async (currentPassword, newPassword, newPasswordConfirm) => {
  const response = await api.put('/api/auth/password', {
    current_password: currentPassword,
    new_password: newPassword,
    new_password_confirm: newPasswordConfirm,
  });
  return response.data;
};

/**
 * 프로필 업데이트
 */
export const updateProfile = async (profileData) => {
  const response = await api.put('/api/auth/profile', profileData);
  
  // 성공 시 로컬 스토리지의 사용자 정보도 업데이트
  if (response.data.status === 200 && response.data.data) {
    const currentUser = getUser();
    if (currentUser) {
      const updatedUser = { ...currentUser, ...response.data.data };
      setUser(updatedUser);
    }
  }
  
  return response.data;
};

/**
 * 계정 삭제
 */
export const deleteAccount = async (password) => {
  const response = await api.delete('/api/auth/account', {
    data: { password },
  });
  
  // 성공 시 로컬 스토리지 정리
  if (response.data.status === 200) {
    removeToken();
    removeRefreshToken();
    removeUser();
  }
  
  return response.data;
};

// ===== 토큰 관리 =====

/**
 * 토큰 저장
 */
export const setToken = (token) => {
  localStorage.setItem(TOKEN_KEY, token);
};

/**
 * 토큰 조회
 */
export const getToken = () => {
  return localStorage.getItem(TOKEN_KEY);
};

/**
 * 토큰 삭제
 */
export const removeToken = () => {
  localStorage.removeItem(TOKEN_KEY);
};

/**
 * 인증 여부 확인
 */
export const isAuthenticated = () => {
  return !!getToken();
};

// ===== 사용자 정보 관리 =====

/**
 * 사용자 정보 저장
 */
export const setUser = (user) => {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
};

/**
 * 사용자 정보 조회
 */
export const getUser = () => {
  const user = localStorage.getItem(USER_KEY);
  return user ? JSON.parse(user) : null;
};

/**
 * 사용자 정보 삭제
 */
export const removeUser = () => {
  localStorage.removeItem(USER_KEY);
};

// ===== 리프레시 토큰 관리 =====

/**
 * 리프레시 토큰 저장
 */
export const setRefreshToken = (token) => {
  localStorage.setItem(REFRESH_TOKEN_KEY, token);
};

/**
 * 리프레시 토큰 조회
 */
export const getRefreshToken = () => {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
};

/**
 * 리프레시 토큰 삭제
 */
export const removeRefreshToken = () => {
  localStorage.removeItem(REFRESH_TOKEN_KEY);
};

export default {
  signup,
  login,
  logout,
  refreshAccessToken,
  getMe,
  changePassword,
  updateProfile,
  deleteAccount,
  setToken,
  getToken,
  removeToken,
  isAuthenticated,
  setUser,
  getUser,
  removeUser,
  setRefreshToken,
  getRefreshToken,
  removeRefreshToken,
};
