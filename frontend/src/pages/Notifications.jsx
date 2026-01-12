import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  getNotifications,
  markNotificationAsRead,
  markAllNotificationsAsRead,
  deleteNotification,
  triggerDailyBriefing,
} from '../services/notificationService';
import './Notifications.css';

// 상대 시간 포맷팅 함수
const formatTimeAgo = (date) => {
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  if (diffMins < 1) return '방금 전';
  if (diffMins < 60) return `${diffMins}분 전`;
  if (diffHours < 24) return `${diffHours}시간 전`;
  return `${diffDays}일 전`;
};

// 초기 알림 데이터 가져오기
const getInitialNotifications = () => {
  const stored = getNotifications();
  if (stored.length > 0) {
    return stored.map(n => ({
      ...n,
      time: formatTimeAgo(new Date(n.timestamp)),
    }));
  }
  // 샘플 데이터 (처음 실행 시)
  return [
    {
      id: 1,
      type: 'deadline',
      title: '과제 마감 임박',
      message: '프로그래밍 과제가 2시간 후에 마감됩니다.',
      time: '10분 전',
      timestamp: new Date(Date.now() - 10 * 60000).toISOString(),
      isRead: false,
    },
    {
      id: 2,
      type: 'reminder',
      title: '일정 알림',
      message: '팀 미팅이 30분 후에 시작됩니다.',
      time: '25분 전',
      timestamp: new Date(Date.now() - 25 * 60000).toISOString(),
      isRead: false,
    },
    {
      id: 3,
      type: 'complete',
      title: '할 일 완료',
      message: '보고서 작성을 완료했습니다!',
      time: '1시간 전',
      timestamp: new Date(Date.now() - 60 * 60000).toISOString(),
      isRead: true,
    },
    {
      id: 4,
      type: 'briefing',
      title: 'AI 데일리 브리핑',
      message: '오늘 할 일 3개 (긴급 1개). 화이팅!',
      time: '2시간 전',
      timestamp: new Date(Date.now() - 120 * 60000).toISOString(),
      isRead: true,
    },
  ];
};

const Notifications = () => {
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState(getInitialNotifications);
  const [filter, setFilter] = useState('all'); // 'all' | 'unread'

  // 필터링된 알림 목록
  const filteredNotifications = useMemo(() => {
    if (filter === 'unread') {
      return notifications.filter(n => !n.isRead);
    }
    return notifications;
  }, [notifications, filter]);

  const getIcon = (type) => {
    switch (type) {
      case 'deadline':
        return (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
        );
      case 'reminder':
        return (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
            <path d="M13.73 21a2 2 0 0 1-3.46 0" />
          </svg>
        );
      case 'complete':
        return (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="20 6 9 17 4 12" />
          </svg>
        );
      case 'briefing':
        return (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="5" />
            <line x1="12" y1="1" x2="12" y2="3" />
            <line x1="12" y1="21" x2="12" y2="23" />
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
            <line x1="1" y1="12" x2="3" y2="12" />
            <line x1="21" y1="12" x2="23" y2="12" />
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
          </svg>
        );
      default:
        return (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="16" x2="12" y2="12" />
            <line x1="12" y1="8" x2="12.01" y2="8" />
          </svg>
        );
    }
  };

  const handleMarkAsRead = (id) => {
    setNotifications(prev =>
      prev.map(n => (n.id === id ? { ...n, isRead: true } : n))
    );
    markNotificationAsRead(id);
  };

  const handleMarkAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, isRead: true })));
    markAllNotificationsAsRead();
  };

  const handleDelete = (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
    deleteNotification(id);
  };

  const handleTriggerBriefing = async () => {
    const result = await triggerDailyBriefing();
    if (result) {
      // 브리핑 결과를 알림 목록에 추가
      const newNotification = {
        id: Date.now(),
        type: 'briefing',
        title: '🌅 AI 데일리 브리핑',
        message: result.message,
        time: '방금 전',
        timestamp: new Date().toISOString(),
        isRead: false,
      };
      setNotifications(prev => [newNotification, ...prev]);
    }
  };

  const unreadCount = notifications.filter(n => !n.isRead).length;

  return (
    <div className="notifications">
      <div className="notifications__header">
        <button className="notifications__back" onClick={() => navigate(-1)}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M15 18l-6-6 6-6" />
          </svg>
        </button>
        <div className="notifications__header-content">
          <svg 
            className="notifications__header-icon"
            width="22" 
            height="22" 
            viewBox="0 0 24 24" 
            fill="none" 
            stroke="currentColor" 
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
            <path d="M13.73 21a2 2 0 0 1-3.46 0" />
          </svg>
          <h1 className="notifications__title">알림</h1>
          {unreadCount > 0 && (
            <span className="notifications__badge">{unreadCount}</span>
          )}
        </div>
        {unreadCount > 0 && (
          <button className="notifications__mark-all" onClick={handleMarkAllAsRead}>
            모두 읽음
          </button>
        )}
      </div>

      {/* 필터 버튼 */}
      <div className="notifications__filter">
        <button
          className={`notifications__filter-btn ${filter === 'all' ? 'notifications__filter-btn--active' : ''}`}
          onClick={() => setFilter('all')}
        >
          전체
          <span className="notifications__filter-count">{notifications.length}</span>
        </button>
        <button
          className={`notifications__filter-btn ${filter === 'unread' ? 'notifications__filter-btn--active' : ''}`}
          onClick={() => setFilter('unread')}
        >
          읽지 않음
          {unreadCount > 0 && (
            <span className="notifications__filter-count notifications__filter-count--unread">
              {unreadCount}
            </span>
          )}
        </button>
      </div>

      <div className="notifications__content">
        {filteredNotifications.length === 0 ? (
          <div className="notifications__empty">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
            <p>{filter === 'unread' ? '읽지 않은 알림이 없습니다' : '새로운 알림이 없습니다'}</p>
          </div>
        ) : (
          <div className="notifications__list">
            {filteredNotifications.map(notification => (
              <div
                key={notification.id}
                className={`notification-item ${!notification.isRead ? 'notification-item--unread' : ''}`}
                onClick={() => handleMarkAsRead(notification.id)}
              >
                <div className={`notification-item__icon notification-item__icon--${notification.type}`}>
                  {getIcon(notification.type)}
                </div>
                <div className="notification-item__content">
                  <h3 className="notification-item__title">{notification.title}</h3>
                  <p className="notification-item__message">{notification.message}</p>
                  <span className="notification-item__time">{notification.time}</span>
                </div>
                <button
                  className="notification-item__delete"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(notification.id);
                  }}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Notifications;
