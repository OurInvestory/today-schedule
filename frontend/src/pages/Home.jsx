import React, { useState } from 'react';
import Calendar from '../components/calendar/Calendar';
import TodoList from '../components/todo/TodoList';
import TodoFilter from '../components/todo/TodoFilter';
import ChatbotButton from '../components/chatbot/ChatbotButton';
import ChatbotWindow from '../components/chatbot/ChatbotWindow';
import Button from '../components/common/Button';
import Modal from '../components/common/Modal';
import Input from '../components/common/Input';
import SearchableSelect from '../components/common/SearchableSelect';
import { useTodo } from '../hooks/useTodo';
import { useChatbot } from '../hooks/useChatbot';
import { useCalendar } from '../hooks/useCalendar';
import { formatDate } from '../utils/dateUtils';
import { calculatePriority } from '../utils/priorityUtils';
import { CATEGORY_LABELS } from '../utils/constants';
import './Home.css';

const Home = ({ isFullCalendarMode = false }) => {
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingTodo, setEditingTodo] = useState(null);
  const [newTodo, setNewTodo] = useState({
    title: '',
    description: '',
    date: '',
    category: 'other',
    importance: 5,
    estimatedTime: 1,
    estimatedMinute: 60,
    scheduleId: '', // 일정 ID 필수
  });

  const { todos, loading, toggleComplete, addTodo, editTodo, removeTodo, updateFilter, filter } =
    useTodo({ date: 'today' });

  // 일정 목록 가져오기 (할일 추가 시 일정 선택용)
  const { events: schedules } = useCalendar();

  const {
    isOpen: isChatOpen,
    messages,
    loading: chatLoading,
    messagesEndRef,
    toggleChatbot,
    sendMessage,
    confirmAction,
    cancelAction,
    clearMessages,
    retryLastMessage,
    lastUserMessage,
  } = useChatbot();

  const handleDateSelect = (date) => {
    setSelectedDate(date);
    updateFilter({ date: formatDate(date, 'YYYY-MM-DD') });
  };

  const handleAddTodo = async () => {
    try {
      // 일정 선택 필수 확인
      if (!newTodo.scheduleId) {
        alert('할 일을 추가하려면 일정을 선택해야 합니다.');
        return;
      }
      
      // 우선순위 자동 계산
      const priority = calculatePriority(newTodo.date, newTodo.estimatedMinute);
      
      await addTodo({
        ...newTodo,
        priority
      });
      setIsAddModalOpen(false);
      setNewTodo({
        title: '',
        description: '',
        date: '',
        category: 'other',
        importance: 5,
        estimatedTime: 1,
        estimatedMinute: 60,
        scheduleId: '',
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
    <div className={`home ${isFullCalendarMode ? 'home--full-calendar' : ''}`}>
      <div className="home__container">
        {isFullCalendarMode ? (
          // 전체 캘린더 모드
          <div className="home__full-calendar">
            <Calendar 
              onDateSelect={handleDateSelect} 
              todos={todos} 
              isFullMode={true}
            />
          </div>
        ) : (
          // 일반 대시보드 모드
          <>
            {/* Left: Calendar */}
            <aside className="home__calendar">
              <Calendar onDateSelect={handleDateSelect} todos={todos} />
            </aside>

            {/* Right: Todo List */}
            <main className="home__main">
          <div className="home__header" style={{ marginBottom: '16px' }}>
            <div className="home__header-left">
              <svg 
                className="home__header-icon"
                width="22" 
                height="22" 
                viewBox="0 0 24 24" 
                fill="none" 
                stroke="currentColor" 
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
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

          <TodoFilter filter={filter} onFilterChange={updateFilter} style={{ marginBottom: '16px' }} />

          <div className="home__todos">
            <TodoList
              todos={todos}
              loading={loading}
              onToggle={toggleComplete}
              onEdit={handleOpenEditModal}
              onDelete={removeTodo}
              onAdd={() => {
                // 선택된 날짜를 기본값으로 설정
                const year = selectedDate.getFullYear();
                const month = String(selectedDate.getMonth() + 1).padStart(2, '0');
                const day = String(selectedDate.getDate()).padStart(2, '0');
                const dateStr = `${year}-${month}-${day}`;
                setNewTodo(prev => ({ ...prev, date: dateStr, scheduleId: '' }));
                setIsAddModalOpen(true);
              }}
              emptyMessage="할 일이 없습니다. 새로운 할 일을 추가해보세요!"
            />
          </div>
            </main>
          </>
        )}
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
        onConfirmAction={confirmAction}
        onCancelAction={cancelAction}
        onClearHistory={clearMessages}
        onRetry={retryLastMessage}
        canRetry={!!lastUserMessage}
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
          <div className="add-todo-form__group">
            <label className="add-todo-form__label">소속 일정 * (필수)</label>
            <SearchableSelect
              options={schedules}
              value={newTodo.scheduleId}
              onChange={(schedule) => {
                setNewTodo({ 
                  ...newTodo, 
                  scheduleId: schedule.id,
                  // 선택한 일정의 카테고리를 자동 설정
                  category: schedule.category || newTodo.category,
                });
              }}
              placeholder="일정을 검색하거나 선택하세요"
              searchPlaceholder="일정 검색..."
              formatOption={(schedule) => schedule.title}
              formatDate={formatDate}
              required
            />
            <small className="add-todo-form__hint">할 일은 반드시 일정에 소속되어야 합니다.</small>
          </div>
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
          <Input
            label="날짜"
            type="date"
            required
            value={newTodo.date}
            onChange={(e) => setNewTodo({ ...newTodo, date: e.target.value })}
          />
          <div className="add-todo-form__row">
            <Input
              label="중요도 (자동 계산)"
              type="number"
              value={newTodo.importance}
              readOnly
              disabled
            />
            <Input
              label="예상 시간 (분)"
              type="number"
              min="5"
              step="5"
              value={newTodo.estimatedMinute}
              onChange={(e) =>
                setNewTodo({ ...newTodo, estimatedMinute: parseInt(e.target.value) })
              }
            />
          </div>
          <div className="add-todo-form__group">
            <label className="add-todo-form__label">카테고리 *</label>
            <select
              className="add-todo-form__select"
              value={newTodo.category}
              onChange={(e) => setNewTodo({ ...newTodo, category: e.target.value })}
            >
              {Object.entries(CATEGORY_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
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
            <Input
              label="날짜"
              type="date"
              required
              value={editingTodo.dueDate || ''}
              onChange={(e) => setEditingTodo({ ...editingTodo, dueDate: e.target.value })}
            />
            <div className="add-todo-form__row">
              <Input
                label="중요도 (자동 계산)"
                type="number"
                value={Math.floor(Math.min(10, Math.max(1, editingTodo.importance || editingTodo.priorityScore || 5)))}
                readOnly
                disabled
              />
              <Input
                label="예상 시간 (분)"
                type="number"
                min="5"
                step="5"
                value={editingTodo.estimatedMinute || 60}
                onChange={(e) =>
                  setEditingTodo({ ...editingTodo, estimatedMinute: parseInt(e.target.value) })
                }
              />
            </div>
            <div className="add-todo-form__group">
              <label className="add-todo-form__label">카테고리 *</label>
              <select
                className="add-todo-form__select"
                value={editingTodo.category || 'other'}
                onChange={(e) => setEditingTodo({ ...editingTodo, category: e.target.value })}
              >
                {Object.entries(CATEGORY_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default Home;