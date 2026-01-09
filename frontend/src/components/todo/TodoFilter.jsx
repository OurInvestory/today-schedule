import React from 'react';
import { CATEGORIES, CATEGORY_LABELS, PRIORITIES, PRIORITY_LABELS } from '../../utils/constants';
import './TodoFilter.css';

const TodoFilter = ({ filter, onFilterChange }) => {
  const handleCategoryChange = (e) => {
    const value = e.target.value;
    onFilterChange({ category: value || undefined });
  };

  const handlePriorityChange = (e) => {
    const value = e.target.value;
    onFilterChange({ priority: value || undefined });
  };

  const handleCompletedChange = (e) => {
    const value = e.target.value;
    onFilterChange({ 
      completed: value === 'all' ? undefined : value === 'completed' 
    });
  };

  return (
    <div className="todo-filter">
      <div className="todo-filter__group">
        <label htmlFor="category-filter" className="todo-filter__label">
          카테고리
        </label>
        <select
          id="category-filter"
          className="todo-filter__select"
          value={filter.category || ''}
          onChange={handleCategoryChange}
        >
          <option value="">전체</option>
          {Object.entries(CATEGORY_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>

      <div className="todo-filter__group">
        <label htmlFor="priority-filter" className="todo-filter__label">
          우선순위
        </label>
        <select
          id="priority-filter"
          className="todo-filter__select"
          value={filter.priority || ''}
          onChange={handlePriorityChange}
        >
          <option value="">전체</option>
          {Object.entries(PRIORITY_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>

      <div className="todo-filter__group">
        <label htmlFor="completed-filter" className="todo-filter__label">
          상태
        </label>
        <select
          id="completed-filter"
          className="todo-filter__select"
          value={
            filter.completed === undefined
              ? 'all'
              : filter.completed
              ? 'completed'
              : 'pending'
          }
          onChange={handleCompletedChange}
        >
          <option value="all">전체</option>
          <option value="pending">미완료</option>
          <option value="completed">완료</option>
        </select>
      </div>
    </div>
  );
};

export default TodoFilter;