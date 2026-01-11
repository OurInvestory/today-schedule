import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getNotificationSettings, updateNotificationSettings } from '../services/notificationService';
import './Settings.css';

const Settings = () => {
  const navigate = useNavigate();
  const [settings, setSettings] = useState({
    pushNotification: true,
    notificationSound: true,
    vibration: true,
    doNotDisturb: false,
    dailySummary: true,
    dailySummaryTime: '08:00',
    deadlineAlert: true,
    autoLock: '5',
    analyticsData: false,
    errorReport: true,
  });
  const [loading, setLoading] = useState(true);

  const [connectedAccounts, setConnectedAccounts] = useState({
    google: { connected: true, email: 'student@gmail.com' },
    kakao: { connected: false },
    naver: { connected: false },
  });

  useEffect(() => {
    fetchSettings();
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

  const handleSelectChange = async (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
    
    try {
      await updateNotificationSettings({ [key]: value });
    } catch (error) {
      console.error('Failed to update setting:', error);
    }
  };

  const handleAccountToggle = (provider) => {
    setConnectedAccounts(prev => ({
      ...prev,
      [provider]: {
        ...prev[provider],
        connected: !prev[provider].connected,
      },
    }));
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
          <div className="settings__header-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
            </svg>
          </div>
          <h1 className="settings__title">설정</h1>
        </div>
      </div>

      <div className="settings__content">
        {/* 프로필 섹션 */}
        <section className="settings__section">
          <h2 className="settings__section-title">프로필</h2>
          <div className="settings__card">
            <div className="profile-info">
              <div className="profile-info__avatar">
                <span>김</span>
              </div>
              <div className="profile-info__details">
                <h3 className="profile-info__name">김학생</h3>
                <p className="profile-info__email">student@university.ac.kr</p>
                <p className="profile-info__dept">컴퓨터공학과 · 3학년</p>
              </div>
            </div>
          </div>
        </section>

        {/* 계정 연결 섹션 */}
        <section className="settings__section">
          <h2 className="settings__section-title">계정 연결</h2>
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
                    {connectedAccounts.google.connected ? connectedAccounts.google.email : '연결되지 않음'}
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
                  <span className="account-item__status">연결되지 않음</span>
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
                  <span className="account-item__status">연결되지 않음</span>
                </div>
              </div>
              <ToggleSwitch
                checked={connectedAccounts.naver.connected}
                onChange={() => handleAccountToggle('naver')}
              />
            </div>
          </div>
        </section>

        {/* 알림 섹션 */}
        <section className="settings__section">
          <h2 className="settings__section-title">알림</h2>
          <div className="settings__card">
            <div className="settings-item">
              <div className="settings-item__text">
                <span className="settings-item__label">푸시 알림 허용</span>
                <span className="settings-item__desc">새로운 일정과 알림을 받습니다</span>
              </div>
              <ToggleSwitch
                checked={settings.pushNotification}
                onChange={() => handleToggle('pushNotification')}
              />
            </div>

            <div className="settings-item">
              <div className="settings-item__text">
                <span className="settings-item__label">알림음</span>
                <span className="settings-item__desc">알림 시 소리를 재생합니다</span>
              </div>
              <ToggleSwitch
                checked={settings.notificationSound}
                onChange={() => handleToggle('notificationSound')}
              />
            </div>

            <div className="settings-item">
              <div className="settings-item__text">
                <span className="settings-item__label">진동</span>
                <span className="settings-item__desc">알림 시 진동을 사용합니다</span>
              </div>
              <ToggleSwitch
                checked={settings.vibration}
                onChange={() => handleToggle('vibration')}
              />
            </div>

            <div className="settings-item">
              <div className="settings-item__text">
                <span className="settings-item__label">방해 금지 모드</span>
                <span className="settings-item__desc">설정한 시간에는 알림을 받지 않습니다</span>
              </div>
              <ToggleSwitch
                checked={settings.doNotDisturb}
                onChange={() => handleToggle('doNotDisturb')}
              />
            </div>

            <div className="settings-item">
              <div className="settings-item__text">
                <span className="settings-item__label">마감 전 알림</span>
                <span className="settings-item__desc">할 일 마감 전에 알림을 받습니다</span>
              </div>
              <ToggleSwitch
                checked={settings.deadlineAlert}
                onChange={() => handleToggle('deadlineAlert')}
              />
            </div>

            {settings.deadlineAlert && (
              <div className="settings-item settings-item--sub">
                <div className="settings-item__text">
                  <span className="settings-item__label">마감 전 알림 시간</span>
                  <span className="settings-item__desc">마감 몇 분 전에 알림을 받을지 설정</span>
                </div>
                <select
                  className="settings-item__select"
                  value={settings.deadlineAlertMinutes || 60}
                  onChange={(e) => handleSelectChange('deadlineAlertMinutes', Number(e.target.value))}
                >
                  <option value={15}>15분 전</option>
                  <option value={30}>30분 전</option>
                  <option value={60}>1시간 전</option>
                  <option value={120}>2시간 전</option>
                  <option value={1440}>1일 전</option>
                </select>
              </div>
            )}

            <div className="settings-item">
              <div className="settings-item__text">
                <span className="settings-item__label">AI 데일리 브리핑</span>
                <span className="settings-item__desc">매일 아침 AI가 일정을 정리해서 알려줍니다</span>
              </div>
              <ToggleSwitch
                checked={settings.dailySummary}
                onChange={() => handleToggle('dailySummary')}
              />
            </div>

            {settings.dailySummary && (
              <div className="settings-item settings-item--sub">
                <div className="settings-item__text">
                  <span className="settings-item__label">브리핑 시간</span>
                  <span className="settings-item__desc">매일 이 시간에 일정 요약을 받습니다</span>
                </div>
                <input
                  type="time"
                  className="settings-item__time-input"
                  value={settings.dailySummaryTime || '08:00'}
                  onChange={(e) => handleSelectChange('dailySummaryTime', e.target.value)}
                />
              </div>
            )}
          </div>
        </section>

        {/* 개인정보 섹션 */}
        <section className="settings__section">
          <h2 className="settings__section-title">개인정보</h2>
          <div className="settings__card">
            <div className="settings-item">
              <div className="settings-item__text">
                <span className="settings-item__label">자동 잠금</span>
                <span className="settings-item__desc">일정 시간 후 자동으로 잠급니다</span>
              </div>
              <select
                className="settings-item__select"
                value={settings.autoLock}
                onChange={(e) => handleSelectChange('autoLock', e.target.value)}
              >
                <option value="1">1분</option>
                <option value="5">5분</option>
                <option value="10">10분</option>
                <option value="30">30분</option>
                <option value="never">사용 안함</option>
              </select>
            </div>

            <div className="settings-item">
              <div className="settings-item__text">
                <span className="settings-item__label">사용 분석 데이터</span>
                <span className="settings-item__desc">앱 개선을 위한 익명 데이터 수집</span>
              </div>
              <ToggleSwitch
                checked={settings.analyticsData}
                onChange={() => handleToggle('analyticsData')}
              />
            </div>

            <div className="settings-item">
              <div className="settings-item__text">
                <span className="settings-item__label">오류 보고서</span>
                <span className="settings-item__desc">앱 오류 발생 시 자동으로 보고합니다</span>
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
          <h2 className="settings__section-title">앱 정보</h2>
          <div className="settings__card">
            <div className="settings-item settings-item--info">
              <span className="settings-item__label">버전</span>
              <span className="settings-item__value">1.0.0</span>
            </div>
            <div className="settings-item settings-item--info">
              <span className="settings-item__label">개발자</span>
              <span className="settings-item__value">Team F5</span>
            </div>
            <div className="settings-item settings-item--info">
              <span className="settings-item__label">라이선스</span>
              <button className="settings-item__link">보기</button>
            </div>
          </div>
        </section>

        {/* 기타 버튼들 */}
        <section className="settings__section">
          <div className="settings__actions">
            <button className="settings__action-btn">캐시 삭제</button>
            <button className="settings__action-btn settings__action-btn--danger">로그아웃</button>
            <button className="settings__action-btn settings__action-btn--danger">계정 삭제</button>
          </div>
        </section>
      </div>
    </div>
  );
};

export default Settings;