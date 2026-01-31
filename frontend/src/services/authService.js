/**
 * 인증 서비스 (회원가입, 로그인, 로그아웃)
 */

import api from './api';

// 로컬 스토리지 키
const TOKEN_KEY = 'accessToken';
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
    const { access_token, user } = response.data.data;
    setToken(access_token);
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
    removeUser();
  }
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

export default {
  signup,
  login,
  logout,
  getMe,
  changePassword,
  setToken,
  getToken,
  removeToken,
  isAuthenticated,
  setUser,
  getUser,
  removeUser,
};
