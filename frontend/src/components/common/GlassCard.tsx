import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/utils/cn';

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  onClick?: () => void;
}

export const GlassCard: React.FC<GlassCardProps> = ({
  children,
  className,
  hover = false,
  onClick,
}) => {
  const Component = hover ? motion.div : 'div';
  const isInteractive = hover || onClick;

  return (
    <Component
      className={cn(
        'glass rounded-2xl p-6',
        isInteractive && 'glass-hover',
        className
      )}
      onClick={onClick}
      whileHover={hover ? { y: -2 } : undefined}
      whileTap={hover ? { scale: 0.98 } : undefined}
      transition={{ duration: 0.2, ease: 'easeOut' }}
    >
      {children}
    </Component>
  );
};
