import React from 'react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import './ChatbotWindow.css';

const ChatbotWindow = ({ isOpen, onClose, messages, onSendMessage, loading, messagesEndRef }) => {
  if (!isOpen) return null;

  return (
    <div className="chatbot-window">
      <div className="chatbot-window__header">
        <h3 className="chatbot-window__title">AI 도우미</h3>
        <button
          type="button"
          className="chatbot-window__close"
          onClick={onClose}
          aria-label="닫기"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 20 20"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="15" y1="5" x2="5" y2="15" />
            <line x1="5" y1="5" x2="15" y2="15" />
          </svg>
        </button>
      </div>

      <div className="chatbot-window__messages">
        {messages.length === 0 ? (
          <div className="chatbot-window__empty">
            <svg
              width="48"
              height="48"
              viewBox="0 0 48 48"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M40 24a16 16 0 0 1-16 16H12l-8 8V8a4 4 0 0 1 4-4h28a4 4 0 0 1 4 4z" />
              <circle cx="16" cy="20" r="2" fill="currentColor" />
              <circle cx="24" cy="20" r="2" fill="currentColor" />
              <circle cx="32" cy="20" r="2" fill="currentColor" />
            </svg>
            <p>무엇을 도와드릴까요?</p>
            <div className="chatbot-window__quick-actions">
              <button type="button" onClick={() => onSendMessage('오늘 할 일 보여줘')}>
                오늘 할 일
              </button>
              <button type="button" onClick={() => onSendMessage('새로운 일정 추가해줘')}>
                일정 추가
              </button>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            {loading && (
              <div className="chatbot-window__typing">
                <span></span>
                <span></span>
                <span></span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      <ChatInput onSend={onSendMessage} disabled={loading} />
    </div>
  );
};

export default ChatbotWindow;