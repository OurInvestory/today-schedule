import React, { useState } from 'react';
import { CATEGORIES, CATEGORY_LABELS, PRIORITIES, PRIORITY_LABELS } from '../../utils/constants';
import './TodoFilter.css';

// PC/태블릿용 드롭다운 필터
const DesktopFilter = ({ filter, handleCategoryChange, handlePriorityChange, handleCompletedChange }) => (
  <div className="todo-filter todo-filter--desktop">
    <div className="todo-filter__group">
      <label htmlFor="category-filter" className="todo-filter__label">
        카테고리
      </label>
      <select
        id="category-filter"
        className="todo-filter__select"
        value={filter.category || ''}
        onChange={(e) => handleCategoryChange(e.target.value)}
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
        onChange={(e) => handlePriorityChange(e.target.value)}
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
        onChange={(e) => handleCompletedChange(e.target.value)}
      >
        <option value="all">전체</option>
        <option value="pending">미완료</option>
        <option value="completed">완료</option>
      </select>
    </div>
  </div>
);

// 모바일용 하단 시트 필터
const MobileFilter = ({ filter, activeCount, handleCategoryChange, handlePriorityChange, handleCompletedChange, onFilterChange, isBottomSheetOpen, setIsBottomSheetOpen }) => (
  <>
    <button 
      className="todo-filter__mobile-trigger"
      onClick={() => setIsBottomSheetOpen(true)}
    >
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
      </svg>
      <span>필터</span>
      {activeCount > 0 && (
        <span className="todo-filter__badge">{activeCount}</span>
      )}
    </button>

    {isBottomSheetOpen && (
      <>
        <div 
          className="todo-filter__overlay"
          onClick={() => setIsBottomSheetOpen(false)}
        />
        <div className="todo-filter__bottom-sheet">
          <div className="todo-filter__sheet-header">
            <h3 className="todo-filter__sheet-title">필터</h3>
            <button 
              className="todo-filter__sheet-close"
              onClick={() => setIsBottomSheetOpen(false)}
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>

          <div className="todo-filter__sheet-content">
            {/* 카테고리 */}
            <div className="todo-filter__sheet-section">
              <h4 className="todo-filter__sheet-label">카테고리</h4>
              <div className="todo-filter__chip-group">
                <button
                  className={`todo-filter__chip ${!filter.category ? 'todo-filter__chip--active' : ''}`}
                  onClick={() => handleCategoryChange('')}
                >
                  전체
                </button>
                {Object.entries(CATEGORY_LABELS).map(([value, label]) => (
                  <button
                    key={value}
                    className={`todo-filter__chip ${filter.category === value ? 'todo-filter__chip--active' : ''}`}
                    onClick={() => handleCategoryChange(value)}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {/* 우선순위 */}
            <div className="todo-filter__sheet-section">
              <h4 className="todo-filter__sheet-label">우선순위</h4>
              <div className="todo-filter__chip-group">
                <button
                  className={`todo-filter__chip ${!filter.priority ? 'todo-filter__chip--active' : ''}`}
                  onClick={() => handlePriorityChange('')}
                >
                  전체
                </button>
                {Object.entries(PRIORITY_LABELS).map(([value, label]) => (
                  <button
                    key={value}
                    className={`todo-filter__chip todo-filter__chip--${value} ${filter.priority === value ? 'todo-filter__chip--active' : ''}`}
                    onClick={() => handlePriorityChange(value)}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {/* 상태 */}
            <div className="todo-filter__sheet-section">
              <h4 className="todo-filter__sheet-label">상태</h4>
              <div className="todo-filter__chip-group">
                <button
                  className={`todo-filter__chip ${filter.completed === undefined ? 'todo-filter__chip--active' : ''}`}
                  onClick={() => handleCompletedChange('all')}
                >
                  전체
                </button>
                <button
                  className={`todo-filter__chip ${filter.completed === false ? 'todo-filter__chip--active' : ''}`}
                  onClick={() => handleCompletedChange('pending')}
                >
                  미완료
                </button>
                <button
                  className={`todo-filter__chip ${filter.completed === true ? 'todo-filter__chip--active' : ''}`}
                  onClick={() => handleCompletedChange('completed')}
                >
                  완료
                </button>
              </div>
            </div>
          </div>

          <div className="todo-filter__sheet-footer">
            <button 
              className="todo-filter__reset-btn"
              onClick={() => {
                onFilterChange({ category: undefined, priority: undefined, completed: undefined });
              }}
            >
              초기화
            </button>
            <button 
              className="todo-filter__apply-btn"
              onClick={() => setIsBottomSheetOpen(false)}
            >
              적용하기
            </button>
          </div>
        </div>
      </>
    )}
  </>
);

const TodoFilter = ({ filter, onFilterChange }) => {
  const [isBottomSheetOpen, setIsBottomSheetOpen] = useState(false);

  const handleCategoryChange = (value) => {
    onFilterChange({ category: value || undefined });
  };

  const handlePriorityChange = (value) => {
    onFilterChange({ priority: value || undefined });
  };

  const handleCompletedChange = (value) => {
    onFilterChange({ 
      completed: value === 'all' ? undefined : value === 'completed' 
    });
  };

  const getActiveFilterCount = () => {
    let count = 0;
    if (filter.category) count++;
    if (filter.priority) count++;
    if (filter.completed !== undefined) count++;
    return count;
  };

  const activeCount = getActiveFilterCount();

  return (
    <>
      <DesktopFilter 
        filter={filter} 
        handleCategoryChange={handleCategoryChange} 
        handlePriorityChange={handlePriorityChange} 
        handleCompletedChange={handleCompletedChange} 
      />
      <MobileFilter 
        filter={filter} 
        activeCount={activeCount} 
        handleCategoryChange={handleCategoryChange} 
        handlePriorityChange={handlePriorityChange} 
        handleCompletedChange={handleCompletedChange} 
        onFilterChange={onFilterChange} 
        isBottomSheetOpen={isBottomSheetOpen} 
        setIsBottomSheetOpen={setIsBottomSheetOpen} 
      />
    </>
  );
};

export default TodoFilter;