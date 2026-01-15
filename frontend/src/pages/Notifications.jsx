import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  getMyNotifications,
  checkNotifications,
  deleteNotification,
  startNotificationPolling,
  stopNotificationPolling,
  requestNotificationPermission,
} from '../services/notificationApiService';
import './Notifications.css';

// 시간 포맷팅 함수 (실제 알림 시간 표시)
const formatNotificationTime = (dateStr) => {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  // 미래 시간인 경우 (아직 예약된 알림)
  if (diffMs < 0) {
    const hours = date.getHours().toString().padStart(2, '0');
    const mins = date.getMinutes().toString().padStart(2, '0');
    return `${hours}:${mins} 예정`;
  }

  // 과거 시간인 경우
  if (diffMins < 1) return '방금 전';
  if (diffMins < 60) return `${diffMins}분 전`;
  if (diffHours < 24) return `${diffHours}시간 전`;
  if (diffDays < 7) return `${diffDays}일 전`;

  // 7일 이상이면 날짜 표시
  const month = date.getMonth() + 1;
  const day = date.getDate();
  return `${month}/${day}`;
};

const Notifications = () => {
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [swipingId, setSwipingId] = useState(null);
  const [swipeOffset, setSwipeOffset] = useState(0);
  const touchStartX = useRef(0);
  const touchCurrentX = useRef(0);
  const isSwiping = useRef(false);
  const SWIPE_THRESHOLD = 80; // 삭제 트리거 임계값

  // 알림 목록 로드
  const loadNotifications = async () => {
    try {
      setLoading(true);
      const response = await getMyNotifications(50, true);
      // API 응답: { status, message, data: [...] }
      // axios response: { data: { status, message, data: [...] } }
      const responseData = response?.data;
      if (responseData?.status === 200 && Array.isArray(responseData?.data)) {
        setNotifications(responseData.data);
      } else {
        setNotifications([]);
      }
    } catch (error) {
      console.error('Failed to load notifications:', error);
      setNotifications([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // 알림 권한 요청
    requestNotificationPermission();

    // 알림 목록 로드
    loadNotifications();

    // 폴링 시작 (새 알림 수신 시 목록 새로고침)
    startNotificationPolling((newNotification) => {
      setNotifications((prev) =>
        Array.isArray(prev) ? [newNotification, ...prev] : [newNotification]
      );
    });

    return () => {
      stopNotificationPolling();
    };
  }, []);

  // 읽지 않은 알림 수
  const unreadCount = useMemo(
    () =>
      Array.isArray(notifications)
        ? notifications.filter((n) => !n.is_checked).length
        : 0,
    [notifications]
  );

  // 시간순 정렬된 알림 목록 (최신순)
  const sortedNotifications = useMemo(() => {
    if (!Array.isArray(notifications)) return [];
    return [...notifications].sort((a, b) => {
      const dateA = new Date(a.notify_at);
      const dateB = new Date(b.notify_at);
      return dateB - dateA; // 최신순 (내림차순)
    });
  }, [notifications]);

  // 알림 확인 처리
  const handleMarkAsRead = async (notificationId) => {
    try {
      await checkNotifications([notificationId]);
      setNotifications((prev) =>
        prev.map((n) =>
          n.notification_id === notificationId ? { ...n, is_checked: true } : n
        )
      );
    } catch (error) {
      console.error('Failed to mark as read:', error);
    }
  };

  // 모두 읽음 처리
  const handleMarkAllAsRead = async () => {
    if (!Array.isArray(notifications)) return;
    const unreadIds = notifications
      .filter((n) => !n.is_checked)
      .map((n) => n.notification_id);
    if (unreadIds.length === 0) return;

    try {
      await checkNotifications(unreadIds);
      setNotifications((prev) =>
        Array.isArray(prev) ? prev.map((n) => ({ ...n, is_checked: true })) : []
      );
    } catch (error) {
      console.error('Failed to mark all as read:', error);
    }
  };

  // 알림 삭제 처리
  const handleDeleteNotification = async (notificationId) => {
    try {
      await deleteNotification(notificationId);
      setNotifications((prev) =>
        prev.filter((n) => n.notification_id !== notificationId)
      );
    } catch (error) {
      console.error('Failed to delete notification:', error);
    }
  };

  // 스와이프 시작
  const handleTouchStart = (e, notificationId) => {
    touchStartX.current = e.touches[0].clientX;
    touchCurrentX.current = e.touches[0].clientX;
    isSwiping.current = true;
    setSwipingId(notificationId);
    setSwipeOffset(0);
  };

  // 스와이프 중
  const handleTouchMove = (e) => {
    if (!isSwiping.current) return;
    touchCurrentX.current = e.touches[0].clientX;
    const diff = touchStartX.current - touchCurrentX.current;
    // 왼쪽으로만 스와이프 (삭제 방향)
    if (diff > 0) {
      setSwipeOffset(Math.min(diff, 120)); // 최대 120px
    } else {
      setSwipeOffset(0);
    }
  };

  // 스와이프 끝
  const handleTouchEnd = (notificationId) => {
    if (!isSwiping.current) return;
    isSwiping.current = false;

    if (swipeOffset >= SWIPE_THRESHOLD) {
      // 삭제 실행
      handleDeleteNotification(notificationId);
    }

    // 리셋
    setSwipingId(null);
    setSwipeOffset(0);
  };

  return (
    <div className="notifications">
      {/* 헤더 - 기존 디자인 유지 */}
      <div className="notifications__header">
        <button className="notifications__back" onClick={() => navigate(-1)}>
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
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
        </div>
        <button
          className="notifications__mark-all"
          onClick={handleMarkAllAsRead}
          disabled={unreadCount === 0}
        >
          모두 읽음
        </button>
      </div>

      {/* 토스 스타일 알림 목록 */}
      <div className="notifications__toss-content">
        {/* 새로운 알림 없음 섹션 */}
        {unreadCount === 0 && (
          <div className="notifications__section-header">
            새로운 알림이 없어요
          </div>
        )}

        {loading ? (
          <div className="notifications__loading">
            <div className="notifications__spinner"></div>
          </div>
        ) : notifications.length === 0 ? (
          <div className="notifications__empty-toss">
            <p>아직 알림이 없어요</p>
          </div>
        ) : (
          <div className="notifications__toss-list">
            {sortedNotifications.map((notification) => (
              <div
                key={notification.notification_id}
                className={`notifications__toss-item-wrapper ${
                  swipingId === notification.notification_id ? 'swiping' : ''
                }`}
              >
                {/* 삭제 배경 */}
                <div className="notifications__delete-bg">
                  <svg
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                  </svg>
                  <span>삭제</span>
                </div>
                {/* 알림 콘텐츠 */}
                <div
                  className={`notifications__toss-item ${
                    notification.is_checked
                      ? 'notifications__toss-item--read'
                      : ''
                  }`}
                  style={{
                    transform:
                      swipingId === notification.notification_id
                        ? `translateX(-${swipeOffset}px)`
                        : 'translateX(0)',
                    transition:
                      swipingId === notification.notification_id
                        ? 'none'
                        : 'transform 0.3s ease',
                  }}
                  onClick={() => handleMarkAsRead(notification.notification_id)}
                  onTouchStart={(e) =>
                    handleTouchStart(e, notification.notification_id)
                  }
                  onTouchMove={handleTouchMove}
                  onTouchEnd={() =>
                    handleTouchEnd(notification.notification_id)
                  }
                >
                  <div className="notifications__toss-icon">
                    <svg
                      width="20"
                      height="20"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                      <path d="M13.73 21a2 2 0 0 1-3.46 0" />
                    </svg>
                  </div>
                  <div className="notifications__toss-content-wrap">
                    <div className="notifications__toss-header">
                      <span className="notifications__toss-source">
                        일정 알림
                      </span>
                      <span className="notifications__toss-time">
                        {formatNotificationTime(notification.notify_at)}
                      </span>
                    </div>
                    <p className="notifications__toss-message">
                      {notification.message}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Notifications;
