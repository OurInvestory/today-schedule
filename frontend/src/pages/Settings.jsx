import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { getNotificationSettings, updateNotificationSettings, triggerDailyBriefing } from '../services/notificationService';
import { getGoogleAuthStatus, initiateGoogleAuth, disconnectGoogleCalendar } from '../services/calendarService';
import { changePassword } from '../services/authService';
import { t, getCurrentLanguage, supportedLanguages } from '../utils/i18n';
import { useAuth } from '../context/AuthContext';
import './Settings.css';

// 테마 적용 함수
const applyTheme = (theme) => {
  const root = document.documentElement;
  
  if (theme === 'system') {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    root.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
  } else {
    root.setAttribute('data-theme', theme);
  }
  
  localStorage.setItem('app-theme', theme);
};

// 초기 테마 로드
const getInitialTheme = () => {
  const saved = localStorage.getItem('app-theme');
  return saved || 'light';
};

// 캐시 크기 계산 함수
const calculateCacheSize = () => {
  let totalSize = 0;
  for (let key in localStorage) {
    if (Object.prototype.hasOwnProperty.call(localStorage, key)) {
      totalSize += localStorage.getItem(key).length * 2; // UTF-16 = 2 bytes per char
    }
  }
  return totalSize;
};

const formatBytes = (bytes) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const Settings = () => {
  const navigate = useNavigate();
  const { isAuthenticated, loading: authLoading, user, logout, updateProfile, deleteAccount } = useAuth();
  const [showLicenseModal, setShowLicenseModal] = useState(false);
  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const [showDeleteAccountModal, setShowDeleteAccountModal] = useState(false);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [cacheSize, setCacheSize] = useState(0);
  const [profileForm, setProfileForm] = useState({
    name: '',
    school: '',
    department: '',
    grade: '',
  });
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    newPasswordConfirm: '',
  });
  const [deletePassword, setDeletePassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [settings, setSettings] = useState({
    pushNotification: true,
    notificationSound: true,
    vibration: true,
    doNotDisturb: false,
    doNotDisturbStart: '22:00',
    doNotDisturbEnd: '08:00',
    dailySummary: true,
    dailySummaryTime: '08:00',
    deadlineAlert: true,
    autoLock: '5',
    analyticsData: false,
    errorReport: true,
    language: 'ko',
    theme: 'light',
  });
  const [loading, setLoading] = useState(true);

  const [connectedAccounts, setConnectedAccounts] = useState({
    google: { connected: true, email: 'demo@five-today.com' },
    kakao: { connected: false, email: null },
    naver: { connected: false, email: null },
  });
  
  // 언어 변경 시 리렌더링을 위한 상태
  const [, setCurrentLang] = useState(getCurrentLanguage());

  // 미인증 사용자 리다이렉트
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate('/login');
    }
  }, [isAuthenticated, authLoading, navigate]);

  // 사용자 정보가 변경될 때 프로필 폼 업데이트
  useEffect(() => {
    if (user) {
      setProfileForm({
        name: user.name || '',
        school: user.school || '',
        department: user.department || '',
        grade: user.grade || '',
      });
    }
  }, [user]);

  useEffect(() => {
    fetchSettings();
    
    // 캐시 크기 계산
    setCacheSize(calculateCacheSize());
    
    // Google 인증 상태 로드
    const googleAuth = getGoogleAuthStatus();
    setConnectedAccounts(prev => ({
      ...prev,
      google: { connected: googleAuth.connected, email: googleAuth.email },
    }));
    
    // 카카오/네이버 연결 상태 로드
    const kakaoAuth = localStorage.getItem('kakao-auth-status');
    const naverAuth = localStorage.getItem('naver-auth-status');
    if (kakaoAuth) {
      const parsed = JSON.parse(kakaoAuth);
      setConnectedAccounts(prev => ({ ...prev, kakao: parsed }));
    }
    if (naverAuth) {
      const parsed = JSON.parse(naverAuth);
      setConnectedAccounts(prev => ({ ...prev, naver: parsed }));
    }
    
    // 초기 테마 적용
    const initialTheme = getInitialTheme();
    setSettings(prev => ({ ...prev, theme: initialTheme }));
    applyTheme(initialTheme);
    
    // 언어 변경 이벤트 리스너
    const handleLanguageChange = (e) => {
      setCurrentLang(e.detail);
    };
    window.addEventListener('languageChange', handleLanguageChange);
    
    // 시스템 테마 변경 감지
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleSystemThemeChange = () => {
      const currentTheme = localStorage.getItem('app-theme');
      if (currentTheme === 'system') {
        applyTheme('system');
      }
    };
    
    mediaQuery.addEventListener('change', handleSystemThemeChange);
    return () => {
      mediaQuery.removeEventListener('change', handleSystemThemeChange);
      window.removeEventListener('languageChange', handleLanguageChange);
    };
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const data = await getNotificationSettings();
      if (data) {
        setSettings(prev => ({ ...prev, ...data }));
      }
    } catch (error) {
      console.error('Failed to fetch settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (key) => {
    const newValue = !settings[key];
    setSettings(prev => ({ ...prev, [key]: newValue }));
    
    try {
      await updateNotificationSettings({ [key]: newValue });
    } catch (error) {
      console.error('Failed to update setting:', error);
      setSettings(prev => ({ ...prev, [key]: !newValue }));
    }
  };

  const handleSelectChange = useCallback(async (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
    
    // 테마 변경 시 즉시 적용
    if (key === 'theme') {
      applyTheme(value);
    }
    
    // 언어 변경 시 즉시 적용
    if (key === 'language') {
      localStorage.setItem('app-language', value);
      // 이벤트 발생시켜 컴포넌트 리렌더링
      window.dispatchEvent(new CustomEvent('languageChange', { detail: value }));
      // 페이지 새로고침으로 완전히 적용 (선택적)
      // window.location.reload();
    }
    
    try {
      await updateNotificationSettings({ [key]: value });
    } catch (error) {
      console.error('Failed to update setting:', error);
    }
  }, []);

  const handleAccountToggle = async (provider) => {
    if (provider === 'google') {
      if (connectedAccounts.google.connected) {
        // 연결 해제
        disconnectGoogleCalendar();
        setConnectedAccounts(prev => ({
          ...prev,
          google: { connected: false, email: null },
        }));
      } else {
        // 연결 시도
        try {
          const authStatus = await initiateGoogleAuth();
          setConnectedAccounts(prev => ({
            ...prev,
            google: { connected: authStatus.connected, email: authStatus.email },
          }));
        } catch (error) {
          console.error('Google auth failed:', error);
          alert('Google 계정 연결에 실패했습니다.');
        }
      }
    } else if (provider === 'kakao') {
      if (connectedAccounts.kakao.connected) {
        // 연결 해제
        localStorage.removeItem('kakao-auth-status');
        setConnectedAccounts(prev => ({
          ...prev,
          kakao: { connected: false, email: null },
        }));
      } else {
        // 모의 연결 (실제로는 카카오 OAuth 필요)
        const mockEmail = 'user@kakao.com';
        const authData = { connected: true, email: mockEmail };
        localStorage.setItem('kakao-auth-status', JSON.stringify(authData));
        setConnectedAccounts(prev => ({
          ...prev,
          kakao: authData,
        }));
      }
    } else if (provider === 'naver') {
      if (connectedAccounts.naver.connected) {
        // 연결 해제
        localStorage.removeItem('naver-auth-status');
        setConnectedAccounts(prev => ({
          ...prev,
          naver: { connected: false, email: null },
        }));
      } else {
        // 모의 연결 (실제로는 네이버 OAuth 필요)
        const mockEmail = 'user@naver.com';
        const authData = { connected: true, email: mockEmail };
        localStorage.setItem('naver-auth-status', JSON.stringify(authData));
        setConnectedAccounts(prev => ({
          ...prev,
          naver: authData,
        }));
      }
    }
  };

  // 캐시 삭제 핸들러
  const handleClearCache = () => {
    // 테마와 언어 설정은 보존
    const theme = localStorage.getItem('app-theme');
    const language = localStorage.getItem('app-language');
    const notificationSettings = localStorage.getItem('notification-settings');
    
    // 캐시 데이터만 삭제 (설정 외 데이터)
    const keysToRemove = [];
    for (let key in localStorage) {
      if (Object.prototype.hasOwnProperty.call(localStorage, key) && 
          !key.includes('theme') && 
          !key.includes('language') && 
          !key.includes('notification-settings') &&
          !key.includes('google-auth')) {
        keysToRemove.push(key);
      }
    }
    
    keysToRemove.forEach(key => localStorage.removeItem(key));
    
    // 설정 복원
    if (theme) localStorage.setItem('app-theme', theme);
    if (language) localStorage.setItem('app-language', language);
    if (notificationSettings) localStorage.setItem('notification-settings', notificationSettings);
    
    setCacheSize(calculateCacheSize());
    alert(t('cacheCleared') + ' 📦');
  };

  // 로그아웃 핸들러
  const handleLogout = async () => {
    try {
      await logout();
      setShowLogoutModal(false);
      navigate('/');
    } catch (error) {
      console.error('Logout failed:', error);
      alert(t('error'));
    }
  };

  // 계정 삭제 핸들러
  const handleDeleteAccount = async () => {
    if (!deletePassword) {
      alert(t('error'));
      return;
    }
    
    setIsSubmitting(true);
    try {
      const response = await deleteAccount(deletePassword);
      if (response.status === 200) {
        setShowDeleteAccountModal(false);
        alert(t('accountDeleted') + ' 🙏');
        navigate('/');
      } else {
        alert(response.message || t('error'));
      }
    } catch (error) {
      console.error('Delete account failed:', error);
      const message = error.response?.data?.detail || t('error');
      alert(message);
    } finally {
      setIsSubmitting(false);
      setDeletePassword('');
    }
  };

  // 프로필 저장 핸들러
  const handleSaveProfile = async () => {
    setIsSubmitting(true);
    try {
      const response = await updateProfile(profileForm);
      if (response.status === 200) {
        alert(t('profileSaved') + ' 👤');
        setShowProfileModal(false);
      } else {
        alert(response.message || t('error'));
      }
    } catch (error) {
      console.error('Profile update failed:', error);
      alert(t('error'));
    } finally {
      setIsSubmitting(false);
    }
  };

  // 비밀번호 변경 핸들러
  const handleChangePassword = async () => {
    const { currentPassword, newPassword, newPasswordConfirm } = passwordForm;
    
    if (!currentPassword || !newPassword || !newPasswordConfirm) {
      alert(t('error'));
      return;
    }
    
    if (newPassword.length < 8) {
      alert(t('error'));
      return;
    }
    
    if (newPassword !== newPasswordConfirm) {
      alert(t('error'));
      return;
    }
    
    setIsSubmitting(true);
    try {
      const response = await changePassword(currentPassword, newPassword, newPasswordConfirm);
      if (response.status === 200) {
        alert(t('passwordChanged') + ' 🔒');
        setShowPasswordModal(false);
        setPasswordForm({ currentPassword: '', newPassword: '', newPasswordConfirm: '' });
      } else {
        alert(response.message || t('error'));
      }
    } catch (error) {
      console.error('Password change failed:', error);
      const message = error.response?.data?.detail || t('error');
      alert(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  // 프로필 폼 핸들러
  const handleProfileFormChange = (field, value) => {
    setProfileForm(prev => ({ ...prev, [field]: value }));
  };

  // 비밀번호 폼 핸들러
  const handlePasswordFormChange = (field, value) => {
    setPasswordForm(prev => ({ ...prev, [field]: value }));
  };

  // 사용자 이름의 첫 글자 추출
  const getInitial = () => {
    if (user?.name) return user.name.charAt(0);
    if (user?.email) return user.email.charAt(0).toUpperCase();
    return '?';
  };

  const ToggleSwitch = ({ checked, onChange }) => (
    <button
      type="button"
      className={`toggle-switch ${checked ? 'toggle-switch--active' : ''}`}
      onClick={onChange}
      role="switch"
      aria-checked={checked}
    >
      <span className="toggle-switch__thumb" />
    </button>
  );

  if (loading) {
    return (
      <div className="settings settings--loading">
        <div className="settings__loader">
          <div className="settings__spinner" />
          <p>설정을 불러오는 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="settings">
      <div className="settings__header">
        <button className="settings__back" onClick={() => navigate(-1)}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M15 18l-6-6 6-6" />
          </svg>
        </button>
        <div className="settings__header-content">
          <svg className="settings__header-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
          <h1 className="settings__title">설정</h1>
        </div>
      </div>

      <div className="settings__content">
        {/* 프로필 섹션 */}
        <section className="settings__section">
          <h2 className="settings__section-title">{t('profile')}</h2>
          <div className="settings__card">
            <div className="profile-info">
              <div className="profile-info__avatar">
                <span>{getInitial()}</span>
              </div>
              <div className="profile-info__details">
                <h3 className="profile-info__name">{user?.name || user?.email || ''}</h3>
                <p className="profile-info__email">{user?.email}</p>
                {user?.department && <p className="profile-info__dept">{user.school ? `${user.school} ` : ''}{user.department}</p>}
                <button className="profile-info__manage-button" onClick={() => setShowProfileModal(true)}>{t('manageInfo')}</button>
              </div>
            </div>
          </div>
        </section>

        {/* 계정 연결 섹션 */}
        <section className="settings__section">
          <h2 className="settings__section-title">{t('accountConnection')}</h2>
          <div className="settings__card">
            <div className="account-item">
              <div className="account-item__info">
                <div className="account-item__icon account-item__icon--google">
                  <svg width="18" height="18" viewBox="0 0 24 24">
                    <path fill="#fff" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#fff" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#fff" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#fff" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                </div>
                <div className="account-item__text">
                  <span className="account-item__name">Google 계정</span>
                  <span className="account-item__status">
                    {connectedAccounts.google.connected ? connectedAccounts.google.email : t('notConnected')}
                  </span>
                </div>
              </div>
              <ToggleSwitch
                checked={connectedAccounts.google.connected}
                onChange={() => handleAccountToggle('google')}
              />
            </div>

            <div className="account-item">
              <div className="account-item__info">
                <div className="account-item__icon account-item__icon--kakao">
                  <svg width="18" height="18" viewBox="0 0 24 24">
                    <path fill="#3C1E1E" d="M12 3C6.5 3 2 6.58 2 11c0 2.8 1.8 5.3 4.5 6.7l-.9 3.5c-.1.3.2.6.5.5l4-2.2c.6.1 1.3.1 1.9.1 5.5 0 10-3.58 10-8s-4.5-8-10-8z"/>
                  </svg>
                </div>
                <div className="account-item__text">
                  <span className="account-item__name">카카오톡</span>
                  <span className="account-item__status">
                    {connectedAccounts.kakao.connected ? connectedAccounts.kakao.email : t('notConnected')}
                  </span>
                </div>
              </div>
              <ToggleSwitch
                checked={connectedAccounts.kakao.connected}
                onChange={() => handleAccountToggle('kakao')}
              />
            </div>

            <div className="account-item">
              <div className="account-item__info">
                <div className="account-item__icon account-item__icon--naver">
                  <svg width="16" height="16" viewBox="0 0 24 24">
                    <path fill="#fff" d="M16.273 12.845L7.376 0H0v24h7.727V11.155L16.624 24H24V0h-7.727v12.845z"/>
                  </svg>
                </div>
                <div className="account-item__text">
                  <span className="account-item__name">네이버</span>
                  <span className="account-item__status">
                    {connectedAccounts.naver.connected ? connectedAccounts.naver.email : t('notConnected')}
                  </span>
                </div>
              </div>
              <ToggleSwitch
                checked={connectedAccounts.naver.connected}
                onChange={() => handleAccountToggle('naver')}
              />
            </div>
          </div>
        </section>

        {/* 일반 설정 섹션 */}
        <section className="settings__section">
          <h2 className="settings__section-title">{t('general')}</h2>
          <div className="settings__card">
            <div className="settings-item">
              <div className="settings-item__text">
                <span className="settings-item__label">{t('language')}</span>
                <span className="settings-item__desc">{t('languageDesc')}</span>
              </div>
              <select
                className="settings-item__select"
                value={settings.language}
                onChange={(e) => handleSelectChange('language', e.target.value)}
              >
                {supportedLanguages.map(lang => (
                  <option key={lang.code} value={lang.code}>{lang.name}</option>
                ))}
              </select>
            </div>

            <div className="settings-item">
              <div className="settings-item__text">
                <span className="settings-item__label">{t('theme')}</span>
                <span className="settings-item__desc">{t('themeDesc')}</span>
              </div>
              <select
                className="settings-item__select"
                value={settings.theme}
                onChange={(e) => handleSelectChange('theme', e.target.value)}
              >
                <option value="light">{t('lightMode')}</option>
                <option value="dark">{t('darkMode')}</option>
                <option value="system">{t('systemTheme')}</option>
              </select>
            </div>
          </div>
        </section>

        {/* 알림 섹션 */}
        <section className="settings__section">
          <h2 className="settings__section-title">{t('notifications')}</h2>
          <div className="settings__card">
            <div className="settings-item">
              <div className="settings-item__text">
                <span className="settings-item__label">{t('pushNotification')}</span>
                <span className="settings-item__desc">{t('pushNotificationDesc')}</span>
              </div>
              <ToggleSwitch
                checked={settings.pushNotification}
                onChange={() => handleToggle('pushNotification')}
              />
            </div>

            <div className="settings-item">
              <div className="settings-item__text">
                <span className="settings-item__label">{t('notificationSound')}</span>
                <span className="settings-item__desc">{t('notificationSoundDesc')}</span>
              </div>
              <ToggleSwitch
                checked={settings.notificationSound}
                onChange={() => handleToggle('notificationSound')}
              />
            </div>

            <div className="settings-item">
              <div className="settings-item__text">
                <span className="settings-item__label">{t('vibration')}</span>
                <span className="settings-item__desc">{t('vibrationDesc')}</span>
              </div>
              <ToggleSwitch
                checked={settings.vibration}
                onChange={() => handleToggle('vibration')}
              />
            </div>

            <div className="settings-item">
              <div className="settings-item__text">
                <span className="settings-item__label">{t('doNotDisturb')}</span>
                <span className="settings-item__desc">{t('doNotDisturbDesc')}</span>
              </div>
              <ToggleSwitch
                checked={settings.doNotDisturb}
                onChange={() => handleToggle('doNotDisturb')}
              />
            </div>

            {settings.doNotDisturb && (
              <>
                <div className="settings-item settings-item--sub">
                  <div className="settings-item__text">
                    <span className="settings-item__label">{t('doNotDisturbStart')}</span>
                  </div>
                  <input
                    type="time"
                    className="settings-item__time-input"
                    value={settings.doNotDisturbStart || '22:00'}
                    onChange={(e) => handleSelectChange('doNotDisturbStart', e.target.value)}
                  />
                </div>
                <div className="settings-item settings-item--sub">
                  <div className="settings-item__text">
                    <span className="settings-item__label">{t('doNotDisturbEnd')}</span>
                  </div>
                  <input
                    type="time"
                    className="settings-item__time-input"
                    value={settings.doNotDisturbEnd || '08:00'}
                    onChange={(e) => handleSelectChange('doNotDisturbEnd', e.target.value)}
                  />
                </div>
              </>
            )}

            <div className="settings-item">
              <div className="settings-item__text">
                <span className="settings-item__label">{t('deadlineAlert')}</span>
                <span className="settings-item__desc">{t('deadlineAlertDesc')}</span>
              </div>
              <ToggleSwitch
                checked={settings.deadlineAlert}
                onChange={() => handleToggle('deadlineAlert')}
              />
            </div>

            {settings.deadlineAlert && (
              <div className="settings-item settings-item--sub">
                <div className="settings-item__text">
                  <span className="settings-item__label">{t('deadlineAlertTime')}</span>
                  <span className="settings-item__desc">{t('deadlineAlertTimeDesc')}</span>
                </div>
                <select
                  className="settings-item__select"
                  value={settings.deadlineAlertMinutes || 60}
                  onChange={(e) => handleSelectChange('deadlineAlertMinutes', Number(e.target.value))}
                >
                  <option value={15}>{t('min15')}</option>
                  <option value={30}>{t('min30')}</option>
                  <option value={60}>{t('hour1')}</option>
                  <option value={120}>{t('hour2')}</option>
                  <option value={1440}>{t('day1')}</option>
                </select>
              </div>
            )}

            <div className="settings-item">
              <div className="settings-item__text">
                <span className="settings-item__label">{t('dailyBriefing')}</span>
                <span className="settings-item__desc">{t('dailyBriefingDesc')}</span>
              </div>
              <ToggleSwitch
                checked={settings.dailySummary}
                onChange={() => handleToggle('dailySummary')}
              />
            </div>

            {settings.dailySummary && (
              <div className="settings-item settings-item--sub">
                <div className="settings-item__text">
                  <span className="settings-item__label">{t('briefingTime')}</span>
                  <span className="settings-item__desc">{t('briefingTimeDesc')}</span>
                </div>
                <input
                  type="time"
                  className="settings-item__time-input"
                  value={settings.dailySummaryTime || '08:00'}
                  onChange={(e) => handleSelectChange('dailySummaryTime', e.target.value)}
                />
              </div>
            )}

            {settings.dailySummary && (
              <div className="settings-item settings-item--sub">
                <div className="settings-item__text">
                  <span className="settings-item__label">{t('briefingTest')}</span>
                  <span className="settings-item__desc">{t('briefingTestDesc')}</span>
                </div>
                <button
                  className="settings-item__button"
                  onClick={async () => {
                    const result = await triggerDailyBriefing();
                    if (result) {
                      alert(t('success'));
                    } else {
                      alert(t('error'));
                    }
                  }}
                >
                  {t('test')}
                </button>
              </div>
            )}
          </div>
        </section>

        {/* 개인정보 섹션 */}
        <section className="settings__section">
          <h2 className="settings__section-title">{t('privacy')}</h2>
          <div className="settings__card">
            <div className="settings-item">
              <div className="settings-item__text">
                <span className="settings-item__label">{t('autoLock')}</span>
                <span className="settings-item__desc">{t('autoLockDesc')}</span>
              </div>
              <select
                className="settings-item__select"
                value={settings.autoLock}
                onChange={(e) => handleSelectChange('autoLock', e.target.value)}
              >
                <option value="1">1{t('minute')}</option>
                <option value="5">5{t('minute')}</option>
                <option value="10">10{t('minute')}</option>
                <option value="30">30{t('minute')}</option>
                <option value="never">{t('notUsed')}</option>
              </select>
            </div>

            <div className="settings-item">
              <div className="settings-item__text">
                <span className="settings-item__label">{t('analyticsData')}</span>
                <span className="settings-item__desc">{t('analyticsDataDesc')}</span>
              </div>
              <ToggleSwitch
                checked={settings.analyticsData}
                onChange={() => handleToggle('analyticsData')}
              />
            </div>

            <div className="settings-item">
              <div className="settings-item__text">
                <span className="settings-item__label">{t('errorReport')}</span>
                <span className="settings-item__desc">{t('errorReportDesc')}</span>
              </div>
              <ToggleSwitch
                checked={settings.errorReport}
                onChange={() => handleToggle('errorReport')}
              />
            </div>
          </div>
        </section>

        {/* 앱 정보 섹션 */}
        <section className="settings__section">
          <h2 className="settings__section-title">{t('appInfo')}</h2>
          <div className="settings__card">
            <div className="settings-item settings-item--info">
              <span className="settings-item__label">{t('version')}</span>
              <span className="settings-item__value">1.0.0</span>
            </div>
            <div className="settings-item settings-item--info">
              <span className="settings-item__label">{t('developer')}</span>
              <span className="settings-item__value">Team F5</span>
            </div>
            <div className="settings-item settings-item--info">
              <span className="settings-item__label">{t('license')}</span>
              <button className="settings-item__link" onClick={() => setShowLicenseModal(true)}>{t('view')}</button>
            </div>
          </div>
        </section>

        {/* 기타 버튼들 */}
        <section className="settings__section">
          <div className="settings__actions">
            <button className="settings__action-btn" onClick={handleClearCache}>
              {t('clearCache')}
              <span className="settings__action-info">({formatBytes(cacheSize)})</span>
            </button>
            <button className="settings__action-btn" onClick={() => setShowPasswordModal(true)}>
              {t('changePassword')}
            </button>
            <button className="settings__action-btn settings__action-btn--danger" onClick={() => setShowLogoutModal(true)}>
              {t('logout')}
            </button>
            <button className="settings__action-btn settings__action-btn--danger" onClick={() => setShowDeleteAccountModal(true)}>
              {t('deleteAccount')}
            </button>
          </div>
        </section>
      </div>

      {/* 로그아웃 확인 모달 */}
      {showLogoutModal && (
        <div className="license-modal__overlay" onClick={() => setShowLogoutModal(false)}>
          <div className="license-modal license-modal--confirm" onClick={(e) => e.stopPropagation()}>
            <div className="license-modal__header">
              <h2 className="license-modal__title">{t('logout')}</h2>
              <button className="license-modal__close" onClick={() => setShowLogoutModal(false)}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
            <div className="license-modal__content">
              <p className="confirm-modal__message">{t('logoutConfirm')}</p>
              <div className="confirm-modal__buttons">
                <button className="confirm-modal__btn confirm-modal__btn--cancel" onClick={() => setShowLogoutModal(false)}>
                  {t('cancel')}
                </button>
                <button className="confirm-modal__btn confirm-modal__btn--confirm" onClick={handleLogout}>
                  {t('logout')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 계정 삭제 확인 모달 */}
      {showDeleteAccountModal && (
        <div className="license-modal__overlay" onClick={() => setShowDeleteAccountModal(false)}>
          <div className="license-modal license-modal--confirm" onClick={(e) => e.stopPropagation()}>
            <div className="license-modal__header">
              <h2 className="license-modal__title">{t('deleteAccount')}</h2>
              <button className="license-modal__close" onClick={() => setShowDeleteAccountModal(false)}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
            <div className="license-modal__content">
              <p className="confirm-modal__message">
                ⚠️ {t('deleteAccountWarning')}<br/>
                {t('deleteAccountConfirm')}
              </p>
              <div className="profile-modal__field">
                <label className="profile-modal__label">{t('passwordConfirm')}</label>
                <input 
                  type="password" 
                  className="profile-modal__input" 
                  value={deletePassword}
                  onChange={(e) => setDeletePassword(e.target.value)}
                  placeholder={t('currentPassword')}
                />
              </div>
              <div className="confirm-modal__buttons">
                <button className="confirm-modal__btn confirm-modal__btn--cancel" onClick={() => {
                  setShowDeleteAccountModal(false);
                  setDeletePassword('');
                }}>
                  {t('cancel')}
                </button>
                <button 
                  className="confirm-modal__btn confirm-modal__btn--danger" 
                  onClick={handleDeleteAccount}
                  disabled={isSubmitting}
                >
                  {isSubmitting ? t('loading') : t('delete')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 라이선스 모달 */}
      {showLicenseModal && (
        <div className="license-modal__overlay" onClick={() => setShowLicenseModal(false)}>
          <div className="license-modal" onClick={(e) => e.stopPropagation()}>
            <div className="license-modal__header">
              <h2 className="license-modal__title">오픈소스 라이선스</h2>
              <button className="license-modal__close" onClick={() => setShowLicenseModal(false)}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
            <div className="license-modal__content">
              <div className="license-modal__section">
                <h3 className="license-modal__section-title">React</h3>
                <p className="license-modal__license-type">MIT License</p>
                <p className="license-modal__text">
                  Copyright (c) Meta Platforms, Inc. and affiliates.
                </p>
              </div>
              
              <div className="license-modal__section">
                <h3 className="license-modal__section-title">React Router</h3>
                <p className="license-modal__license-type">MIT License</p>
                <p className="license-modal__text">
                  Copyright (c) React Training LLC
                </p>
              </div>
              
              <div className="license-modal__section">
                <h3 className="license-modal__section-title">Vite</h3>
                <p className="license-modal__license-type">MIT License</p>
                <p className="license-modal__text">
                  Copyright (c) 2019-present, Yuxi (Evan) You and Vite contributors
                </p>
              </div>

              <div className="license-modal__section">
                <h3 className="license-modal__section-title">date-fns</h3>
                <p className="license-modal__license-type">MIT License</p>
                <p className="license-modal__text">
                  Copyright (c) 2021 Sasha Koss and Lesha Koss
                </p>
              </div>

              <div className="license-modal__divider" />

              <div className="license-modal__full-license">
                <h4 className="license-modal__full-title">MIT License 전문</h4>
                <p className="license-modal__full-text">
                  Permission is hereby granted, free of charge, to any person obtaining a copy
                  of this software and associated documentation files (the "Software"), to deal
                  in the Software without restriction, including without limitation the rights
                  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
                  copies of the Software, and to permit persons to whom the Software is
                  furnished to do so, subject to the following conditions:
                </p>
                <p className="license-modal__full-text">
                  The above copyright notice and this permission notice shall be included in all
                  copies or substantial portions of the Software.
                </p>
                <p className="license-modal__full-text">
                  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
                  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
                  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
                  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
                  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
                  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
                  SOFTWARE.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 내 정보 관리 모달 */}
      {showProfileModal && (
        <div className="license-modal__overlay" onClick={() => setShowProfileModal(false)}>
          <div className="license-modal license-modal--profile" onClick={(e) => e.stopPropagation()}>
            <div className="license-modal__header">
              <h2 className="license-modal__title">{t('manageInfo')}</h2>
              <button className="license-modal__close" onClick={() => setShowProfileModal(false)}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
            <div className="license-modal__content">
              <div className="profile-modal__avatar-section">
                <div className="profile-modal__avatar">
                  <span>{getInitial()}</span>
                </div>
              </div>
              
              <div className="profile-modal__form">
                <div className="profile-modal__field">
                  <label className="profile-modal__label">{t('email')}</label>
                  <input 
                    type="email" 
                    className="profile-modal__input profile-modal__input--disabled" 
                    value={user?.email || ''}
                    disabled
                  />
                </div>
                
                <div className="profile-modal__field">
                  <label className="profile-modal__label">{t('name')}</label>
                  <input 
                    type="text" 
                    className="profile-modal__input" 
                    value={profileForm.name}
                    onChange={(e) => handleProfileFormChange('name', e.target.value)}
                    placeholder={t('namePlaceholder')}
                  />
                </div>
                
                <div className="profile-modal__field">
                  <label className="profile-modal__label">{t('school')}</label>
                  <input 
                    type="text" 
                    className="profile-modal__input" 
                    value={profileForm.school}
                    onChange={(e) => handleProfileFormChange('school', e.target.value)}
                    placeholder={t('schoolPlaceholder')}
                  />
                </div>
                
                <div className="profile-modal__field">
                  <label className="profile-modal__label">{t('department')}</label>
                  <input 
                    type="text" 
                    className="profile-modal__input" 
                    value={profileForm.department}
                    onChange={(e) => handleProfileFormChange('department', e.target.value)}
                    placeholder={t('departmentPlaceholder')}
                  />
                </div>
                
                <div className="profile-modal__field">
                  <label className="profile-modal__label">{t('grade')}</label>
                  <select 
                    className="profile-modal__select" 
                    value={profileForm.grade}
                    onChange={(e) => handleProfileFormChange('grade', e.target.value)}
                  >
                    <option value="">{t('gradePlaceholder')}</option>
                    <option value="1">{t('grade1')}</option>
                    <option value="2">{t('grade2')}</option>
                    <option value="3">{t('grade3')}</option>
                    <option value="4">{t('grade4')}</option>
                    <option value="grad">{t('gradeGrad')}</option>
                    <option value="other">{t('gradeOther')}</option>
                  </select>
                </div>
              </div>
              
              <div className="profile-modal__actions">
                <button className="profile-modal__btn profile-modal__btn--cancel" onClick={() => setShowProfileModal(false)}>
                  {t('cancel')}
                </button>
                <button 
                  className="profile-modal__btn profile-modal__btn--save" 
                  onClick={handleSaveProfile}
                  disabled={isSubmitting}
                >
                  {isSubmitting ? t('loading') : t('save')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 비밀번호 변경 모달 */}
      {showPasswordModal && (
        <div className="license-modal__overlay" onClick={() => setShowPasswordModal(false)}>
          <div className="license-modal license-modal--profile" onClick={(e) => e.stopPropagation()}>
            <div className="license-modal__header">
              <h2 className="license-modal__title">{t('changePassword')}</h2>
              <button className="license-modal__close" onClick={() => setShowPasswordModal(false)}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
            <div className="license-modal__content">
              <div className="profile-modal__form">
                <div className="profile-modal__field">
                  <label className="profile-modal__label">{t('currentPassword')}</label>
                  <input 
                    type="password" 
                    className="profile-modal__input" 
                    value={passwordForm.currentPassword}
                    onChange={(e) => handlePasswordFormChange('currentPassword', e.target.value)}
                    placeholder={t('currentPassword')}
                  />
                </div>
                
                <div className="profile-modal__field">
                  <label className="profile-modal__label">{t('newPassword')}</label>
                  <input 
                    type="password" 
                    className="profile-modal__input" 
                    value={passwordForm.newPassword}
                    onChange={(e) => handlePasswordFormChange('newPassword', e.target.value)}
                    placeholder={t('newPassword')}
                  />
                </div>
                
                <div className="profile-modal__field">
                  <label className="profile-modal__label">{t('newPasswordConfirm')}</label>
                  <input 
                    type="password" 
                    className="profile-modal__input" 
                    value={passwordForm.newPasswordConfirm}
                    onChange={(e) => handlePasswordFormChange('newPasswordConfirm', e.target.value)}
                    placeholder={t('newPasswordConfirm')}
                  />
                </div>
              </div>
              
              <div className="profile-modal__actions">
                <button className="profile-modal__btn profile-modal__btn--cancel" onClick={() => {
                  setShowPasswordModal(false);
                  setPasswordForm({ currentPassword: '', newPassword: '', newPasswordConfirm: '' });
                }}>
                  {t('cancel')}
                </button>
                <button 
                  className="profile-modal__btn profile-modal__btn--save" 
                  onClick={handleChangePassword}
                  disabled={isSubmitting}
                >
                  {isSubmitting ? t('loading') : t('confirm')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Settings;