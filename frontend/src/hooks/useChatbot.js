import { useState, useCallback, useRef, useEffect } from 'react';
import {
  sendChatMessage,
  getChatHistory,
  createScheduleFromAI,
  createSubTaskFromAI,
  analyzeTimetableImage,
  createLectureFromAI,
  saveLectures,
  searchSchedulesByKeyword,
} from '../services/aiService';
import {
  scheduleReminder,
  scheduleReminderForSchedule,
} from '../services/notificationService';
import { createNotification } from '../services/notificationApiService';
import { deleteCalendarEvent } from '../services/calendarService';

// localStorage 키
const CHAT_STORAGE_KEY = 'chatbot_messages';
const CHAT_GREETED_KEY = 'chatbot_has_greeted';

// 10가지 랜덤 인사 템플릿
const greetingTemplates = [
  '안녕하세요! 👋 오늘 하루도 파이팅이에요! 일정 관리 도와드릴게요.',
  '반가워요! 🎉 무엇을 도와드릴까요? 일정 추가, 조회, 우선순위 정리 다 할 수 있어요!',
  '어서 오세요! 🌟 오늘 할 일이 많으신가요? 함께 정리해봐요!',
  '안녕하세요! 😊 일정 관리 AI 도우미입니다. 편하게 말씀해주세요!',
  '좋은 하루예요! ✨ 일정이나 할 일 관련해서 도움이 필요하시면 말씀해주세요.',
  '반갑습니다! 🙌 시간표 이미지 분석, 일정 추가, 알림 예약 모두 가능해요!',
  '하이요! 💪 오늘의 미션을 함께 정리해볼까요?',
  '안녕하세요! 📅 일정 걱정은 저에게 맡기세요! 무엇을 도와드릴까요?',
  '환영합니다! 🚀 효율적인 일정 관리를 위해 제가 도와드릴게요!',
  '만나서 반가워요! 🌈 할 일 추가, 일정 조회 등 무엇이든 물어보세요!',
];

// 시간대별 인사 접두어
const getTimeGreeting = () => {
  const hour = new Date().getHours();
  if (hour >= 5 && hour < 12) return '좋은 아침이에요! ☀️';
  if (hour >= 12 && hour < 18) return '좋은 오후예요! 🌤️';
  return '좋은 저녁이에요! 🌙';
};

// 첫 인사 메시지 (랜덤)
const getGreetingMessage = () => {
  const timeGreeting = getTimeGreeting();
  const randomTemplate =
    greetingTemplates[Math.floor(Math.random() * greetingTemplates.length)];

  return {
    id: 'greeting',
    role: 'assistant',
    content: `${timeGreeting} ${randomTemplate}`,
    timestamp: new Date().toISOString(),
  };
};

// 10가지 랜덤 로딩 메시지
const loadingMessages = [
  '열심히 처리 중이에요... 🔄',
  '잠시만요, 확인하고 있어요! ⏳',
  '일정을 분석하고 있습니다... 📊',
  '좋은 답변을 준비하고 있어요! 💭',
  '데이터를 확인하는 중이에요... 🔍',
  '조금만 기다려주세요! ⚡',
  '최선의 답변을 찾고 있어요... 🎯',
  '열심히 일하는 중! 🏃‍♂️',
  '거의 다 됐어요... ✨',
  '정보를 정리하고 있습니다! 📝',
];

// 랜덤 로딩 메시지 가져오기
export const getRandomLoadingMessage = () => {
  return loadingMessages[Math.floor(Math.random() * loadingMessages.length)];
};

// 빠른 패턴 매칭: "알림 예약" 패턴 감지
const NOTIFICATION_PATTERN = /(.+?)\s*(\d+)\s*분\s*전에?\s*알림/;
const TIMETABLE_PATTERN = /시간표.*사진|사진.*시간표|강의.*추가/;

