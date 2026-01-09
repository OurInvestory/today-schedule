import React from 'react';
import Badge from '../common/Badge';
import { CATEGORIES, CATEGORY_LABELS } from '../../utils/constants';

const CategoryBadge = ({ category, size = 'sm' }) => {
  const variantMap = {
    [CATEGORIES.CLASS]: 'category-class',
    [CATEGORIES.ASSIGNMENT]: 'category-assignment',
    [CATEGORIES.EXAM]: 'category-exam',
    [CATEGORIES.TEAM]: 'category-team',
    [CATEGORIES.ACTIVITY]: 'category-activity',
  };

  const label = CATEGORY_LABELS[category] || category;

  return (
    <Badge variant={variantMap[category]} size={size}>
      {label}
    </Badge>
  );
};

export default CategoryBadge;