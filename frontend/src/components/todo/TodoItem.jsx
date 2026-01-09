import React from 'react';
import { getTimeUntilText, isOverdue } from '../../utils/dateUtils';
import PriorityBadge from './PriorityBadge';
import CategoryBadge from './CategoryBadge';
import './TodoItem.css';

const TodoItem = ({ todo, onToggle, onEdit, onDelete }) => {
  const handleCheckboxChange = () => {
    onToggle(todo.id, !todo.completed);
  };

  const handleEdit = () => {
    if (onEdit) onEdit(todo);
  };

  const handleDelete = () => {
    if (onDelete) onDelete(todo.id);
  };

  const itemClass = [
    'todo-item',
    todo.completed && 'todo-item--completed',
    isOverdue(todo.dueDate) && !todo.completed && 'todo-item--overdue',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={itemClass}>
      {/* Priority indicator */}
      <div 
        className="todo-item__priority-indicator" 
        style={{ 
          backgroundColor: `var(--color-priority-${todo.priority}-text)` 
        }}
      />

      {/* Checkbox */}
      <label className="todo-item__checkbox">
        <input
          type="checkbox"
          checked={todo.completed}
          onChange={handleCheckboxChange}
        />
        <span className="todo-item__checkmark">
          {todo.completed && (
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path
                d="M2 6L5 9L10 3"
                stroke="white"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          )}
        </span>
      </label>

      {/* Content */}
      <div className="todo-item__content">
        <div className="todo-item__header">
          <h3 className="todo-item__title">{todo.title}</h3>
          <div className="todo-item__badges">
            <CategoryBadge category={todo.category} />
            <PriorityBadge priority={todo.priority} showIcon={false} />
          </div>
        </div>

        {todo.description && (
          <p className="todo-item__description">{todo.description}</p>
        )}

        <div className="todo-item__footer">
          <span className="todo-item__time">
            {getTimeUntilText(todo.dueDate)}
          </span>
          {todo.estimatedTime && (
            <span className="todo-item__estimated-time">
              예상 {todo.estimatedTime}시간
            </span>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="todo-item__actions">
        <button
          type="button"
          className="todo-item__action-btn"
          onClick={handleEdit}
          aria-label="수정"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor">
            <path d="M11.5 2L14 4.5L5 13.5H2.5V11L11.5 2Z" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
        <button
          type="button"
          className="todo-item__action-btn todo-item__action-btn--danger"
          onClick={handleDelete}
          aria-label="삭제"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor">
            <path d="M3 4H13M5 4V3C5 2.5 5.5 2 6 2H10C10.5 2 11 2.5 11 3V4M12 4V13C12 13.5 11.5 14 11 14H5C4.5 14 4 13.5 4 13V4" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
      </div>
    </div>
  );
};

export default TodoItem;