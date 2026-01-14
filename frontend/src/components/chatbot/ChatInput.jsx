import React, { useState } from 'react';
import './ChatInput.css';

const ChatInput = ({
  onSend,
  disabled = false,
  placeholder = '메시지를 입력하세요...',
  onFileUpload,
  hasFiles = false, // 파일이 선택되어 있는지 여부
}) => {
  const [value, setValue] = useState('');

  // 텍스트가 있거나 파일이 있으면 전송 가능
  const canSend = value.trim() || hasFiles;

  const handleSubmit = (e) => {
    e.preventDefault();
    // 텍스트가 있거나, 파일이 있으면 전송 가능
    if (canSend && !disabled) {
      onSend(value.trim());
      setValue('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form className="chat-input" onSubmit={handleSubmit}>
      {onFileUpload && (
        <button
          type="button"
          className="chat-input__file-btn"
          onClick={onFileUpload}
          disabled={disabled}
          aria-label="파일 첨부"
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
            <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
          </svg>
        </button>
      )}
      <textarea
        className="chat-input__textarea"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={hasFiles ? '시간표 사진에 있는 강의 추가해줘' : placeholder}
        disabled={disabled}
        rows={1}
      />
      <button
        type="submit"
        className="chat-input__button"
        disabled={disabled || !canSend}
        aria-label="전송"
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
          <line x1="2" y1="10" x2="18" y2="10" />
          <polyline points="12 4 18 10 12 16" />
        </svg>
      </button>
    </form>
  );
};

export default ChatInput;
