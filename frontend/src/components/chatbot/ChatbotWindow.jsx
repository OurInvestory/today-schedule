import React, { useRef, useState } from 'react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import './ChatbotWindow.css';

// 추천 질문 목록
const suggestedQuestions = [
  { id: 1, text: '오늘 할 일 보여줘', icon: '📋' },
  { id: 2, text: '이번 주 일정 정리해줘', icon: '📅' },
  { id: 3, text: '우선순위 높은 일정 알려줘', icon: '🔥' },
  { id: 4, text: '새로운 일정 추가해줘', icon: '➕' },
  { id: 5, text: '마감 임박한 할 일은?', icon: '⏰' },
];

const ChatbotWindow = ({ 
  isOpen, 
  onClose, 
  messages, 
  onSendMessage, 
  loading, 
  messagesEndRef,
  onConfirmAction,
  onCancelAction,
  onClearHistory,
}) => {
  const fileInputRef = useRef(null);
  const suggestionsRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const [startX, setStartX] = useState(0);
  const [scrollLeft, setScrollLeft] = useState(0);

  if (!isOpen) return null;

  // 드래그 스크롤 핸들러
  const handleMouseDown = (e) => {
    if (!suggestionsRef.current) return;
    setIsDragging(true);
    setStartX(e.pageX - suggestionsRef.current.offsetLeft);
    setScrollLeft(suggestionsRef.current.scrollLeft);
    suggestionsRef.current.style.cursor = 'grabbing';
  };

  const handleMouseMove = (e) => {
    if (!isDragging || !suggestionsRef.current) return;
    e.preventDefault();
    const x = e.pageX - suggestionsRef.current.offsetLeft;
    const walk = (x - startX) * 1.5;
    suggestionsRef.current.scrollLeft = scrollLeft - walk;
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    if (suggestionsRef.current) {
      suggestionsRef.current.style.cursor = 'grab';
    }
  };

  const handleMouseLeave = () => {
    if (isDragging) {
      setIsDragging(false);
      if (suggestionsRef.current) {
        suggestionsRef.current.style.cursor = 'grab';
      }
    }
  };

  const handleFileUpload = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      // 파일 업로드 처리 (추후 구현)
      console.log('File selected:', file.name);
      onSendMessage(`[파일 첨부: ${file.name}]`);
    }
    e.target.value = '';
  };

  const handleSuggestedQuestion = (question) => {
    onSendMessage(question);
  };

  const handleEndConversation = () => {
    if (onClearHistory) {
      onClearHistory();
    }
  };

  return (
    <div className="chatbot-window">
      <div className="chatbot-window__header">
        <div className="chatbot-window__header-left">
          <button
            type="button"
            className="chatbot-window__back"
            onClick={onClose}
            aria-label="닫기"
          >
            <svg
              width="20"
              height="20"
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
          <h3 className="chatbot-window__title">AI 도우미</h3>
        </div>
        <button
          type="button"
          className="chatbot-window__end-btn"
          onClick={handleEndConversation}
        >
          대화 종료
        </button>
      </div>

      <div className="chatbot-window__messages">
        {messages.map((message) => (
          <ChatMessage 
            key={message.id} 
            message={message}
            onConfirm={onConfirmAction}
            onCancel={onCancelAction}
          />
        ))}
        {loading && (
          <div className="chatbot-window__typing">
            <span></span>
            <span></span>
            <span></span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* 추천 질문 카드 */}
      <div className="chatbot-window__suggestions">
        <div 
          className="chatbot-window__suggestions-scroll"
          ref={suggestionsRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseLeave}
        >
          {suggestedQuestions.map((q) => (
            <button
              key={q.id}
              type="button"
              className="chatbot-window__suggestion-card"
              onClick={() => !isDragging && handleSuggestedQuestion(q.text)}
            >
              <span className="chatbot-window__suggestion-icon">{q.icon}</span>
              <span className="chatbot-window__suggestion-text">{q.text}</span>
            </button>
          ))}
        </div>
      </div>

      <ChatInput 
        onSend={onSendMessage} 
        disabled={loading}
        onFileUpload={handleFileUpload}
      />
      
      {/* 숨겨진 파일 입력 */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        style={{ display: 'none' }}
        accept="image/*,.pdf,.doc,.docx,.txt"
      />
    </div>
  );
};

export default ChatbotWindow;