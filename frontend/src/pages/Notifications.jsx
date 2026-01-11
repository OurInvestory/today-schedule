import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Notifications.css';

const Notifications = () => {
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState([
    {
      id: 1,
      type: 'deadline',
      title: '과제 마감 임박',
      message: '프로그래밍 과제가 2시간 후에 마감됩니다.',
      time: '10분 전',
      isRead: false,
    },
    {
      id: 2,
      type: 'reminder',
      title: '일정 알림',
      message: '팀 미팅이 30분 후에 시작됩니다.',
      time: '25분 전',
      isRead: false,
    },
    {
      id: 3,
      type: 'complete',
      title: '할 일 완료',
      message: '보고서 작성을 완료했습니다!',
      time: '1시간 전',
      isRead: true,
    },
    {
      id: 4,
      type: 'info',
      title: '새로운 일정 추가됨',
      message: 'AI가 새로운 학습 일정을 추천했습니다.',
      time: '2시간 전',
      isRead: true,
    },
  ]);

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
  };

  const handleMarkAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, isRead: true })));
  };

  const handleDelete = (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
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
          <div className="notifications__header-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
          </div>
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

      <div className="notifications__content">
        {notifications.length === 0 ? (
          <div className="notifications__empty">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
            <p>새로운 알림이 없습니다</p>
          </div>
        ) : (
          <div className="notifications__list">
            {notifications.map(notification => (
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
