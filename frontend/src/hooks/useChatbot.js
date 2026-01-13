import { useState, useCallback, useRef, useEffect } from 'react';
import { sendChatMessage, getChatHistory, createScheduleFromAI, createSubTaskFromAI, analyzeTimetableImage } from '../services/aiService';

// 첫 인사 메시지
const getGreetingMessage = () => {
  const hour = new Date().getHours();
  let greeting = '안녕하세요!';
  
  if (hour >= 5 && hour < 12) {
    greeting = '좋은 아침이에요! ☀️';
  } else if (hour >= 12 && hour < 18) {
    greeting = '좋은 오후예요! 🌤️';
  } else {
    greeting = '좋은 저녁이에요! 🌙';
  }
  
  return {
    id: 'greeting',
    role: 'assistant',
    content: `${greeting} 저는 일정 관리를 도와드리는 AI 도우미입니다. 오늘 할 일을 확인하거나, 새로운 일정을 추가하거나, 우선순위를 정리하는 것을 도와드릴 수 있어요. 무엇을 도와드릴까요?`,
    timestamp: new Date().toISOString(),
  };
};

export const useChatbot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [conversationId, setConversationId] = useState(null);
  const [hasGreeted, setHasGreeted] = useState(false);
  const messagesEndRef = useRef(null);

  // 챗봇 열기/닫기
  const toggleChatbot = useCallback(() => {
    setIsOpen(prev => !prev);
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
    }
  }, [isOpen, hasGreeted, messages.length]);

  // 메시지 전송 (파일 업로드 지원)
  const sendMessage = async (text, selectedScheduleId = null, files = null) => {
    if (!text.trim() && (!files || files.length === 0)) return;

    // 이미지 파일 분석
    let imageAnalysisResult = null;
    const imageFiles = files ? Array.from(files).filter(f => f.type.startsWith('image/')) : [];
    
    if (imageFiles.length > 0) {
      try {
        // 첫 번째 이미지 분석 (시간표 감지)
        imageAnalysisResult = await analyzeTimetableImage(imageFiles[0]);
      } catch (error) {
        console.error('Image analysis failed:', error);
      }
    }

    // 파일 정보 생성 (미리보기 URL 포함)
    const fileInfo = files ? Array.from(files).map(f => {
      const info = { 
        name: f.name, 
        type: f.type, 
        size: f.size 
      };
      
      // 이미지 파일인 경우 미리보기 URL 추가
      if (f.type.startsWith('image/')) {
        info.preview = URL.createObjectURL(f);
      }
      
      return info;
    }) : null;

    // 사용자 메시지 추가
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: text || '이미지를 분석해주세요',
      timestamp: new Date().toISOString(),
      files: fileInfo,
    };

    setMessages(prev => [...prev, userMessage]);
    setLoading(true);
    setError(null);

    try {
      // 이미지 파일이 있으면 이미지 분석 결과를 사용
      if (imageAnalysisResult && imageAnalysisResult.success) {
        const newAssistantMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: imageAnalysisResult.message || '이미지 분석을 완료했어요! 📸',
          timestamp: new Date().toISOString(),
          parsedResult: imageAnalysisResult.parsedResult,
          actions: imageAnalysisResult.parsedResult?.actions || [],
          imageAnalysis: imageAnalysisResult,
        };
        setMessages(prev => [...prev, newAssistantMessage]);
        setLoading(false);
        return;
      }

      // 일반 텍스트 메시지 처리
      const response = await sendChatMessage(text, null, selectedScheduleId, {}, null);
      
      // axios 응답 구조: response.data가 API 응답 본문
      // API 응답 구조: { status, message, data: { parsedResult, assistantMessage } }
      const apiResponse = response.data;
      console.log('API Response:', apiResponse); // 디버깅용
      
      // data가 없거나 오류인 경우 처리
      if (!apiResponse || apiResponse.status !== 200) {
        throw new Error(apiResponse?.message || '서버 응답 오류');
      }
      
      const responseData = apiResponse.data || {};
      const parsedResult = responseData.parsed_result || responseData.parsedResult;
      const assistantMessage = responseData.assistant_message || responseData.assistantMessage;
      
      // 응답 메시지 추가
      const newAssistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: assistantMessage || '요청을 처리했습니다.',
        timestamp: new Date().toISOString(),
        parsedResult: parsedResult,
        actions: parsedResult?.actions || [],
        reasoning: parsedResult?.reasoning,
        missingFields: parsedResult?.missingFields || parsedResult?.missing_fields || [],
      };

      setMessages(prev => [...prev, newAssistantMessage]);
      
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
      
      setMessages(prev => [...prev, errorMessage]);
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
  }, []);

  // 인터랙티브 액션 확인 (일정/할 일 생성)
  const confirmAction = useCallback(async (messageId, action) => {
    setMessages(prev => prev.map(msg => 
      msg.id === messageId 
        ? { ...msg, actionCompleted: 'confirmed', actionLoading: true }
        : msg
    ));
    
    try {
      let result;
      
      // 액션 타입에 따라 처리
      if (action.op === 'CREATE') {
        if (action.target === 'SCHEDULE') {
          // 일정 생성
          result = await createScheduleFromAI(action.payload);
        } else if (action.target === 'SUB_TASK') {
          // 할 일 생성
          result = await createSubTaskFromAI(action.scheduleId, action.payload);
        }
      }
      
      // 성공 메시지 업데이트
      setMessages(prev => prev.map(msg => 
        msg.id === messageId 
          ? { ...msg, actionLoading: false, actionResult: result }
          : msg
      ));
      
      // 확인 메시지 추가
      const confirmMessage = {
        id: Date.now(),
        role: 'assistant',
        content: `${action.target === 'SCHEDULE' ? '일정이' : '할 일이'} 성공적으로 추가되었습니다! ✅ 다른 도움이 필요하시면 말씀해주세요.`,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, confirmMessage]);
      
      // 페이지 새로고침을 위한 이벤트 발생
      window.dispatchEvent(new CustomEvent('scheduleUpdated'));
      
    } catch (err) {
      console.error('Action confirmation failed:', err);
      
      setMessages(prev => prev.map(msg => 
        msg.id === messageId 
          ? { ...msg, actionLoading: false, actionError: err.message }
          : msg
      ));
      
      // 에러 메시지 추가
      const errorMessage = {
        id: Date.now(),
        role: 'assistant',
        content: '죄송합니다. 일정 추가 중 오류가 발생했습니다. 다시 시도해주세요.',
        timestamp: new Date().toISOString(),
        isError: true,
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  }, []);

  // 인터랙티브 액션 취소
  const cancelAction = useCallback((messageId) => {
    setMessages(prev => prev.map(msg => 
      msg.id === messageId 
        ? { ...msg, actionCompleted: 'cancelled' }
        : msg
    ));
    
    // 취소 메시지 추가
    const cancelMessage = {
      id: Date.now(),
      role: 'assistant',
      content: '알겠습니다. 취소되었습니다. 다른 도움이 필요하시면 말씀해주세요.',
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, cancelMessage]);
  }, []);

  // 메시지 자동 스크롤
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  // 새 메시지 추가 시 자동 스크롤
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // 빠른 액션 (자주 사용하는 명령어)
  const quickActions = [
    { label: '오늘 할 일', message: '오늘 할 일 보여줘' },
    { label: '일정 추가', message: '새로운 일정 추가해줘' },
    { label: '우선순위 보기', message: '우선순위 높은 일정 알려줘' },
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
  };
};