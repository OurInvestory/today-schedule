import { useState, useCallback, useRef, useEffect } from 'react';
import { sendChatMessage, getChatHistory } from '../services/aiService';

export const useChatbot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [conversationId, setConversationId] = useState(null);
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

  // 메시지 전송
  const sendMessage = async (text) => {
    if (!text.trim()) return;

    // 사용자 메시지 추가
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setLoading(true);
    setError(null);

    try {
      const response = await sendChatMessage(text, conversationId);
      
      // 응답 메시지 추가
      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.message || response.content,
        timestamp: new Date().toISOString(),
        data: response.data, // 추가 데이터 (할 일 생성 결과 등)
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      // 대화 ID 저장
      if (response.conversationId) {
        setConversationId(response.conversationId);
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
  };
};