import React, { useState, useRef, useEffect } from 'react';
import './SearchableSelect.css';

const SearchableSelect = ({
  options,
  value,
  onChange,
  placeholder = '선택하세요',
  searchPlaceholder = '검색...',
  required = false,
  disabled = false,
  formatOption = (option) => option.label || option.title,
  formatDate = null,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const containerRef = useRef(null);
  const searchInputRef = useRef(null);

  // 클릭 외부 감지
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
        setSearchTerm('');
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // 드롭다운 열릴 때 검색창에 포커스
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isOpen]);

  // 필터링된 옵션
  const filteredOptions = options.filter((option) => {
    const label = formatOption(option).toLowerCase();
    return label.includes(searchTerm.toLowerCase());
  });

  // 현재 선택된 옵션 찾기
  const selectedOption = options.find((opt) => opt.id === value || opt.value === value);

  const handleSelect = (option) => {
    onChange(option);
    setIsOpen(false);
    setSearchTerm('');
  };

  const handleToggle = () => {
    if (!disabled) {
      setIsOpen(!isOpen);
    }
  };

  return (
    <div 
      className={`searchable-select ${isOpen ? 'searchable-select--open' : ''} ${disabled ? 'searchable-select--disabled' : ''}`}
      ref={containerRef}
    >
      <button
        type="button"
        className="searchable-select__trigger"
        onClick={handleToggle}
        disabled={disabled}
      >
        <span className={`searchable-select__value ${!selectedOption ? 'searchable-select__value--placeholder' : ''}`}>
          {selectedOption ? (
            <>
              {formatOption(selectedOption)}
              {formatDate && selectedOption.startDate && (
                <span className="searchable-select__date">
                  ({formatDate(selectedOption.startDate || selectedOption.start_at, 'M/D')})
                </span>
              )}
            </>
          ) : placeholder}
        </span>
        <svg 
          className={`searchable-select__arrow ${isOpen ? 'searchable-select__arrow--up' : ''}`}
          width="12" 
          height="12" 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          strokeWidth="2"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {isOpen && (
        <div className="searchable-select__dropdown">
          <div className="searchable-select__search">
            <svg 
              className="searchable-select__search-icon"
              width="16" 
              height="16" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2"
            >
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input
              ref={searchInputRef}
              type="text"
              className="searchable-select__search-input"
              placeholder={searchPlaceholder}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onClick={(e) => e.stopPropagation()}
            />
          </div>
          <div className="searchable-select__options">
            {filteredOptions.length === 0 ? (
              <div className="searchable-select__no-results">
                {searchTerm ? '검색 결과가 없습니다' : '옵션이 없습니다'}
              </div>
            ) : (
              filteredOptions.map((option) => (
                <button
                  key={option.id || option.value}
                  type="button"
                  className={`searchable-select__option ${(option.id === value || option.value === value) ? 'searchable-select__option--selected' : ''}`}
                  onClick={() => handleSelect(option)}
                >
                  <span className="searchable-select__option-label">
                    {formatOption(option)}
                  </span>
                  {formatDate && (option.startDate || option.start_at) && (
                    <span className="searchable-select__option-date">
                      {formatDate(option.startDate || option.start_at, 'M/D')}
                    </span>
                  )}
                  {option.source === 'google' && (
                    <span className="searchable-select__option-badge">G</span>
                  )}
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default SearchableSelect;
