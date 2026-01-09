import React from 'react';
import { LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import { GlassButton } from '@/components/common/GlassButton';
import { useAuthStore } from '@/store/authStore';
import { authAPI } from '@/api/auth';

export const Header: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user, clearAuth } = useAuthStore();
  const [isLoggingOut, setIsLoggingOut] = React.useState(false);

  const handleLogout = async () => {
    setIsLoggingOut(true);
    try {
      await authAPI.logout();
    } finally {
      clearAuth();
      navigate('/login');
      setIsLoggingOut(false);
    }
  };

  return (
    <header className="flex items-center justify-between px-6 py-4 border-b border-white/10">
      <div></div>

      <div className="flex items-center gap-3">
        <div className="text-right">
          <p className="text-sm font-semibold">{user?.username || 'User'}</p>
          <p className="text-xs text-white/50">{user?.role || 'member'}</p>
        </div>
        <GlassButton
          size="sm"
          variant="ghost"
          onClick={handleLogout}
          loading={isLoggingOut}
          title={t('header.logout')}
        >
          <LogOut className="w-4 h-4" />
        </GlassButton>
      </div>
    </header>
  );
};
