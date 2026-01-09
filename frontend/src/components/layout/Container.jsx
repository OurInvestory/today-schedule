import React from 'react';
import './Container.css';

const Container = ({ children, maxWidth = 'xl', padding = true, className = '' }) => {
  const containerClass = [
    'container',
    `container--${maxWidth}`,
    !padding && 'container--no-padding',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return <div className={containerClass}>{children}</div>;
};

export default Container;