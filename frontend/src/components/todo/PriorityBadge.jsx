import React from 'react';
import Badge from '../common/Badge';
import { PRIORITIES, PRIORITY_LABELS, PRIORITY_ICONS } from '../../utils/constants';

const PriorityBadge = ({ priority, size = 'sm', showIcon = true }) => {
  const variantMap = {
    [PRIORITIES.HIGH]: 'priority-high',
    [PRIORITIES.MEDIUM]: 'priority-medium',
    [PRIORITIES.LOW]: 'priority-low',
  };

  const label = PRIORITY_LABELS[priority] || priority;
  const icon = PRIORITY_ICONS[priority] || '';

  return (
    <Badge variant={variantMap[priority]} size={size}>
      {showIcon && icon && <span style={{ marginRight: '4px' }}>{icon}</span>}
      {label}
    </Badge>
  );
};

export default PriorityBadge;