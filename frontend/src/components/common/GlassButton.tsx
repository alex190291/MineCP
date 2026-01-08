import React from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import { cn } from '@/utils/cn';

interface GlassButtonProps extends HTMLMotionProps<'button'> {
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
    primary: 'glass-button bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 border-blue-500/30',
    secondary: 'glass-button bg-white/10 hover:bg-white/15 text-white border-white/20',
    danger: 'glass-button bg-red-500/20 hover:bg-red-500/30 text-red-300 border-red-500/30',
    ghost: 'glass-button bg-transparent hover:bg-white/5 text-white border-transparent',
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  return (
    <motion.button
      className={cn(
        'relative rounded-lg font-medium transition-all',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        variants[variant],
        sizes[size],
        className
      )}
      disabled={disabled || loading}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      {...props}
    >
      {loading && (
        <Loader2 className="w-4 h-4 absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 animate-spin" />
      )}
      <span className={cn(loading && 'invisible')}>{children}</span>
    </motion.button>
  );
};
