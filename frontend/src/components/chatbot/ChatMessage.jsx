import React from 'react';
import { formatDate } from '../../utils/dateUtils';
import { CATEGORY_LABELS } from '../../utils/constants';
import './ChatMessage.css';

const ChatMessage = ({ message, onConfirm, onCancel, onRetry, onConfirmSingle, onChoiceSelect }) => {
  const isUser = message.role === 'user';
  const isError = message.isError;
  const hasActions = message.actions && message.actions.length > 0;
  
  // 개별 액션 완료 상태 추적
  const completedActions = message.completedActions || {};
  const pendingActions = message.actions?.filter((_, idx) => !completedActions[idx]) || [];
  const hasAllCompleted = message.actions?.length > 0 && pendingActions.length === 0;

  const messageClass = [
    'chat-message',
    isUser ? 'chat-message--user' : 'chat-message--assistant',
    isError && 'chat-message--error',
  ]
    .filter(Boolean)
    .join(' ');

  const handleConfirmAction = (action, index) => {
    if (onConfirmSingle) {
      onConfirmSingle(message.id, action, index);
    } else if (onConfirm) {
      onConfirm(message.id, action);
    }
  };

  const handleCancelAction = (index) => {
    if (onCancel) {
      onCancel(message.id, index);
    }
  };

  const handleCancelAll = () => {
    if (onCancel) {
      onCancel(message.id, 'all');
    }
  };

  // 액션 payload를 사람이 읽을 수 있는 형식으로 변환
  const formatActionPayload = (action) => {
    const { payload, target } = action;
    if (!payload) return '';

    const parts = [];
    
    // target이 있으면 사용, 없으면 payload.type으로 판단
    const actionTarget = target || (payload.type === 'TASK' ? 'SUB_TASK' : 'SCHEDULE');
    
    // LECTURES (시간표 강의 일괄 추가)
    if (actionTarget === 'LECTURES') {
      const lectures = Array.isArray(payload) ? payload : [payload];
      const titles = lectures.slice(0, 3).map(l => l.title).join(', ');
      const moreText = lectures.length > 3 ? ` 외 ${lectures.length - 3}개` : '';
      return `${titles}${moreText}`;
    }
    
    if (actionTarget === 'SCHEDULE' || payload.type === 'EVENT' || payload.type === 'TASK') {
      if (payload.title) parts.push(`제목: ${payload.title}`);
      // start_at/end_at 또는 start_time/end_time 처리
      const startTime = payload.start_at || payload.start_time;
      const endTime = payload.end_at || payload.end_time;
      if (startTime && endTime) {
        parts.push(`시간: ${formatDate(startTime, 'M월 D일 HH:mm')} ~ ${formatDate(endTime, 'HH:mm')}`);
      } else if (endTime) {
        parts.push(`마감: ${formatDate(endTime, 'M월 D일 HH:mm')}`);
      }
      if (payload.category) parts.push(`카테고리: ${CATEGORY_LABELS[payload.category] || payload.category}`);
      if (payload.location) parts.push(`위치: ${payload.location}`);
      if (payload.importance_score) parts.push(`중요도: ${payload.importance_score}/10`);
    } else if (actionTarget === 'SUB_TASK') {
      if (payload.title) parts.push(`할 일: ${payload.title}`);
      if (payload.due_date) parts.push(`마감: ${formatDate(payload.due_date, 'M월 D일 HH:mm')}`);
      if (payload.priority) parts.push(`우선순위: ${payload.priority}`);
      if (payload.category) parts.push(`카테고리: ${CATEGORY_LABELS[payload.category] || payload.category}`);
    }

    return parts.join(', ');
  };

  // 액션 타입 아이콘/라벨 결정
  const getActionTypeLabel = (action) => {
    const target = action.target || (action.payload?.type === 'TASK' ? 'SUB_TASK' : 'SCHEDULE');
    const payloadType = action.payload?.type;
    
    if (target === 'LECTURES') {
      const count = Array.isArray(action.payload) ? action.payload.length : 1;
      return { icon: '📚', label: `강의 ${count}개` };
    }
    if (target === 'SUB_TASK' || payloadType === 'TASK') {
      return { icon: '✓', label: '할 일' };
    }
    return { icon: '📅', label: '일정' };
  };

  // 마크다운 스타일 볼드 텍스트 처리 (**text** -> <strong>text</strong>)
  const formatMessageContent = (content) => {
    if (!content) return null;
    
    // **text** 패턴을 찾아서 <strong>으로 변환
    const parts = content.split(/(\*\*[^*]+\*\*)/g);
    
    return parts.map((part, index) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={index}>{part.slice(2, -2)}</strong>;
      }
      return part;
    });
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
          {formatMessageContent(message.content)}
          
          {/* 에러 메시지일 때 재시도 버튼 표시 */}
          {isError && onRetry && (
            <div className="chat-message__error-actions">
              <button 
                type="button" 
                className="chat-message__retry-btn"
                onClick={onRetry}
              >
                🔄 다시 시도
              </button>
            </div>
          )}
          
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
          
          {/* AI 이미지 분석 결과 - 일정 목록 미리보기 */}
          {!isUser && message.imageAnalysis && message.actions && message.actions.length > 0 && !message.actionCompleted && (
            <div className="chat-message__image-analysis">
              <div className="chat-message__analysis-header">
                📷 시간표에서 {message.actions.length}개의 일정을 찾았어요!
              </div>
              <div className="chat-message__analysis-content">
                <ul className="chat-message__schedule-list">
                  {message.actions.slice(0, 5).map((action, idx) => {
                    const startTime = action.payload?.start_at || action.payload?.start_time;
                    const endTime = action.payload?.end_at || action.payload?.end_time;
                    return (
                    <li key={idx}>
                      <strong>{action.payload?.title}</strong>
                      {(startTime || endTime) && (
                        <span className="chat-message__schedule-time">
                          {startTime ? (
                            <>{' - '}{formatDate(startTime, 'M/D HH:mm')}
                            {endTime && ` ~ ${formatDate(endTime, 'HH:mm')}`}</>
                          ) : (
                            <>{' - '}마감: {formatDate(endTime, 'M/D HH:mm')}</>
                          )}
                        </span>
                      )}
                    </li>
                  );})}
                  {message.actions.length > 5 && (
                    <li className="chat-message__more-items">...외 {message.actions.length - 5}개</li>
                  )}
                </ul>
              </div>
              <div className="chat-message__bulk-actions">
                <button 
                  type="button" 
                  className="chat-message__action-btn chat-message__action-btn--confirm-all"
                  onClick={() => {
                    // 모든 일정 한 번에 추가
                    message.actions.forEach((action, idx) => handleConfirmAction(action, idx));
                  }}
                  disabled={message.actionLoading}
                >
                  {message.actionLoading ? '추가 중...' : `✓ ${message.actions.length}개 일정 모두 추가`}
                </button>
                <button 
                  type="button" 
                  className="chat-message__action-btn chat-message__action-btn--cancel"
                  onClick={handleCancelAll}
                  disabled={message.actionLoading}
                >
                  ✕ 취소
                </button>
              </div>
            </div>
          )}
          
          {/* AI 추론 이유 표시 */}
          {!isUser && message.reasoning && (
            <div className="chat-message__reasoning">
              <div className="chat-message__reasoning-icon">💡</div>
              <div className="chat-message__reasoning-text">{message.reasoning}</div>
            </div>
          )}
          
          {/* 알림 예약 요청 표시 */}
          {!isUser && message.parsedResult?.intent === 'NOTIFICATION_REQUEST' && !message.actionCompleted && (
            <div className="chat-message__parsed-actions">
              <div className="chat-message__action-card">
                <div className="chat-message__action-header">
                  <span className="chat-message__action-type">🔔 알림 예약</span>
                </div>
                <div className="chat-message__action-details">
                  {message.parsedResult.preserved_info?.target_title && 
                    `대상: ${message.parsedResult.preserved_info.target_title}`}
                  {message.parsedResult.preserved_info?.minutes_before && 
                    `, ${message.parsedResult.preserved_info.minutes_before}분 전`}
                  {message.parsedResult.preserved_info?.reminder_time && 
                    `, 예약 시간: ${new Date(message.parsedResult.preserved_info.reminder_time).toLocaleString('ko-KR')}`}
                </div>
                <div className="chat-message__action-buttons">
                  <button 
                    type="button" 
                    className="chat-message__action-btn chat-message__action-btn--confirm"
                    onClick={() => onConfirm && onConfirm(message.id, null, message.parsedResult)}
                    disabled={message.actionLoading}
                  >
                    {message.actionLoading ? '처리중...' : '✓ 예약'}
                  </button>
                  <button 
                    type="button" 
                    className="chat-message__action-btn chat-message__action-btn--cancel"
                    onClick={handleCancelAll}
                    disabled={message.actionLoading}
                  >
                    ✕ 취소
                  </button>
                </div>
              </div>
            </div>
          )}
          
          {/* 파싱된 액션 표시 (이미지 분석이 아닌 일반 채팅의 경우) */}
          {!isUser && hasActions && !hasAllCompleted && !message.imageAnalysis && (
            <div className="chat-message__parsed-actions">
              {message.actions.map((action, index) => {
                const typeInfo = getActionTypeLabel(action);
                const isCompleted = completedActions[index];
                const isLoading = message.loadingActions?.[index];
                
                // 이미 완료된 액션은 완료 상태로 표시
                if (isCompleted) {
                  return (
                    <div key={index} className="chat-message__action-card chat-message__action-card--completed">
                      <div className="chat-message__action-header">
                        <span className="chat-message__action-type">
                          {typeInfo.icon} {typeInfo.label}
                        </span>
                        <span className="chat-message__action-status-badge chat-message__action-status-badge--success">
                          {isCompleted === 'cancelled' ? '취소됨' : '✅ 완료'}
                        </span>
                      </div>
                      <div className="chat-message__action-details">
                        {action.payload?.title}
                      </div>
                    </div>
                  );
                }
                
                return (
                <div key={index} className="chat-message__action-card">
                  <div className="chat-message__action-header">
                    <span className="chat-message__action-type">
                      {typeInfo.icon} {typeInfo.label}
                    </span>
                    <span className="chat-message__action-op">
                      {action.op === 'CREATE' ? '추가' : action.op === 'UPDATE' ? '수정' : '삭제'}
                    </span>
                  </div>
                  <div className="chat-message__action-details">
                    {formatActionPayload(action)}
                  </div>
                  <div className="chat-message__action-buttons">
                    <button 
                      type="button" 
                      className="chat-message__action-btn chat-message__action-btn--confirm"
                      onClick={() => handleConfirmAction(action, index)}
                      disabled={isLoading}
                    >
                      {isLoading ? '처리중...' : '✓ 확인'}
                    </button>
                    <button 
                      type="button" 
                      className="chat-message__action-btn chat-message__action-btn--cancel"
                      onClick={() => handleCancelAction(index)}
                      disabled={isLoading}
                    >
                      ✕ 취소
                    </button>
                  </div>
                </div>
              );})}
              
              {/* 여러 개일 때 전체 취소 버튼 */}
              {pendingActions.length > 1 && (
                <div className="chat-message__bulk-actions">
                  <button 
                    type="button" 
                    className="chat-message__action-btn chat-message__action-btn--cancel-all"
                    onClick={handleCancelAll}
                  >
                    ✕ 모두 취소
                  </button>
                </div>
              )}
            </div>
          )}
          
          {/* 누락된 필드 표시 */}
          {!isUser && message.missingFields && message.missingFields.length > 0 && (
            <div className="chat-message__missing-fields">
              <div className="chat-message__missing-fields-title">추가 정보가 필요해요:</div>
              <ul className="chat-message__missing-fields-list">
                {message.missingFields.map((field, index) => {
                  const fieldData = typeof field === 'string' ? { field, question: field } : field;
                  const choices = fieldData.choices || [];
                  
                  return (
                    <li key={index}>
                      {fieldData.question || fieldData.field || '정보 필요'}
                      {/* 선택지가 있으면 버튼으로 표시 */}
                      {choices.length > 0 && (
                        <div className="chat-message__choices">
                          {choices.map((choice, choiceIdx) => (
                            <button
                              key={choiceIdx}
                              className="chat-message__choice-btn"
                              onClick={() => onChoiceSelect && onChoiceSelect(choice)}
                            >
                              {choice}
                            </button>
                          ))}
                        </div>
                      )}
                    </li>
                  );
                })}
              </ul>
            </div>
          )}
          
          {/* 액션 완료 표시 */}
          {message.actionCompleted && (
            <div className="chat-message__action-status">
              {message.actionCompleted === 'confirmed' && !message.actionError ? (
                <span className="chat-message__action-status--success">
                  ✅ 성공적으로 처리되었습니다!
                </span>
              ) : message.actionCompleted === 'cancelled' ? (
                <span className="chat-message__action-status--cancelled">
                  취소되었습니다.
                </span>
              ) : (
                <span className="chat-message__action-status--error">
                  ✗ {message.actionError || '처리 중 오류가 발생했습니다'}
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
