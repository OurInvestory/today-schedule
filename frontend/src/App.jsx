import React, { useEffect, useState, useCallback } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Header from './components/layout/Header';
import Home from './pages/Home';
import FullCalendar from './pages/FullCalendar';
import TaskDetail from './pages/TaskDetail';
import ScheduleDetail from './pages/ScheduleDetail';
import Archive from './pages/Archive';
import Notifications from './pages/Notifications';
import Settings from './pages/Settings';
import Timetable from './pages/Timetable';
import Login from './pages/Login';
import Signup from './pages/Signup';
import ErrorBoundary from './components/common/ErrorBoundary';
import { ToastProvider } from './components/common/Toast';
import NetworkStatus from './components/common/NetworkStatus';
import LoginModal from './components/common/LoginModal';
import { AuthProvider } from './context/AuthContext';
import {
  initNotificationService,
  cleanupNotificationService,
} from './services/notificationService';
import {
  startNotificationPolling,
  stopNotificationPolling,
  requestNotificationPermission as requestApiNotificationPermission,
  getMyNotifications,
} from './services/notificationApiService';
import './App.css';

// 알림 권한 요청 함수
const requestNotificationPermission = async () => {
  if (!('Notification' in window)) {
    console.log('이 브라우저는 알림을 지원하지 않습니다.');
    return false;
  }

  if (Notification.permission === 'granted') {
    return true;
  }

  if (Notification.permission !== 'denied') {
    const permission = await Notification.requestPermission();
    return permission === 'granted';
  }

  return false;
};

function App() {
  const [hasUnreadNotifications, setHasUnreadNotifications] = useState(false);

  // 읽지 않은 알림 개수 확인
  const checkUnreadNotifications = useCallback(async () => {
    try {
      const response = await getMyNotifications(50, true);
      const notifications = response?.data?.data || response?.data || [];
      const unreadCount = notifications.filter((n) => !n.is_checked).length;
      setHasUnreadNotifications(unreadCount > 0);
    } catch (error) {
      console.error('Failed to check unread notifications:', error);
    }
  }, []);

  // 앱 시작 시 알림 권한 요청 및 알림 서비스 초기화
  useEffect(() => {
    requestNotificationPermission().then((granted) => {
      if (granted) {
        console.log('알림 권한이 허용되었습니다.');
        // 알림 서비스 초기화 (마감 알림, 데일리 브리핑 스케줄러 시작)
        initNotificationService();
        // 백엔드 알림 폴링 시작 (새 알림 시 빨간점 즉시 업데이트)
        requestApiNotificationPermission();
        startNotificationPolling(() => {
          // 새 알림이 감지되면 즉시 읽지 않은 알림 확인
          checkUnreadNotifications();
        });
      } else {
        console.log('알림 권한이 거부되었습니다.');
      }
    });

    // 읽지 않은 알림 확인
    checkUnreadNotifications();

    // 30초마다 읽지 않은 알림 확인
    const interval = setInterval(checkUnreadNotifications, 30000);

    // 클린업
    return () => {
      cleanupNotificationService();
      stopNotificationPolling();
      clearInterval(interval);
    };
  }, [checkUnreadNotifications]);

  return (
    <ErrorBoundary>
      <AuthProvider>
        <ToastProvider>
          <BrowserRouter>
            <NetworkStatus />
            <LoginModal />
            <div className="app">
              <Routes>
                {/* 인증 페이지 (헤더 없음) */}
                <Route path="/login" element={<Login />} />
                <Route path="/signup" element={<Signup />} />
                
                {/* 헤더가 있는 레이아웃 */}
                <Route
                  path="/"
                  element={
                    <>
                      <Header hasNotification={hasUnreadNotifications} />
                      <div className="app__content">
                      <Home />
                    </div>
                  </>
                }
              />
              <Route
                path="/task/:id"
                element={
                  <>
                    <Header hasNotification={hasUnreadNotifications} />
                    <div className="app__content">
                      <TaskDetail />
                    </div>
                  </>
                }
              />
              <Route
                path="/schedule/:id"
                element={
                  <>
                    <Header hasNotification={hasUnreadNotifications} />
                    <div className="app__content">
                      <ScheduleDetail />
                    </div>
                  </>
                }
              />
              <Route
                path="/archive"
                element={
                  <>
                    <Header hasNotification={hasUnreadNotifications} />
                    <div className="app__content">
                      <Archive />
                    </div>
                  </>
                }
              />

              {/* 독립 페이지 (헤더/네비게이션 없음) */}
              <Route path="/calendar" element={<FullCalendar />} />
              <Route path="/notifications" element={<Notifications />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/timetable" element={<Timetable />} />
            </Routes>
          </div>
        </BrowserRouter>
      </ToastProvider>
    </AuthProvider>
  </ErrorBoundary>
  );
}

export default App;
