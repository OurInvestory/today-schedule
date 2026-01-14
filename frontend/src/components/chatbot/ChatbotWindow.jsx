import React, { useRef, useState, useEffect } from 'react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import { getRandomLoadingMessage } from '../../hooks/useChatbot';
import './ChatbotWindow.css';

// 추천 질문 목록 (5개)
const suggestedQuestions = [
  { id: 1, text: '내일 3시에 회의, 5시에 미팅 추가해줘', icon: '📅' },
  { id: 2, text: '오늘 6시까지 보고서 작성 추가해줘', icon: '✅' },
  { id: 3, text: '회의 10분 전에 알림 예약해줘', icon: '🔔' },
  { id: 4, text: '시간표 사진에 있는 강의 추가해줘', icon: '📸' },
  { id: 5, text: '우선순위 높은 일정 추천해줘', icon: '🎯' },
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
  onRetry,
  canRetry,
}) => {
  const fileInputRef = useRef(null);
  const suggestionsRef = useRef(null);
  const dropZoneRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const [startX, setStartX] = useState(0);
  const [scrollLeft, setScrollLeft] = useState(0);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isFileDragging, setIsFileDragging] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('');
  
  // 로딩 상태 변경 시 랜덤 메시지 설정 (2초마다 변경)
  useEffect(() => {
    if (loading) {
      setLoadingMessage(getRandomLoadingMessage());
      
      // 2초마다 메시지 변경
      const interval = setInterval(() => {
        setLoadingMessage(getRandomLoadingMessage());
      }, 2000);
      
      return () => clearInterval(interval);
    }
  }, [loading]);

  // 컴포넌트 언마운트 시 미리보기 URL 정리 (Hook은 조건부 return 전에 호출되어야 함)
  useEffect(() => {
    return () => {
      selectedFiles.forEach(f => {
        if (f.preview) {
          URL.revokeObjectURL(f.preview);
        }
      });
    };
  }, [selectedFiles]);

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
    const files = e.target.files;
    if (files && files.length > 0) {
      processFiles(Array.from(files));
    }
    e.target.value = '';
  };

  const processFiles = (files) => {
    const processedFiles = files.map(file => {
      const fileData = {
        name: file.name,
        type: file.type,
        size: file.size,
        file: file,
      };
      
      // 이미지 파일인 경우 미리보기 URL 생성
      if (file.type.startsWith('image/')) {
        fileData.preview = URL.createObjectURL(file);
      }
      
      return fileData;
    });
    
    setSelectedFiles(prev => [...prev, ...processedFiles]);
    console.log('Files processed:', processedFiles.map(f => f.name));
  };

  // 드래그 앤 드롭 핸들러
  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsFileDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.target === dropZoneRef.current) {
      setIsFileDragging(false);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsFileDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      processFiles(files);
    }
  };

  const handleSendWithFiles = (text) => {
    if (selectedFiles.length > 0) {
      // 파일 객체만 추출
      const fileObjects = selectedFiles.map(f => f.file);
      onSendMessage(text, null, fileObjects);
      
      // 미리보기 URL 정리
      selectedFiles.forEach(f => {
        if (f.preview) {
          URL.revokeObjectURL(f.preview);
        }
      });
      
      setSelectedFiles([]);
    } else {
      onSendMessage(text);
    }
  };

  const handleRemoveFile = (index) => {
    const file = selectedFiles[index];
    if (file.preview) {
      URL.revokeObjectURL(file.preview);
    }
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleSuggestedQuestion = (question) => {
    // "시간표 사진에 있는 강의 추가해줘" 클릭 시 파일 선택 열기
    if (question.includes('시간표 사진')) {
      handleFileUpload();
      return;
    }
    onSendMessage(question);
  };

  const handleEndConversation = () => {
    if (onClearHistory) {
      onClearHistory();
    }
  };

  const handleRetry = () => {
    if (onRetry) {
      onRetry();
    }
  };

  return (
    <div 
      className={`chatbot-window ${isFileDragging ? 'chatbot-window--dragging' : ''}`}
      ref={dropZoneRef}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      {isFileDragging && (
        <div className="chatbot-window__drop-overlay">
          <div className="chatbot-window__drop-message">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            <p>이미지나 파일을 여기에 드롭하세요</p>
            <small>시간표 이미지를 분석하여 일정을 자동으로 추가할 수 있습니다</small>
          </div>
        </div>
      )}
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
        {messages.map((message, index) => (
          <ChatMessage 
            key={message.id} 
            message={message}
            onConfirm={onConfirmAction}
            onCancel={onCancelAction}
            onConfirmSingle={(messageId, action, actionIndex) => 
              onConfirmAction(messageId, action, null, actionIndex)
            }
            onChoiceSelect={(choice) => onSendMessage(choice)}
            onRetry={message.isError && index === messages.length - 1 && canRetry ? handleRetry : undefined}
          />
        ))}
        {loading && (
          <div className="chatbot-window__loading">
            <div className="chatbot-window__loading-message">
              {loadingMessage}
            </div>
            <div className="chatbot-window__typing">
              <span></span>
              <span></span>
              <span></span>
            </div>
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

      {/* 선택된 파일 미리보기 */}
      {selectedFiles.length > 0 && (
        <div className="chatbot-window__selected-files">
          {selectedFiles.map((file, index) => (
            <div key={index} className="chatbot-window__file-preview">
              {file.preview ? (
                <div className="chatbot-window__image-thumb">
                  <img src={file.preview} alt={file.name} />
                </div>
              ) : (
                <div className="chatbot-window__file-icon">
                  📄
                </div>
              )}
              <span className="chatbot-window__file-name">
                {file.name}
              </span>
              <button
                type="button"
                className="chatbot-window__file-remove"
                onClick={() => handleRemoveFile(index)}
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}

      <ChatInput 
        onSend={handleSendWithFiles} 
        disabled={loading}
        onFileUpload={handleFileUpload}
        hasFiles={selectedFiles.length > 0}
      />
      
      {/* 숨겨진 파일 입력 */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        style={{ display: 'none' }}
        accept="image/*,.pdf,.doc,.docx,.txt"
        multiple
      />
    </div>
  );
};

export default ChatbotWindow;