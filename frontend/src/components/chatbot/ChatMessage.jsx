import React from 'react';
import { formatDate } from '../../utils/dateUtils';
import './ChatMessage.css';

const ChatMessage = ({ message, onConfirm, onCancel }) => {
  const isUser = message.role === 'user';
  const isError = message.isError;
  const hasAction = message.hasAction || message.content?.includes('일정에 반영');

  const messageClass = [
    'chat-message',
    isUser ? 'chat-message--user' : 'chat-message--assistant',
    isError && 'chat-message--error',
  ]
    .filter(Boolean)
    .join(' ');

  const handleConfirm = () => {
    if (onConfirm) {
      onConfirm(message.id, message.data);
    }
  };

  const handleCancel = () => {
    if (onCancel) {
      onCancel(message.id);
    }
  };

  return (
    <div className={messageClass}>
      <div className="chat-message__avatar">
        {isUser ? (
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10 2a4 4 0 100 8 4 4 0 000-8zM4 14a6 6 0 0112 0v2H4v-2z" />
          </svg>
        ) : (
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path d="M2 5a2 2 0 012-2h12a2 2 0 012 2v10a2 2 0 01-2 2H4a2 2 0 01-2-2V5zm3.5 1a1.5 1.5 0 100 3 1.5 1.5 0 000-3zm9 0a1.5 1.5 0 100 3 1.5 1.5 0 000-3zM5 11a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1z" />
          </svg>
        )}
      </div>
      <div className="chat-message__content">
        <div className="chat-message__bubble">
          {message.content}
          
          {/* 인터랙티브 확인/취소 버튼 */}
          {!isUser && hasAction && !message.actionCompleted && (
            <div className="chat-message__actions">
              <button 
                type="button" 
                className="chat-message__action-btn chat-message__action-btn--confirm"
                onClick={handleConfirm}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                확인
              </button>
              <button 
                type="button" 
                className="chat-message__action-btn chat-message__action-btn--cancel"
                onClick={handleCancel}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
                취소
              </button>
            </div>
          )}
          
          {/* 액션 완료 표시 */}
          {message.actionCompleted && (
            <div className="chat-message__action-status">
              {message.actionCompleted === 'confirmed' ? (
                <span className="chat-message__action-status--confirmed">✓ 반영되었습니다</span>
              ) : (
                <span className="chat-message__action-status--cancelled">✗ 취소되었습니다</span>
              )}
            </div>
          )}
        </div>
        <span className="chat-message__time">
          {formatDate(message.timestamp, 'HH:mm')}
        </span>
      </div>
    </div>
  );
};

export default ChatMessage;
