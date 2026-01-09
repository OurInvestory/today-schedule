import React from 'react';
import './Loading.css';

const Loading = ({ size = 'md', fullscreen = false, text = '' }) => {
  if (fullscreen) {
    return (
      <div className="loading-fullscreen">
        <div className="loading-content">
          <div className={`loading-spinner loading-spinner--${size}`}>
            <svg viewBox="0 0 50 50">
              <circle
                cx="25"
                cy="25"
                r="20"
                fill="none"
                stroke="currentColor"
                strokeWidth="4"
                strokeLinecap="round"
                strokeDasharray="80 50"
              />
            </svg>
          </div>
          {text && <p className="loading-text">{text}</p>}
        </div>
      </div>
    );
  }

  return (
    <div className="loading-container">
      <div className={`loading-spinner loading-spinner--${size}`}>
        <svg viewBox="0 0 50 50">
          <circle
            cx="25"
            cy="25"
            r="20"
            fill="none"
            stroke="currentColor"
            strokeWidth="4"
            strokeLinecap="round"
            strokeDasharray="80 50"
          />
        </svg>
      </div>
      {text && <p className="loading-text">{text}</p>}
    </div>
  );
};

export default Loading;