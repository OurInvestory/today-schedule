import React from 'react';
import TodoItem from './TodoItem';
import Loading from '../common/Loading';
import './TodoList.css';

const TodoList = ({ todos, loading, onToggle, onEdit, onDelete, onAdd, emptyMessage }) => {
  if (loading) {
    return (
      <div className="todo-list todo-list--loading">
        <Loading text="할 일을 불러오는 중..." />
      </div>
    );
  }

  if (!todos || todos.length === 0) {
    return (
      <div className="todo-list-empty">
        <svg
          width="64"
          height="64"
          viewBox="0 0 64 64"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <rect x="12" y="12" width="40" height="40" rx="4" />
          <path d="M20 28L28 36L44 20" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <p className="todo-list-empty__message">
          {emptyMessage || '할 일이 없습니다'}
        </p>
        {onAdd && (
          <button className="todo-list__add-btn todo-list__add-btn--empty" onClick={onAdd}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            <span>할 일 추가</span>
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="todo-list">
      {todos.map((todo) => (
        <TodoItem
          key={todo.id}
          todo={todo}
          onToggle={onToggle}
          onEdit={onEdit}
          onDelete={onDelete}
        />
      ))}
      
      {/* 하단 추가 버튼 */}
      {onAdd && (
        <button className="todo-list__add-btn" onClick={onAdd}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
        </button>
      )}
    </div>
  );
};

export default TodoList;