// 빠른 알림 예약 처리 (LLM 호출 없이 로컬에서 처리)
const handleQuickNotificationRequest = async (text) => {
  const match = text.match(NOTIFICATION_PATTERN);
  if (!match) return null;

  const keyword = match[1].trim(); // "회의" 등의 키워드
  const minutesBefore = parseInt(match[2], 10);

  // 키워드로 일정 검색
  const schedules = await searchSchedulesByKeyword(keyword);

  if (schedules.length === 0) {
    return {
      type: 'NO_SCHEDULES',
      keyword,
      minutesBefore,
      message: `'${keyword}' 키워드가 포함된 예정된 일정을 찾지 못했어요. 다른 키워드로 검색하거나 일정을 먼저 추가해주세요.`,
    };
  }

  // 일정 목록 반환 (사용자가 선택할 수 있도록)
  return {
    type: 'SCHEDULE_LIST',
    keyword,
    minutesBefore,
    schedules: schedules.map((s) => ({
      id: s.schedule_id || s.id,
      title: s.title,
      start_at: s.start_at,
      end_at: s.end_at,
    })),
    message: `'${keyword}' 키워드가 포함된 일정을 찾았어요! 📋\n알림을 설정할 일정을 선택해주세요.`,
  };
};

// localStorage에서 메시지 불러오기
const loadMessagesFromStorage = () => {
  try {
    const saved = localStorage.getItem(CHAT_STORAGE_KEY);
    return saved ? JSON.parse(saved) : [];
  } catch {
    return [];
  }
};

// localStorage에 메시지 저장
const saveMessagesToStorage = (messages) => {
  try {
    localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(messages));
  } catch (e) {
    console.error('Failed to save messages to storage:', e);
  }
};

// localStorage에서 인사 상태 불러오기
const loadGreetedFromStorage = () => {
  try {
    return localStorage.getItem(CHAT_GREETED_KEY) === 'true';
  } catch {
    return false;
  }
};

// localStorage에 인사 상태 저장
const saveGreetedToStorage = (greeted) => {
  try {
    localStorage.setItem(CHAT_GREETED_KEY, String(greeted));
  } catch (e) {
    console.error('Failed to save greeted state:', e);
  }
};

