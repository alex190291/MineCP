import React from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '@/utils/cn';

interface GlassButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  children: React.ReactNode;
}

export const GlassButton: React.FC<GlassButtonProps> = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  children,
  className,
  disabled,
  ...props
}) => {
  const variants = {
    primary: 'btn primary',
    secondary: 'btn secondary',
    danger: 'btn danger',
    ghost: 'btn secondary',
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  return (
    <button
      className={cn(
        'relative inline-flex items-center justify-center',
        variants[variant],
        sizes[size],
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <span className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
          <Loader2 className="w-4 h-4 animate-spin" />
        </span>
      )}
      <span className={cn(loading && 'invisible')}>{children}</span>
    </button>
  );
};
