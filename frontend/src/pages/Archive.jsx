import React from 'react';
import './Archive.css';

const Archive = () => {
  return (
    <div className="archive">
      <div className="archive__container">
        <div className="archive__header">
          <h1 className="archive__title">경험 아카이브</h1>
          <p className="archive__subtitle">
            완료한 활동들을 정리하고 관리할 수 있습니다
          </p>
        </div>

        <div className="archive__content">
          <div className="archive__empty">
            <svg
              width="64"
              height="64"
              viewBox="0 0 64 64"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <rect x="8" y="16" width="48" height="40" rx="4" />
              <polyline points="32 8 24 16 40 16 32 8" />
              <line x1="24" y1="28" x2="40" y2="28" />
            </svg>
            <p>아카이브 기능은 2순위로 향후 구현 예정입니다.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Archive;