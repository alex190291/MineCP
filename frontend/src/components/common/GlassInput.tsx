import React from 'react';
import { cn } from '@/utils/cn';

interface GlassInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const GlassInput = React.forwardRef<HTMLInputElement, GlassInputProps>(
  ({ label, error, className, ...props }, ref) => {
    return (
      <div className="space-y-2">
        {label && (
          <label className="block text-sm font-medium text-white/80">
            {label}
          </label>
        )}
        <input
          ref={ref}
          className={cn(
            'glass-input w-full rounded-lg px-4 py-2.5',
            'text-white placeholder:text-white/40',
            'focus:ring-2 focus:ring-blue-500/50',
            error && 'border-red-500/50',
            className
          )}
          {...props}
        />
        {error && (
          <p className="text-sm text-red-400">{error}</p>
        )}
      </div>
    );
  }
);

GlassInput.displayName = 'GlassInput';
