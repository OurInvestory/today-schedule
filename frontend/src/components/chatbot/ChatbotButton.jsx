import React from 'react';
import './ChatbotButton.css';

const ChatbotButton = ({ onClick }) => {
  return (
    <button 
      type="button"
      className="chatbot-button" 
      onClick={onClick}
      aria-label="챗봇 열기"
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
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
    </button>
  );
};

export default ChatbotButton;