import React from 'react';
import { X } from 'lucide-react';
import { GlassCard } from './GlassCard';
import { GlassButton } from './GlassButton';

interface ConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  confirmVariant?: 'danger' | 'primary';
}

export const ConfirmModal: React.FC<ConfirmModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  confirmVariant = 'primary',
}) => {
  if (!isOpen) return null;

  const handleConfirm = () => {
    onConfirm();
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      <GlassCard className="relative max-w-md w-full p-6 space-y-4">
        <div className="flex items-start justify-between">
          <h3 className="text-xl font-semibold text-white">{title}</h3>
          <button
            onClick={onClose}
            className="text-white/60 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <p className="text-white/80">{message}</p>

        <div className="flex gap-3 pt-2">
          <GlassButton
            onClick={handleConfirm}
            className={
              confirmVariant === 'danger'
                ? 'bg-red-500/20 hover:bg-red-500/30 border-red-500/30'
                : ''
            }
          >
            {confirmText}
          </GlassButton>
          <GlassButton onClick={onClose} variant="secondary">
            {cancelText}
          </GlassButton>
        </div>
      </GlassCard>
    </div>
  );
};
