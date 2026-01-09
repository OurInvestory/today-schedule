import React, { forwardRef } from 'react';
import './Input.css';

const Input = forwardRef(
  (
    {
      type = 'text',
      label,
      placeholder,
      value,
      onChange,
      error,
      helper,
      disabled = false,
      required = false,
      fullWidth = false,
      icon = null,
      size = 'md',
      className = '',
      ...props
    },
    ref
  ) => {
    const inputClass = [
      'input',
      `input--${size}`,
      error && 'input--error',
      disabled && 'input--disabled',
      icon && 'input--with-icon',
      fullWidth && 'input--full-width',
      className,
    ]
      .filter(Boolean)
      .join(' ');

    return (
      <div className={`input-wrapper ${fullWidth ? 'input-wrapper--full-width' : ''}`}>
        {label && (
          <label className="input__label">
            {label}
            {required && <span className="input__required">*</span>}
          </label>
        )}
        <div className="input__container">
          {icon && <span className="input__icon">{icon}</span>}
          <input
            ref={ref}
            type={type}
            className={inputClass}
            value={value}
            onChange={onChange}
            placeholder={placeholder}
            disabled={disabled}
            required={required}
            {...props}
          />
        </div>
        {error && <p className="input__error-message">{error}</p>}
        {helper && !error && <p className="input__helper-text">{helper}</p>}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;