import React from 'react';
import { Link } from 'react-router-dom';
import './Header.css';

const Header = ({ user, onNotificationClick }) => {
  return (
    <header className="header">
      <div className="header__container">
        <Link to="/" className="header__logo">
          <h1 className="header__title">오늘의 일정</h1>
        </Link>

        <div className="header__actions">
          <button
            className="header__notification-btn"
            onClick={onNotificationClick}
            aria-label="알림"
          >
            <svg
              width="24"
              height="24"
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
          </button>

          {user ? (
            <div className="header__user">
              <div className="header__user-avatar">
                {user.name ? user.name[0] : 'U'}
              </div>
              <span className="header__user-name">{user.name || '사용자'}</span>
            </div>
          ) : (
            <button className="header__login-btn">로그인</button>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;