/**
 * 인증 컨텍스트 (Auth Context)
 * 전역 인증 상태 관리
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  login as loginApi,
  logout as logoutApi,
  signup as signupApi,
  getMe,
  getToken,
  getUser,
  setUser as setStoredUser,
  isAuthenticated as checkAuth,
  updateProfile as updateProfileApi,
  deleteAccount as deleteAccountApi,
} from '../services/authService';

// Context 생성
const AuthContext = createContext(null);

// Provider 컴포넌트
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showLoginModal, setShowLoginModal] = useState(false);

  // 초기 인증 상태 확인
  useEffect(() => {
    const initAuth = async () => {
      try {
        if (checkAuth()) {
          // 저장된 사용자 정보 복원
          const savedUser = getUser();
          if (savedUser) {
            setUser(savedUser);
            setIsAuthenticated(true);
          } else {
            // 토큰은 있지만 사용자 정보가 없으면 서버에서 조회
            const response = await getMe();
            if (response.status === 200 && response.data) {
              setUser(response.data);
              setIsAuthenticated(true);
            }
          }
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
        // 토큰이 유효하지 않으면 초기화
        setUser(null);
        setIsAuthenticated(false);
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  // 로그인
  const login = useCallback(async (email, password) => {
    const response = await loginApi(email, password);
    if (response.status === 200 && response.data) {
      setUser(response.data.user);
      setIsAuthenticated(true);
      setShowLoginModal(false);
    }
    return response;
  }, []);

  // 회원가입
  const signup = useCallback(async (email, password, passwordConfirm) => {
    const response = await signupApi(email, password, passwordConfirm);
    return response;
  }, []);

  // 로그아웃
  const logout = useCallback(async () => {
    await logoutApi();
    setUser(null);
    setIsAuthenticated(false);
  }, []);

  // 프로필 업데이트
  const updateProfile = useCallback(async (profileData) => {
    const response = await updateProfileApi(profileData);
    if (response.status === 200 && response.data) {
      const updatedUser = { ...user, ...response.data };
      setUser(updatedUser);
      setStoredUser(updatedUser);  // 로컬 스토리지에도 저장
    }
    return response;
  }, [user]);

  // 계정 삭제
  const deleteAccount = useCallback(async (password) => {
    const response = await deleteAccountApi(password);
    if (response.status === 200) {
      setUser(null);
      setIsAuthenticated(false);
    }
    return response;
  }, []);

  // 사용자 정보 갱신
  const refreshUser = useCallback(async () => {
    try {
      const response = await getMe();
      if (response.status === 200 && response.data) {
        setUser(response.data);
        setStoredUser(response.data);
      }
    } catch (error) {
      console.error('Failed to refresh user:', error);
    }
  }, []);

  // 로그인 필요 액션 처리
  const requireAuth = useCallback((action) => {
    if (!isAuthenticated) {
      setShowLoginModal(true);
      return false;
    }
    if (action) {
      action();
    }
    return true;
  }, [isAuthenticated]);

  // 로그인 모달 열기
  const openLoginModal = useCallback(() => {
    setShowLoginModal(true);
  }, []);

  // 로그인 모달 닫기
  const closeLoginModal = useCallback(() => {
    setShowLoginModal(false);
  }, []);

  const value = {
    user,
    isAuthenticated,
    loading,
    showLoginModal,
    login,
    signup,
    logout,
    updateProfile,
    deleteAccount,
    refreshUser,
    requireAuth,
    openLoginModal,
    closeLoginModal,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Hook
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
