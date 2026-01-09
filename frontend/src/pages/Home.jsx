import React, { useState } from 'react';
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
  const [newTodo, setNewTodo] = useState({
    title: '',
    description: '',
    dueDate: '',
    category: 'assignment',
    importance: 5,
    estimatedTime: 1,
  });

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
        dueDate: '',
        category: 'assignment',
        importance: 5,
        estimatedTime: 1,
      });
    } catch (error) {
      console.error('Failed to add todo:', error);
    }
  };

  return (
    <div className="home">
      <div className="home__container">
        {/* Left: Calendar */}
        <aside className="home__calendar">
          <Calendar onDateSelect={handleDateSelect} />
        </aside>

        {/* Right: Todo List */}
        <main className="home__main">
          <div className="home__header">
            <div>
              <h1 className="home__title">
                {formatDate(selectedDate, 'M월 D일')} 할 일
              </h1>
              <p className="home__subtitle">
                {todos.filter((t) => !t.completed).length}개의 할 일이 남았습니다
              </p>
            </div>
            <Button onClick={() => setIsAddModalOpen(true)}>
              + 할 일 추가
            </Button>
          </div>

          <TodoFilter filter={filter} onFilterChange={updateFilter} />

          <div className="home__todos">
            <TodoList
              todos={todos}
              loading={loading}
              onToggle={toggleComplete}
              onEdit={editTodo}
              onDelete={removeTodo}
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
          <Input
            label="마감일"
            type="datetime-local"
            required
            value={newTodo.dueDate}
            onChange={(e) => setNewTodo({ ...newTodo, dueDate: e.target.value })}
          />
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
    </div>
  );
};

export default Home;