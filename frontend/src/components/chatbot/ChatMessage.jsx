import React from 'react';
import { formatDate } from '../../utils/dateUtils';
import { CATEGORY_LABELS } from '../../utils/constants';
import './ChatMessage.css';

const ChatMessage = ({ message, onConfirm, onCancel }) => {
  const isUser = message.role === 'user';
  const isError = message.isError;
  const hasActions = message.actions && message.actions.length > 0;

  const messageClass = [
    'chat-message',
    isUser ? 'chat-message--user' : 'chat-message--assistant',
    isError && 'chat-message--error',
  ]
    .filter(Boolean)
    .join(' ');

  const handleConfirmAction = (action) => {
    if (onConfirm) {
      onConfirm(message.id, action);
    }
  };

  const handleCancel = () => {
    if (onCancel) {
      onCancel(message.id);
    }
  };

  // 액션 payload를 사람이 읽을 수 있는 형식으로 변환
  const formatActionPayload = (action) => {
    const { payload, target } = action;
    if (!payload) return '';

    const parts = [];

    if (target === 'SCHEDULE') {
      if (payload.title) parts.push(`제목: ${payload.title}`);
      if (payload.start_time && payload.end_time) {
        parts.push(
          `시간: ${formatDate(
            payload.start_time,
            'M월 D일 HH:mm'
          )} ~ ${formatDate(payload.end_time, 'HH:mm')}`
        );
      }
      if (payload.category)
        parts.push(
          `카테고리: ${CATEGORY_LABELS[payload.category] || payload.category}`
        );
      if (payload.location) parts.push(`위치: ${payload.location}`);
    } else if (target === 'SUB_TASK') {
      if (payload.title) parts.push(`할 일: ${payload.title}`);
      if (payload.due_date)
        parts.push(`마감: ${formatDate(payload.due_date, 'M월 D일 HH:mm')}`);
      if (payload.priority) parts.push(`우선순위: ${payload.priority}`);
      if (payload.category)
        parts.push(
          `카테고리: ${CATEGORY_LABELS[payload.category] || payload.category}`
        );
    } else if (target === 'LECTURES') {
      if (Array.isArray(payload)) {
        return action.description || `${payload.length}개의 강의`;
      }
    }

    return parts.join(', ');
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

          {/* 첨부된 파일 표시 (사용자 메시지) */}
          {isUser && message.files && message.files.length > 0 && (
            <div className="chat-message__attached-files">
              {message.files.map((file, index) => (
                <div key={index} className="chat-message__attached-file">
                  {file.type.startsWith('image/') ? (
                    <div className="chat-message__image-preview">
                      {file.preview ? (
                        <img src={file.preview} alt={file.name} />
                      ) : (
                        <span>🖼️ {file.name}</span>
                      )}
                    </div>
                  ) : (
                    <div className="chat-message__file-info">
                      <span>📄</span>
                      <span>{file.name}</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* AI 이미지 분석 결과 */}
          {!isUser && message.imageAnalysis && (
            <div className="chat-message__image-analysis">
              <div className="chat-message__analysis-header">
                📊 이미지 분석 결과
              </div>
              <div className="chat-message__analysis-content">
                {message.imageAnalysis.schedules &&
                message.imageAnalysis.schedules.length > 0 ? (
                  <ul className="chat-message__schedule-list">
                    {message.imageAnalysis.schedules.map((schedule, idx) => (
                      <li key={idx}>
                        {schedule.title} - {schedule.time}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p>{message.imageAnalysis.message}</p>
                )}
              </div>
            </div>
          )}

          {/* AI 추론 이유 표시 */}
          {!isUser && message.reasoning && (
            <div className="chat-message__reasoning">
              <div className="chat-message__reasoning-icon">💡</div>
              <div className="chat-message__reasoning-text">
                {message.reasoning}
              </div>
            </div>
          )}

          {/* 파싱된 액션 표시 */}
          {!isUser && hasActions && !message.actionCompleted && (
            <div className="chat-message__parsed-actions">
              {message.actions.map((action, index) => (
                <div key={index} className="chat-message__action-card">
                  <div className="chat-message__action-header">
                    <span className="chat-message__action-type">
                      {action.target === 'SCHEDULE'
                        ? '📅 일정'
                        : action.target === 'LECTURES'
                        ? '📚 시간표'
                        : '✓ 할 일'}
                    </span>
                    <span className="chat-message__action-op">
                      {action.op === 'CREATE'
                        ? '추가'
                        : action.op === 'UPDATE'
                        ? '수정'
                        : '삭제'}
                    </span>
                  </div>
                  <div className="chat-message__action-details">
                    {formatActionPayload(action)}
                  </div>
                  {/* LECTURES인 경우 강의 목록 표시 */}
                  {action.target === 'LECTURES' &&
                    Array.isArray(action.payload) && (
                      <div className="chat-message__lectures-list">
                        <ul>
                          {action.payload.map((lecture, idx) => (
                            <li key={idx}>
                              {lecture.title}
                              <span className="chat-message__lecture-time">
                                {lecture.startTime} - {lecture.endTime}
                              </span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  <div className="chat-message__action-buttons">
                    <button
                      type="button"
                      className="chat-message__action-btn chat-message__action-btn--confirm"
                      onClick={() => handleConfirmAction(action)}
                      disabled={message.actionLoading}
                    >
                      {message.actionLoading ? '처리중...' : '✓ 확인'}
                    </button>
                    <button
                      type="button"
                      className="chat-message__action-btn chat-message__action-btn--cancel"
                      onClick={handleCancel}
                      disabled={message.actionLoading}
                    >
                      ✕ 취소
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* 누락된 필드 표시 */}
          {!isUser &&
            message.missingFields &&
            message.missingFields.length > 0 && (
              <div className="chat-message__missing-fields">
                <div className="chat-message__missing-fields-title">
                  추가 정보가 필요해요:
                </div>
                <ul className="chat-message__missing-fields-list">
                  {message.missingFields.map((field, index) => (
                    <li key={index}>
                      {typeof field === 'string'
                        ? field
                        : field.question || field.field || '정보 필요'}
                    </li>
                  ))}
                </ul>
              </div>
            )}

          {/* 액션 완료 표시 */}
          {message.actionCompleted && (
            <div className="chat-message__action-status">
              {message.actionResult?.success ? (
                <span className="chat-message__action-status--confirmed">
                  ✓ {message.actionResult.message || '반영되었습니다'}
                </span>
              ) : (
                <span className="chat-message__action-status--error">
                  ✗{' '}
                  {message.actionResult?.message ||
                    '처리 중 오류가 발생했습니다'}
                </span>
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