export const useChatbot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState(() => loadMessagesFromStorage());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [conversationId, setConversationId] = useState(null);
  const [hasGreeted, setHasGreeted] = useState(() => loadGreetedFromStorage());
  const [lastUserMessage, setLastUserMessage] = useState(null); // 재시도용 마지막 메시지 저장
  const messagesEndRef = useRef(null);

  // 메시지 변경 시 localStorage에 저장
  useEffect(() => {
    if (messages.length > 0) {
      saveMessagesToStorage(messages);
    }
  }, [messages]);

  // 챗봇 열기/닫기
  const toggleChatbot = useCallback(() => {
    setIsOpen((prev) => !prev);
  }, []);

  const openChatbot = useCallback(() => {
    setIsOpen(true);
  }, []);

  const closeChatbot = useCallback(() => {
    setIsOpen(false);
  }, []);

  // 챗봇 열릴 때 첫 인사
  useEffect(() => {
    if (isOpen && !hasGreeted && messages.length === 0) {
      const greetingMessage = getGreetingMessage();
      setMessages([greetingMessage]);
      setHasGreeted(true);
      saveGreetedToStorage(true);
    }
  }, [isOpen, hasGreeted, messages.length]);

  // 메시지 전송 (파일 업로드 지원)
  const sendMessage = async (text, selectedScheduleId = null, files = null) => {
    if (!text.trim() && (!files || files.length === 0)) return;

    // 재시도를 위한 마지막 메시지 저장
    setLastUserMessage({ text, selectedScheduleId, files });

    // 파일 정보 생성 (미리보기 URL 포함)
    const fileInfo = files
      ? Array.from(files).map((f) => {
          const info = {
            name: f.name,
            type: f.type,
            size: f.size,
          };

          // 이미지 파일인 경우 미리보기 URL 추가
          if (f.type.startsWith('image/')) {
            info.preview = URL.createObjectURL(f);
          }

          return info;
        })
      : null;

    // 사용자 메시지 추가
    let userContent = text || '시간표 사진에 있는 강의 추가해줘';

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: userContent,
      timestamp: new Date().toISOString(),
      files: fileInfo,
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);
    setError(null);

    try {
      // 이미지 파일이 있는 경우 시간표 분석
      const imageFiles = files
        ? Array.from(files).filter((f) => f.type.startsWith('image/'))
        : [];

      if (imageFiles.length > 0) {
        // 시간표 이미지 분석
        const imageAnalysisResult = await analyzeTimetableImage(imageFiles[0]);

        if (imageAnalysisResult && imageAnalysisResult.success) {
          let actions =
            imageAnalysisResult.actions ||
            imageAnalysisResult.parsedResult?.actions ||
            [];
          const lectures = imageAnalysisResult.lectures || [];

          let displayMessage = '';

          // lectures 배열이 있으면 강의 추가 UI 표시
          if (lectures && lectures.length > 0) {
            // lectures를 LECTURES 타겟 액션으로 변환
            const lecturesAction = {
              op: 'CREATE',
              target: 'LECTURES',
              payload: lectures,
            };
            // 기존 actions에 lectures 액션 추가 (중복 방지)
            const hasLecturesAction = actions.some(
              (a) => a.target === 'LECTURES'
            );
            if (!hasLecturesAction) {
              actions = [
                lecturesAction,
                ...actions.filter((a) => a.payload?.type !== 'EVENT'),
              ];
            }

            // 텍스트 리스트는 chat-message__lectures-list UI에서 표시하므로 메시지에서 제거
            displayMessage = `이미지에서 강의 정보를 찾았어요! 📚\n시간표에 추가할까요?`;
          } else if (actions && actions.length > 0) {
            // 강의는 없지만 일정이 있는 경우 (포스터 등)
            displayMessage = `이미지에서 일정 정보를 찾았어요! 📅\n일정을 추가할까요?`;
          } else {
            // 아무것도 찾지 못한 경우
            displayMessage =
              '이미지를 분석했지만 일정 정보를 찾지 못했어요. 📸\n다른 이미지로 다시 시도해주세요.';
          }

          const newAssistantMessage = {
            id: Date.now() + 1,
            role: 'assistant',
            content: displayMessage,
            timestamp: new Date().toISOString(),
            parsedResult: imageAnalysisResult.parsedResult,
            actions: actions,
            imageAnalysis: imageAnalysisResult,
            lectures: lectures,
          };
          setMessages((prev) => [...prev, newAssistantMessage]);
          setLoading(false);
          return;
        } else {
          // 이미지 분석 실패
          const errorMessage = {
            id: Date.now() + 1,
            role: 'assistant',
            content:
              '이미지 분석에 실패했어요. 😢\n시간표가 잘 보이는 선명한 이미지로 다시 시도해주세요.',
            timestamp: new Date().toISOString(),
          };
          setMessages((prev) => [...prev, errorMessage]);
          setLoading(false);
          return;
        }
      }

      // 빠른 알림 예약 패턴 감지 (LLM 호출 없이 로컬에서 처리)
      const notificationResult = await handleQuickNotificationRequest(text);

      if (notificationResult) {
        if (notificationResult.type === 'NO_SCHEDULES') {
          // 일정을 찾지 못한 경우
          const noScheduleMessage = {
            id: Date.now() + 1,
            role: 'assistant',
            content: notificationResult.message,
            timestamp: new Date().toISOString(),
          };
          setMessages((prev) => [...prev, noScheduleMessage]);
          setLoading(false);
          return;
        }

        if (notificationResult.type === 'SCHEDULE_LIST') {
          // 일정 목록을 보여주고 사용자가 선택하게 함
          const scheduleListMessage = {
            id: Date.now() + 1,
            role: 'assistant',
            content: notificationResult.message,
            timestamp: new Date().toISOString(),
            notificationRequest: {
              keyword: notificationResult.keyword,
              minutesBefore: notificationResult.minutesBefore,
              schedules: notificationResult.schedules,
            },
          };
          setMessages((prev) => [...prev, scheduleListMessage]);
          setLoading(false);
          return;
        }
      }

      // 이전 CLARIFY 컨텍스트 확인 (마지막 assistant 메시지에서)
      let userContext = {};
      const lastAssistantMsg = messages
        .filter((m) => m.role === 'assistant')
        .slice(-1)[0];
      if (lastAssistantMsg?.parsedResult?.intent === 'CLARIFY') {
        // 이전 CLARIFY의 preserved_info를 userContext로 전달
        userContext = {
          ...lastAssistantMsg.parsedResult.preserved_info,
          previous_intent: 'CLARIFY',
          previous_type: lastAssistantMsg.parsedResult.type,
        };
      }

      // 일반 텍스트 메시지 처리
      const response = await sendChatMessage(
        text,
        null,
        selectedScheduleId,
        userContext,
        null
      );

      // axios 응답 구조: response.data가 API 응답 본문
      // API 응답 구조: { status, message, data: { parsedResult, assistantMessage } }
      const apiResponse = response.data;
      console.log('API Response:', apiResponse); // 디버깅용

      // data가 없거나 오류인 경우 처리
      if (!apiResponse || apiResponse.status !== 200) {
        throw new Error(apiResponse?.message || '서버 응답 오류');
      }

      const responseData = apiResponse.data || {};
      const parsedResult =
        responseData.parsed_result || responseData.parsedResult;
      const assistantMessage =
        responseData.assistant_message || responseData.assistantMessage;

      // 응답 메시지 추가
      const newAssistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: assistantMessage || '요청을 처리했습니다.',
        timestamp: new Date().toISOString(),
        parsedResult: parsedResult,
        actions: parsedResult?.actions || [],
        reasoning: parsedResult?.reasoning,
        missingFields:
          parsedResult?.missingFields || parsedResult?.missing_fields || [],
      };

      setMessages((prev) => [...prev, newAssistantMessage]);

      // 대화 ID 저장
      if (apiResponse.conversationId) {
        setConversationId(apiResponse.conversationId);
      }
    } catch (err) {
      setError(err.message || '메시지 전송에 실패했습니다.');
      console.error('Failed to send message:', err);

      // 에러 메시지 추가
      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: '죄송합니다. 오류가 발생했습니다. 다시 시도해주세요.',
        timestamp: new Date().toISOString(),
        isError: true,
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  // 대화 내역 불러오기
  const loadHistory = async (convId) => {
    try {
      setLoading(true);
      setError(null);
      const history = await getChatHistory(convId);
      setMessages(history);
      setConversationId(convId);
    } catch (err) {
      setError(err.message || '대화 내역을 불러오는데 실패했습니다.');
      console.error('Failed to load chat history:', err);
    } finally {
      setLoading(false);
    }
  };

  // 대화 초기화
  const clearMessages = useCallback(() => {
    setMessages([]);
    setConversationId(null);
    setError(null);
    setHasGreeted(false);
    setLastUserMessage(null);
    // localStorage 초기화
    localStorage.removeItem(CHAT_STORAGE_KEY);
    localStorage.removeItem(CHAT_GREETED_KEY);
  }, []);

  // 마지막 메시지 재시도
  const retryLastMessage = useCallback(async () => {
    if (lastUserMessage && !loading) {
      // 마지막 에러 메시지 제거
      setMessages((prev) => {
        const newMessages = [...prev];
        // 마지막 메시지가 에러면 제거
        if (
          newMessages.length > 0 &&
          newMessages[newMessages.length - 1].isError
        ) {
          newMessages.pop();
        }
        // 마지막 사용자 메시지도 제거 (다시 보낼 것임)
        if (
          newMessages.length > 0 &&
          newMessages[newMessages.length - 1].role === 'user'
        ) {
          newMessages.pop();
        }
        return newMessages;
      });

      // 재시도
      await sendMessage(
        lastUserMessage.text,
        lastUserMessage.selectedScheduleId,
        lastUserMessage.files
      );
    }
  }, [lastUserMessage, loading]);

  // 인터랙티브 액션 확인 (일정/할 일 생성/알림 예약)
  const confirmAction = useCallback(
    async (messageId, action, parsedResult = null, actionIndex = null) => {
      // 개별 액션 로딩 상태 업데이트
      if (actionIndex !== null) {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === messageId
              ? {
                  ...msg,
                  loadingActions: {
                    ...msg.loadingActions,
                    [actionIndex]: true,
                  },
                }
              : msg
          )
        );
      } else {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === messageId
              ? { ...msg, actionCompleted: 'confirmed', actionLoading: true }
              : msg
          )
        );
      }

      try {
        let result;
        let confirmContent = '';

        // NOTIFICATION_REQUEST 인텐트 처리
        if (parsedResult?.intent === 'NOTIFICATION_REQUEST') {
          const preserved = parsedResult.preserved_info || {};
          const targetTitle = preserved.target_title || '일정';
          const minutesBefore = preserved.minutes_before;
          const reminderTime = preserved.reminder_time;

          if (reminderTime) {
            // 특정 시간에 알림 예약
            result = scheduleReminder({
              title: targetTitle,
              message: `예약된 알림: ${targetTitle}`,
              scheduledTime: reminderTime,
            });
            confirmContent = `'${targetTitle}' 알림이 예약되었습니다! 🔔`;
          } else if (minutesBefore) {
            // N분 전 알림 - 일정 검색 후 예약 필요
            // 현재는 간단하게 현재 시간 + 분으로 예약
            const reminderDate = new Date(
              Date.now() + minutesBefore * 60 * 1000
            );
            result = scheduleReminder({
              title: `${targetTitle} 알림`,
              message: `${minutesBefore}분 전 알림: ${targetTitle}`,
              scheduledTime: reminderDate.toISOString(),
            });
            confirmContent = `'${targetTitle}' ${minutesBefore}분 전 알림이 예약되었습니다! 🔔`;
          }
        }
        // 액션 타입에 따라 처리
        // target이 없으면 payload.type으로 판단 (이미지 분석 결과)
        const payloadType = action?.payload?.type?.toUpperCase();
        const actionTarget =
          action?.target || (payloadType === 'TASK' ? 'SUB_TASK' : 'SCHEDULE');

        if (action?.op === 'CREATE') {
          if (actionTarget === 'LECTURES') {
            // 시간표 강의 일괄 생성
            const lecturesPayload = Array.isArray(action.payload)
              ? action.payload
              : [action.payload];
            const response = await saveLectures(lecturesPayload);
            result = response?.data || response;
            confirmContent = `${lecturesPayload.length}개의 강의가 시간표에 추가되었습니다! 📚`;
          } else if (actionTarget === 'NOTIFICATION') {
            // 알림 생성 - POST /api/notifications
            const notifyPayload = {
              message: action.payload.message,
              notify_at: action.payload.notify_at,
              schedule_id: action.payload.schedule_id || null,
            };
            const response = await createNotification(notifyPayload);
            result = response?.data || response;

            // 알림 시간 포맷팅
            const notifyAt = new Date(action.payload.notify_at);
            const timeStr = `${
              notifyAt.getMonth() + 1
            }월 ${notifyAt.getDate()}일 ${String(notifyAt.getHours()).padStart(
              2,
              '0'
            )}:${String(notifyAt.getMinutes()).padStart(2, '0')}`;
            confirmContent = `알림이 설정되었습니다! 🔔 (${timeStr})`;
          } else if (actionTarget === 'SCHEDULE' || payloadType === 'EVENT') {
            // 일정 생성
            const response = await createScheduleFromAI(action.payload);
            // axios 응답에서 data 추출
            result = response?.data || response;
            confirmContent = '일정이 성공적으로 추가되었습니다! ✅';
          } else if (actionTarget === 'SUB_TASK' || payloadType === 'TASK') {
            // 할 일 생성 - importance_score를 priority로 변환
            const importanceScore = action.payload.importance_score || 5;
            let priority = 'medium';
            if (importanceScore >= 7) priority = 'high';
            else if (importanceScore <= 3) priority = 'low';

            // end_at에서 date 추출
            const endAt = action.payload.end_at || action.payload.date;
            const dateStr = endAt
              ? endAt.split('T')[0]
              : new Date().toISOString().split('T')[0];

            const payloadWithTip = {
              ...action.payload,
              date: dateStr,
              priority: action.payload.priority || priority,
              tip: action.payload.tip || action.payload.reason || null,
            };
            const response = await createSubTaskFromAI(
              action.scheduleId,
              payloadWithTip
            );
            result = response?.data || response;
            confirmContent = '할 일이 성공적으로 추가되었습니다! ✅';
          }
        } else if (action?.op === 'UPDATE') {
          confirmContent = '일정이 수정되었습니다! ✏️';
        } else if (action?.op === 'DELETE') {
          confirmContent = '일정이 삭제되었습니다! 🗑️';
        }

        // 개별 액션 성공 업데이트
        if (actionIndex !== null) {
          setMessages((prev) =>
            prev.map((msg) => {
              if (msg.id !== messageId) return msg;

              const newCompletedActions = {
                ...msg.completedActions,
                [actionIndex]: 'confirmed',
              };
              const newLoadingActions = {
                ...msg.loadingActions,
                [actionIndex]: false,
              };
              const newActionResults = {
                ...msg.actionResults,
                [actionIndex]: {
                  success: true,
                  result,
                  message: confirmContent,
                },
              };

              // 모든 액션이 완료되었는지 확인
              const totalActions = msg.actions?.length || 0;
              const completedCount = Object.keys(newCompletedActions).length;
              const allCompleted = completedCount === totalActions;

              return {
                ...msg,
                completedActions: newCompletedActions,
                loadingActions: newLoadingActions,
                actionResults: newActionResults,
                actionCompleted: allCompleted
                  ? 'confirmed'
                  : msg.actionCompleted,
              };
            })
          );

          // 개별 성공 메시지 추가
          const confirmMessage = {
            id: Date.now(),
            role: 'assistant',
            content: confirmContent || '처리가 완료되었습니다! ✅',
            timestamp: new Date().toISOString(),
          };
          setMessages((prev) => [...prev, confirmMessage]);
        } else {
          // 전체 액션 성공 업데이트 (기존 로직)
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === messageId
                ? { ...msg, actionLoading: false, actionResult: result }
                : msg
            )
          );

          // 확인 메시지 추가
          const confirmMessage = {
            id: Date.now(),
            role: 'assistant',
            content:
              confirmContent ||
              '처리가 완료되었습니다! ✅ 다른 도움이 필요하시면 말씀해주세요.',
            timestamp: new Date().toISOString(),
          };
          setMessages((prev) => [...prev, confirmMessage]);
        }

        // 페이지 새로고침을 위한 이벤트 발생
        window.dispatchEvent(new CustomEvent('scheduleUpdated'));
      } catch (err) {
        console.error('Action confirmation failed:', err);

        if (actionIndex !== null) {
          // 개별 액션 에러 업데이트
          setMessages((prev) =>
            prev.map((msg) => {
              if (msg.id !== messageId) return msg;

              return {
                ...msg,
                loadingActions: { ...msg.loadingActions, [actionIndex]: false },
                actionResults: {
                  ...msg.actionResults,
                  [actionIndex]: { success: false, error: err.message },
                },
              };
            })
          );
        } else {
          // 전체 액션 에러 업데이트 (기존 로직)
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === messageId
                ? { ...msg, actionLoading: false, actionError: err.message }
                : msg
            )
          );
        }

        // 에러 메시지 추가
        const errorMessage = {
          id: Date.now(),
          role: 'assistant',
          content:
            '죄송합니다. 처리 중 오류가 발생했습니다. 다시 시도해주세요.',
          timestamp: new Date().toISOString(),
          isError: true,
        };
        setMessages((prev) => [...prev, errorMessage]);
      }
    },
    []
  );

  // 인터랙티브 액션 취소 (개별 또는 전체)
  const cancelAction = useCallback((messageId, actionIndex = null) => {
    if (actionIndex === 'all') {
      // 전체 취소 (버튼으로 전체 취소) - 모든 pending 액션을 cancelled로 표시
      setMessages((prev) =>
        prev.map((msg) => {
          if (msg.id !== messageId) return msg;

          // 모든 액션을 cancelled로 표시
          const newCompletedActions = { ...msg.completedActions };
          (msg.actions || []).forEach((_, idx) => {
            if (!newCompletedActions[idx]) {
              newCompletedActions[idx] = 'cancelled';
            }
          });

          return {
            ...msg,
            completedActions: newCompletedActions,
            actionCompleted: 'cancelled',
          };
        })
      );

      // 취소 메시지 추가
      const cancelMessage = {
        id: Date.now(),
        role: 'assistant',
        content:
          '알겠습니다. 모두 취소되었습니다. 다른 도움이 필요하시면 말씀해주세요.',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, cancelMessage]);
    } else if (actionIndex !== null) {
      // 개별 액션 취소 - 먼저 제목을 찾고 나서 상태 업데이트
      setMessages((prev) => {
        // 취소된 액션의 정보 찾기
        const targetMsg = prev.find((msg) => msg.id === messageId);
        const cancelledAction = targetMsg?.actions?.[actionIndex];
        const actionTitle =
          cancelledAction?.payload?.title ||
          cancelledAction?.payload?.name ||
          '항목';

        // SCHEDULE 취소 시 연관된 SUB_TASK도 함께 취소
        const isScheduleCancel = cancelledAction?.target === 'SCHEDULE';

        // 메시지 업데이트
        const updatedMessages = prev.map((msg) => {
          if (msg.id !== messageId) return msg;

          const newCompletedActions = {
            ...msg.completedActions,
            [actionIndex]: 'cancelled',
          };

          // SCHEDULE 취소 시 같은 메시지의 모든 SUB_TASK도 취소
          if (isScheduleCancel && msg.actions) {
            msg.actions.forEach((action, idx) => {
              if (action.target === 'SUB_TASK' && !newCompletedActions[idx]) {
                newCompletedActions[idx] = 'cancelled';
              }
            });
          }

          // 모든 액션이 완료되었는지 확인
          const totalActions = msg.actions?.length || 0;
          const completedCount = Object.keys(newCompletedActions).length;
          const allCompleted = completedCount === totalActions;

          return {
            ...msg,
            completedActions: newCompletedActions,
            actionCompleted: allCompleted ? 'partial' : msg.actionCompleted,
          };
        });

        // 취소 메시지
        const cancelContent = isScheduleCancel
          ? '일정이 취소되었습니다.'
          : `'${actionTitle}' 항목이 취소되었습니다.`;

        const cancelMessage = {
          id: Date.now(),
          role: 'assistant',
          content: cancelContent,
          timestamp: new Date().toISOString(),
        };

        return [...updatedMessages, cancelMessage];
      });
    } else {
      // 전체 취소 (기존 로직, messageId만 전달된 경우)
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === messageId ? { ...msg, actionCompleted: 'cancelled' } : msg
        )
      );

      // 취소 메시지 추가
      const cancelMessage = {
        id: Date.now(),
        role: 'assistant',
        content:
          '알겠습니다. 취소되었습니다. 다른 도움이 필요하시면 말씀해주세요.',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, cancelMessage]);
    }
  }, []);

  // 메시지 자동 스크롤
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  // 새 메시지 추가 시 자동 스크롤
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // 알림 예약을 위한 일정 선택 처리
  const selectScheduleForNotification = useCallback(
    async (messageId, schedule, minutesBefore) => {
      // 선택한 일정에 대한 알림 예약
      const startTime = schedule.start_at;
      if (!startTime) {
        const errorMessage = {
          id: Date.now(),
          role: 'assistant',
          content:
            '해당 일정에 시작 시간이 설정되어 있지 않아 알림을 예약할 수 없어요. 😢',
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errorMessage]);
        return;
      }

      const scheduleStartTime = new Date(startTime);
      const reminderTime = new Date(
        scheduleStartTime.getTime() - minutesBefore * 60 * 1000
      );

      // 이미 지난 시간인지 확인
      if (reminderTime <= new Date()) {
        const errorMessage = {
          id: Date.now(),
          role: 'assistant',
          content: `'${schedule.title}' 일정의 ${minutesBefore}분 전은 이미 지났어요. 다른 일정을 선택해주세요.`,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errorMessage]);
        return;
      }

      try {
        // 백엔드 API를 통한 알림 예약
        const notificationData = {
          schedule_id: schedule.id,
          schedule_title: schedule.title,
          message: `${minutesBefore}분 후에 '${schedule.title}'이(가) 시작됩니다!`,
          notify_at: reminderTime.toISOString(),
          minutes_before: minutesBefore,
        };

        const response = await createNotification(notificationData);

        if (response.status !== 200 && response.status !== 201) {
          throw new Error('알림 예약 실패');
        }

        // 기존 로컬 알림도 함께 예약 (백업)
        scheduleReminder({
          title: `${schedule.title} 알림`,
          message: `${minutesBefore}분 후에 '${schedule.title}'이(가) 시작됩니다!`,
          scheduledTime: reminderTime.toISOString(),
          scheduleId: schedule.id,
        });

        // 원래 메시지의 상태 업데이트
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === messageId
              ? {
                  ...msg,
                  notificationCompleted: true,
                  selectedSchedule: schedule,
                }
              : msg
          )
        );

        // 날짜/시간 포맷팅
        const formatDateTime = (date) => {
          const d = new Date(date);
          const month = d.getMonth() + 1;
          const day = d.getDate();
          const hours = String(d.getHours()).padStart(2, '0');
          const minutes = String(d.getMinutes()).padStart(2, '0');
          return `${month}월 ${day}일 ${hours}:${minutes}`;
        };

        // 성공 메시지 추가
        const successMessage = {
          id: Date.now(),
          role: 'assistant',
          content: `'${
            schedule.title
          }' 일정 ${minutesBefore}분 전 알림이 예약되었습니다! 🔔\n알림 시간: ${formatDateTime(
            reminderTime
          )}`,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, successMessage]);
      } catch (error) {
        console.error('Failed to create notification:', error);
        const errorMessage = {
          id: Date.now(),
          role: 'assistant',
          content: '알림 예약 중 오류가 발생했어요. 다시 시도해주세요. 😢',
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errorMessage]);
      }
    },
    []
  );

  // CLARIFY 선택지 선택 처리 (일정 삭제 포함)
  const handleChoiceSelect = useCallback(
    async (messageId, choice, choiceIndex, preservedInfo) => {
      // 취소 선택
      if (choice === '아니오' || choiceIndex === -1) {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === messageId
              ? { ...msg, clarifyCompleted: true, deleteCompleted: true }
              : msg
          )
        );

        const cancelMessage = {
          id: Date.now(),
          role: 'assistant',
          content: '알겠습니다. 취소되었습니다.',
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, cancelMessage]);
        return;
      }

      // 삭제 확인 (DELETE_CONFIRM) 또는 CLARIFY에서 일정 선택
      if (preservedInfo?.op === 'DELETE' || preservedInfo?.schedule_id) {
        // 로딩 상태 설정
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === messageId ? { ...msg, deleteLoading: true } : msg
          )
        );

        try {
          // schedule_id 가져오기
          let scheduleId = preservedInfo.schedule_id;

          // CLARIFY에서 선택한 경우 matching_schedules에서 id 찾기
          if (
            !scheduleId &&
            preservedInfo.matching_schedules &&
            choiceIndex >= 0
          ) {
            scheduleId = preservedInfo.matching_schedules[choiceIndex]?.id;
          }

          if (!scheduleId) {
            throw new Error('일정 ID를 찾을 수 없습니다.');
          }

          // DELETE API 호출
          const response = await deleteCalendarEvent(scheduleId);

          // 성공
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === messageId
                ? {
                    ...msg,
                    clarifyCompleted: true,
                    deleteCompleted: true,
                    deleteLoading: false,
                  }
                : msg
            )
          );

          const successMessage = {
            id: Date.now(),
            role: 'assistant',
            content: '일정이 삭제되었습니다! 🗑️',
            timestamp: new Date().toISOString(),
          };
          setMessages((prev) => [...prev, successMessage]);
        } catch (error) {
          console.error('Failed to delete schedule:', error);

          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === messageId ? { ...msg, deleteLoading: false } : msg
            )
          );

          const errorMessage = {
            id: Date.now(),
            role: 'assistant',
            content:
              error.response?.status === 404
                ? '해당 일정을 찾을 수 없어요. 이미 삭제되었을 수 있습니다.'
                : '일정 삭제 중 오류가 발생했어요. 다시 시도해주세요. 😢',
            timestamp: new Date().toISOString(),
            isError: true,
          };
          setMessages((prev) => [...prev, errorMessage]);
        }
        return;
      }

      // 기타 CLARIFY 선택 (삭제가 아닌 경우) - 사용자 선택을 메시지로 전송
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === messageId ? { ...msg, clarifyCompleted: true } : msg
        )
      );

      // 선택한 내용을 다시 메시지로 전송
      sendMessage(choice);
    },
    [sendMessage]
  );

  // 빠른 액션 (자주 사용하는 명령어)
  const quickActions = [
    { label: '오늘 할 일', message: '오늘 할 일 보여줘' },
    { label: '🔥 우선순위 높은 일정', message: '우선순위 높은 일정 추천해줘' },
    { label: '📷 시간표 추가', message: '시간표 사진에 있는 강의 추가해줘' },
    { label: '이번 주 일정', message: '이번 주 일정 정리해줘' },
  ];

  const sendQuickAction = (action) => {
    sendMessage(action.message);
  };

  return {
    isOpen,
    messages,
    loading,
    error,
    messagesEndRef,
    toggleChatbot,
    openChatbot,
    closeChatbot,
    sendMessage,
    loadHistory,
    clearMessages,
    scrollToBottom,
    quickActions,
    sendQuickAction,
    confirmAction,
    cancelAction,
    retryLastMessage,
    lastUserMessage,
    selectScheduleForNotification,
    handleChoiceSelect,
  };
};
