import React from 'react';
import TodoItem from './TodoItem';
import Loading from '../common/Loading';
import './TodoList.css';

const TodoList = ({ todos, loading, onToggle, onEdit, onDelete, emptyMessage }) => {
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
    </div>
  );
};

export default TodoList;