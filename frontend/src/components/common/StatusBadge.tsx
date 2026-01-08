import React from 'react';
import { ServerStatus } from '@/types/server';
import { cn } from '@/utils/cn';
import { STATUS_COLORS, STATUS_LABELS } from '@/utils/constants';

interface StatusBadgeProps {
  status: ServerStatus;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  return (
    <span
      className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
        `status-${status}`
      )}
    >
      <span
        className={cn(
          'w-2 h-2 rounded-full mr-1.5',
          STATUS_COLORS[status]
        )}
      />
      {STATUS_LABELS[status]}
    </span>
  );
};
