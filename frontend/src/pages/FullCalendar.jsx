import React from 'react';
import { useNavigate } from 'react-router-dom';
import Calendar from '../components/calendar/Calendar';
import './FullCalendar.css';

const FullCalendar = () => {
  const navigate = useNavigate();

  const handleBack = () => {
    navigate(-1);
  };

  return (
    <div className="full-calendar-page">
      <header className="full-calendar-page__header">
        <button 
          className="full-calendar-page__back-btn"
          onClick={handleBack}
          aria-label="뒤로 가기"
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
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>
        <h1 className="full-calendar-page__title">이번 달 달력</h1>
        <div className="full-calendar-page__spacer" />
      </header>
      
      <main className="full-calendar-page__content">
        <Calendar isFullMode={true} />
      </main>
    </div>
  );
};

export default FullCalendar;
