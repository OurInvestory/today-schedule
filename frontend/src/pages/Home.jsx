import React, { useState, useEffect } from 'react';
import Calendar from '../components/calendar/Calendar';
import TodoList from '../components/todo/TodoList';
import TodoFilter from '../components/todo/TodoFilter';
import ChatbotButton from '../components/chatbot/ChatbotButton';
import ChatbotWindow from '../components/chatbot/ChatbotWindow';
import Button from '../components/common/Button';
import Modal from '../components/common/Modal';
import Input from '../components/common/Input';
import { useTodo } from '../hooks/useTodo';
import { useChatbot } from '../hooks/useChatbot';
import { formatDate } from '../utils/dateUtils';
import './Home.css';

const Home = () => {
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingTodo, setEditingTodo] = useState(null);
  const [newTodo, setNewTodo] = useState({
    title: '',
    description: '',
    startDate: '',
    startTime: '',
    dueDate: '',
    dueTime: '',
    category: 'assignment',
    importance: 5,
    estimatedTime: 1,
  });

  // 시작일/시간과 마감일/시간이 모두 입력되면 예상 시간 자동 계산
  useEffect(() => {
    const { startDate, startTime, dueDate, dueTime } = newTodo;
    if (startDate && startTime && dueDate && dueTime) {
      const startDateTime = new Date(`${startDate}T${startTime}`);
      const dueDateTime = new Date(`${dueDate}T${dueTime}`);
      const diffMs = dueDateTime - startDateTime;
      if (diffMs > 0) {
        const diffHours = Math.round(diffMs / (1000 * 60 * 60) * 10) / 10; // 소수점 1자리
        setNewTodo(prev => ({ ...prev, estimatedTime: diffHours }));
      }
    }
  }, [newTodo.startDate, newTodo.startTime, newTodo.dueDate, newTodo.dueTime]);

  // 편집 모달에서도 시간 자동 계산
  useEffect(() => {
    if (!editingTodo) return;
    const { startDate, startTime, dueDate, dueTime } = editingTodo;
    if (startDate && startTime && dueDate && dueTime) {
      const startDateTime = new Date(`${startDate}T${startTime}`);
      const dueDateTime = new Date(`${dueDate}T${dueTime}`);
      const diffMs = dueDateTime - startDateTime;
      if (diffMs > 0) {
        const diffHours = Math.round(diffMs / (1000 * 60 * 60) * 10) / 10;
        setEditingTodo(prev => ({ ...prev, estimatedTime: diffHours }));
      }
    }
  }, [editingTodo?.startDate, editingTodo?.startTime, editingTodo?.dueDate, editingTodo?.dueTime]);

  const { todos, loading, toggleComplete, addTodo, editTodo, removeTodo, updateFilter, filter } =
    useTodo({ date: 'today' });

  const {
    isOpen: isChatOpen,
    messages,
    loading: chatLoading,
    messagesEndRef,
    toggleChatbot,
    sendMessage,
  } = useChatbot();

  const handleDateSelect = (date) => {
    setSelectedDate(date);
    updateFilter({ date: formatDate(date, 'YYYY-MM-DD') });
  };

  const handleAddTodo = async () => {
    try {
      await addTodo(newTodo);
      setIsAddModalOpen(false);
      setNewTodo({
        title: '',
        description: '',
        startDate: '',
        startTime: '',
        dueDate: '',
        dueTime: '',
        category: 'assignment',
        importance: 5,
        estimatedTime: 1,
      });
    } catch (error) {
      console.error('Failed to add todo:', error);
    }
  };

  const handleOpenEditModal = (todo) => {
    setEditingTodo({ ...todo });
    setIsEditModalOpen(true);
  };

  const handleEditTodo = async () => {
    try {
      await editTodo(editingTodo.id, editingTodo);
      setIsEditModalOpen(false);
      setEditingTodo(null);
    } catch (error) {
      console.error('Failed to edit todo:', error);
    }
  };

  return (
    <div className="home">
      <div className="home__container">
        {/* Left: Calendar */}
        <aside className="home__calendar">
          <Calendar onDateSelect={handleDateSelect} todos={todos} />
        </aside>

        {/* Right: Todo List */}
        <main className="home__main">
          <div className="home__header">
            <div className="home__header-left">
              <div className="home__header-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M9 11l3 3L22 4" />
                  <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
                </svg>
              </div>
              <div>
                <h1 className="home__title">
                  {formatDate(selectedDate, 'M월 D일')} 할 일
                </h1>
                <p className="home__subtitle">
                  {todos.filter((t) => !t.completed).length}개의 할 일이 남았습니다
                </p>
              </div>
            </div>
          </div>

          <TodoFilter filter={filter} onFilterChange={updateFilter} />

          <div className="home__todos">
            <TodoList
              todos={todos}
              loading={loading}
              onToggle={toggleComplete}
              onEdit={handleOpenEditModal}
              onDelete={removeTodo}
              onAdd={() => setIsAddModalOpen(true)}
              emptyMessage="할 일이 없습니다. 새로운 할 일을 추가해보세요!"
            />
          </div>
        </main>
      </div>

      {/* Chatbot */}
      <ChatbotButton onClick={toggleChatbot} />
      <ChatbotWindow
        isOpen={isChatOpen}
        onClose={toggleChatbot}
        messages={messages}
        onSendMessage={sendMessage}
        loading={chatLoading}
        messagesEndRef={messagesEndRef}
      />

      {/* Add Todo Modal */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="새 할 일 추가"
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsAddModalOpen(false)}>
              취소
            </Button>
            <Button onClick={handleAddTodo}>추가</Button>
          </>
        }
      >
        <div className="add-todo-form">
          <Input
            label="제목"
            required
            value={newTodo.title}
            onChange={(e) => setNewTodo({ ...newTodo, title: e.target.value })}
            placeholder="할 일 제목을 입력하세요"
          />
          <Input
            label="설명"
            value={newTodo.description}
            onChange={(e) => setNewTodo({ ...newTodo, description: e.target.value })}
            placeholder="상세 설명 (선택)"
          />
          <div className="add-todo-form__row">
            <Input
              label="시작일"
              type="date"
              required
              value={newTodo.startDate}
              onChange={(e) => setNewTodo({ ...newTodo, startDate: e.target.value })}
            />
            <Input
              label="시작 시간 (선택)"
              type="time"
              value={newTodo.startTime}
              onChange={(e) => setNewTodo({ ...newTodo, startTime: e.target.value })}
            />
          </div>
          <div className="add-todo-form__row">
            <Input
              label="마감일"
              type="date"
              required
              value={newTodo.dueDate}
              onChange={(e) => setNewTodo({ ...newTodo, dueDate: e.target.value })}
            />
            <Input
              label="마감 시간 (선택)"
              type="time"
              value={newTodo.dueTime}
              onChange={(e) => setNewTodo({ ...newTodo, dueTime: e.target.value })}
            />
          </div>
          <div className="add-todo-form__row">
            <Input
              label="중요도 (1-10)"
              type="number"
              min="1"
              max="10"
              value={newTodo.importance}
              onChange={(e) =>
                setNewTodo({ ...newTodo, importance: parseInt(e.target.value) })
              }
            />
            <Input
              label="예상 시간 (시간)"
              type="number"
              min="0.5"
              step="0.5"
              value={newTodo.estimatedTime}
              onChange={(e) =>
                setNewTodo({ ...newTodo, estimatedTime: parseFloat(e.target.value) })
              }
            />
          </div>
        </div>
      </Modal>

      {/* Edit Todo Modal */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => {
          setIsEditModalOpen(false);
          setEditingTodo(null);
        }}
        title="할 일 수정"
        footer={
          <>
            <Button variant="secondary" onClick={() => {
              setIsEditModalOpen(false);
              setEditingTodo(null);
            }}>
              취소
            </Button>
            <Button onClick={handleEditTodo}>저장</Button>
          </>
        }
      >
        {editingTodo && (
          <div className="add-todo-form">
            <Input
              label="제목"
              required
              value={editingTodo.title}
              onChange={(e) => setEditingTodo({ ...editingTodo, title: e.target.value })}
              placeholder="할 일 제목을 입력하세요"
            />
            <Input
              label="설명"
              value={editingTodo.description || ''}
              onChange={(e) => setEditingTodo({ ...editingTodo, description: e.target.value })}
              placeholder="상세 설명 (선택)"
            />
            <div className="add-todo-form__row">
              <Input
                label="시작일"
                type="date"
                required
                value={editingTodo.startDate || ''}
                onChange={(e) => setEditingTodo({ ...editingTodo, startDate: e.target.value })}
              />
              <Input
                label="시작 시간 (선택)"
                type="time"
                value={editingTodo.startTime || ''}
                onChange={(e) => setEditingTodo({ ...editingTodo, startTime: e.target.value })}
              />
            </div>
            <div className="add-todo-form__row">
              <Input
                label="마감일"
                type="date"
                required
                value={editingTodo.dueDate || ''}
                onChange={(e) => setEditingTodo({ ...editingTodo, dueDate: e.target.value })}
              />
              <Input
                label="마감 시간 (선택)"
                type="time"
                value={editingTodo.dueTime || ''}
                onChange={(e) => setEditingTodo({ ...editingTodo, dueTime: e.target.value })}
              />
            </div>
            <div className="add-todo-form__row">
              <Input
                label="중요도 (1-10)"
                type="number"
                min="1"
                max="10"
                value={editingTodo.importance}
                onChange={(e) =>
                  setEditingTodo({ ...editingTodo, importance: parseInt(e.target.value) })
                }
              />
              <Input
                label="예상 시간 (시간)"
                type="number"
                min="0.5"
                step="0.5"
                value={editingTodo.estimatedTime}
                onChange={(e) =>
                  setEditingTodo({ ...editingTodo, estimatedTime: parseFloat(e.target.value) })
                }
              />
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default Home;