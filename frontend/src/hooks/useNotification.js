import { useState, useCallback } from 'react';
import { isUrgent, isOverdue } from '../utils/priorityUtils';

export const useNotification = () => {
  // 초기 상태를 lazy initialization으로 설정
  const [permission, setPermission] = useState(() => {
    return 'Notification' in window ? Notification.permission : 'default';
  });
  
  const [enabled, setEnabled] = useState(() => {
    return 'Notification' in window && Notification.permission === 'granted';
  });

  // 알림 권한 요청
  const requestPermission = async () => {
    if (!('Notification' in window)) {
      console.error('This browser does not support notifications');
      return false;
    }

    try {
      const result = await Notification.requestPermission();
      setPermission(result);
      setEnabled(result === 'granted');
      return result === 'granted';
    } catch (err) {
      console.error('Failed to request notification permission:', err);
      return false;
    }
  };

  // 알림 표시
  const showNotification = useCallback((title, options = {}) => {
    if (!enabled) {
      console.warn('Notifications are not enabled');
      return;
    }

    const defaultOptions = {
      icon: '/favicon.ico',
      badge: '/favicon.ico',
      vibrate: [200, 100, 200],
      requireInteraction: false,
      ...options,
    };

    try {
      const notification = new Notification(title, defaultOptions);
      
      // 알림 클릭 이벤트
      notification.onclick = () => {
        window.focus();
        notification.close();
        if (options.onClick) {
          options.onClick();
        }
      };

      return notification;
    } catch (err) {
      console.error('Failed to show notification:', err);
    }
  }, [enabled]);

  // Todo 마감 알림
  const notifyTodoDeadline = useCallback((todo) => {
    const title = '마감 임박!';
    const body = `"${todo.title}" 마감까지 얼마 남지 않았습니다.`;
    
    showNotification(title, {
      body,
      tag: `todo-${todo.id}`,
      data: { todoId: todo.id },
    });
  }, [showNotification]);

  // 우선순위 높은 Todo 알림
  const notifyHighPriorityTodo = useCallback((todo) => {
    const title = '우선순위 높음';
    const body = `"${todo.title}"을(를) 먼저 처리하는 것이 좋습니다.`;
    
    showNotification(title, {
      body,
      tag: `priority-${todo.id}`,
      data: { todoId: todo.id },
    });
  }, [showNotification]);

  // 일일 요약 알림
  const notifyDailySummary = useCallback((todos) => {
    const pendingCount = todos.filter(t => !t.completed).length;
    const urgentCount = todos.filter(t => isUrgent(t.dueDate)).length;
    
    const title = '오늘의 할 일';
    const body = `총 ${pendingCount}개의 할 일이 있습니다.${
      urgentCount > 0 ? ` (긴급: ${urgentCount}개)` : ''
    }`;
    
    showNotification(title, { body, tag: 'daily-summary' });
  }, [showNotification]);

  // 마감 지난 Todo 알림
  const notifyOverdueTodos = useCallback((todos) => {
    const overdueTodos = todos.filter(t => isOverdue(t.dueDate) && !t.completed);
    
    if (overdueTodos.length === 0) return;
    
    const title = '마감 지난 할 일';
    const body = `${overdueTodos.length}개의 할 일이 마감되었습니다.`;
    
    showNotification(title, { body, tag: 'overdue-todos' });
  }, [showNotification]);

  // Todo 완료 축하 알림
  const notifyTodoCompleted = useCallback((todo) => {
    const title = '완료!';
    const body = `"${todo.title}"을(를) 완료했습니다. 🎉`;
    
    showNotification(title, {
      body,
      tag: `completed-${todo.id}`,
      requireInteraction: false,
    });
  }, [showNotification]);

  // 스케줄 알림 체크 (주기적으로 실행)
  const checkAndNotify = useCallback((todos) => {
    if (!enabled) return;

    todos.forEach(todo => {
      if (todo.completed) return;

      // 마감 임박 알림 (24시간 이내)
      if (isUrgent(todo.dueDate)) {
        notifyTodoDeadline(todo);
      }

      // 마감 지남 알림
      if (isOverdue(todo.dueDate)) {
        // 하루에 한 번만 알림 (로컬 스토리지 활용 가능)
        const lastNotified = localStorage.getItem(`overdue-notified-${todo.id}`);
        const today = new Date().toDateString();
        
        if (lastNotified !== today) {
          notifyOverdueTodos([todo]);
          localStorage.setItem(`overdue-notified-${todo.id}`, today);
        }
      }
    });
  }, [enabled, notifyTodoDeadline, notifyOverdueTodos]);

  return {
    permission,
    enabled,
    requestPermission,
    showNotification,
    notifyTodoDeadline,
    notifyHighPriorityTodo,
    notifyDailySummary,
    notifyOverdueTodos,
    notifyTodoCompleted,
    checkAndNotify,
  };
};