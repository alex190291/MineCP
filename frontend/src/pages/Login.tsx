import React from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import axios from 'axios';

import { GlassCard } from '@/components/common/GlassCard';
import { GlassInput } from '@/components/common/GlassInput';
import { GlassButton } from '@/components/common/GlassButton';
import { authAPI } from '@/api/auth';
import { useAuthStore } from '@/store/authStore';
import { LoginCredentials } from '@/types/user';

export const Login: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { setAuth, isAuthenticated } = useAuthStore();
  const [errorMessage, setErrorMessage] = React.useState('');

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginCredentials>();

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const onSubmit = async (data: LoginCredentials) => {
    setErrorMessage('');
    try {
      const response = await authAPI.login(data);
      setAuth(response.user, response.access_token, response.refresh_token);
      navigate('/');
    } catch (error) {
      if (axios.isAxiosError(error)) {
        setErrorMessage(error.response?.data?.error || t('login.loginFailed'));
      } else {
        setErrorMessage(t('login.loginFailed'));
      }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-lg space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold text-gradient">{t('login.appTitle')}</h1>
          <p className="text-white/60">{t('login.appSubtitle')}</p>
        </div>

        <GlassCard className="space-y-6">
          <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
            <GlassInput
              label={t('login.username')}
              placeholder={t('login.usernamePlaceholder')}
              {...register('username', { required: t('login.usernameRequired') })}
              error={errors.username?.message}
            />
            <GlassInput
              label={t('login.password')}
              type="password"
              placeholder={t('login.passwordPlaceholder')}
              {...register('password', { required: t('login.passwordRequired') })}
              error={errors.password?.message}
            />

            {errorMessage && (
              <p className="text-sm text-red-400">{errorMessage}</p>
            )}

            <GlassButton
              type="submit"
              variant="primary"
              className="w-full"
              loading={isSubmitting}
            >
              {t('login.signIn')}
            </GlassButton>
          </form>
        </GlassCard>
      </div>
    </div>
  );
};
