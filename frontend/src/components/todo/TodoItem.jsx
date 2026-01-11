import React, { useState, useRef } from 'react';
import { getTimeUntilText, isOverdue } from '../../utils/dateUtils';
import PriorityBadge from './PriorityBadge';
import CategoryBadge from './CategoryBadge';
import './TodoItem.css';

const TodoItem = ({ todo, onToggle, onEdit, onDelete }) => {
  const [swipeOffset, setSwipeOffset] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const startXRef = useRef(0);
  const currentXRef = useRef(0);

  const handleCheckboxChange = (e) => {
    e.stopPropagation();
    onToggle(todo.id, !todo.completed);
  };

  const handleDoubleClick = () => {
    if (onEdit) onEdit(todo);
  };

  const handleDelete = () => {
    if (onDelete) onDelete(todo.id);
  };

  // 터치/마우스 시작
  const handleDragStart = (clientX) => {
    startXRef.current = clientX;
    currentXRef.current = clientX;
    setIsDragging(true);
  };

  // 터치/마우스 이동
  const handleDragMove = (clientX) => {
    if (!isDragging) return;
    currentXRef.current = clientX;
    const diff = clientX - startXRef.current;
    // 왼쪽으로만 스와이프 허용
    if (diff < 0) {
      setSwipeOffset(Math.max(diff, -100));
    }
  };

  // 터치/마우스 종료
  const handleDragEnd = () => {
    setIsDragging(false);
    if (swipeOffset < -60) {
      // 삭제 실행
      handleDelete();
    }
    setSwipeOffset(0);
  };

  // 마우스 이벤트
  const handleMouseDown = (e) => {
    if (e.target.closest('.todo-item__checkbox') || e.target.closest('.todo-item__actions')) return;
    handleDragStart(e.clientX);
  };

  const handleMouseMove = (e) => {
    handleDragMove(e.clientX);
  };

  const handleMouseUp = () => {
    handleDragEnd();
  };

  const handleMouseLeave = () => {
    if (isDragging) handleDragEnd();
  };

  // 터치 이벤트
  const handleTouchStart = (e) => {
    if (e.target.closest('.todo-item__checkbox') || e.target.closest('.todo-item__actions')) return;
    handleDragStart(e.touches[0].clientX);
  };

  const handleTouchMove = (e) => {
    handleDragMove(e.touches[0].clientX);
  };

  const handleTouchEnd = () => {
    handleDragEnd();
  };

  const itemClass = [
    'todo-item',
    todo.completed && 'todo-item--completed',
    isOverdue(todo.dueDate) && !todo.completed && 'todo-item--overdue',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className="todo-item__wrapper">
      {/* 삭제 배경 */}
      <div 
        className="todo-item__delete-bg"
        style={{ 
          width: swipeOffset < 0 ? Math.abs(swipeOffset) : 0,
          opacity: swipeOffset < 0 ? 1 : 0 
        }}
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
          <path d="M3 6h18M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
        </svg>
        <span>삭제</span>
      </div>
      
      <div 
        className={itemClass}
        style={{ transform: `translateX(${swipeOffset}px)` }}
        onDoubleClick={handleDoubleClick}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseLeave}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
      {/* Checkbox */}
      <label className="todo-item__checkbox" onClick={(e) => e.stopPropagation()}>
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
    </div>
  </div>
  );
};

export default TodoItem;