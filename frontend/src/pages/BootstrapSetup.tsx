import React from 'react';
import { useForm } from 'react-hook-form';
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';

import { GlassCard } from '@/components/common/GlassCard';
import { GlassInput } from '@/components/common/GlassInput';
import { GlassButton } from '@/components/common/GlassButton';
import { usersAPI } from '@/api/users';
import { useAuthStore } from '@/store/authStore';
import { useNavigate } from 'react-router-dom';

interface AdminSetupFormData {
  username: string;
  email: string;
  password: string;
}

export const BootstrapSetup: React.FC = () => {
  const navigate = useNavigate();
  const { clearAuth } = useAuthStore();
  const [message, setMessage] = React.useState('');
  const [messageType, setMessageType] = React.useState<'success' | 'error'>('success');

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<AdminSetupFormData>();

  const createAdminMutation = useMutation({
    mutationFn: (data: AdminSetupFormData) =>
      usersAPI.create({
        username: data.username,
        email: data.email,
        role_id: 'admin',  // Backend will convert 'admin' name to role_id
        password: data.password,
        is_ldap_user: false,
        is_active: true,
      }),
    onSuccess: async () => {
      setMessage('Admin account created. Please sign in with the new credentials.');
      setMessageType('success');
      // Bootstrap user is automatically deleted on the backend
      // Clear local session and redirect to login
      clearAuth();
      navigate('/login', { replace: true });
    },
    onError: (error) => {
      if (axios.isAxiosError(error)) {
        const serverError = error.response?.data?.error;
        const status = error.response?.status;
        const details = status ? ` (HTTP ${status})` : '';
        setMessage((serverError || error.message || 'Failed to create admin account.') + details);
      } else {
        setMessage('Failed to create admin account.');
      }
      setMessageType('error');
    },
  });

  const onSubmit = (data: AdminSetupFormData) => {
    setMessage('');
    createAdminMutation.mutate(data);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-lg space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold text-gradient">Create Admin Account</h1>
          <p className="text-white/60">
            You must create an admin account to continue. This will log you out of setup.
          </p>
        </div>

        <GlassCard className="space-y-6">
          <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
            <GlassInput
              label="Username"
              placeholder="admin"
              {...register('username', { required: 'Username is required' })}
              error={errors.username?.message}
            />
            <GlassInput
              label="Email"
              type="email"
              placeholder="admin@example.com"
              {...register('email', {
                required: 'Email is required',
                pattern: {
                  value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                  message: 'Enter a valid email address',
                },
              })}
              error={errors.email?.message}
            />
            <GlassInput
              label="Password"
              type="password"
              placeholder="Strong password"
              {...register('password', {
                required: 'Password is required',
                minLength: {
                  value: 12,
                  message: 'Password must be at least 12 characters',
                },
                validate: (value) => {
                  const hasUpper = /[A-Z]/.test(value);
                  const hasLower = /[a-z]/.test(value);
                  const hasDigit = /\d/.test(value);
                  const hasSpecial = /[!@#$%^&*()_+\-=[\]{}|;:,.<>?]/.test(value);
                  if (!hasUpper) return 'Password must include an uppercase letter';
                  if (!hasLower) return 'Password must include a lowercase letter';
                  if (!hasDigit) return 'Password must include a number';
                  if (!hasSpecial) return 'Password must include a special character';
                  return true;
                },
              })}
              error={errors.password?.message}
            />

            <p className="text-xs text-white/50">
              After creation, you will be redirected to the login page.
              Username and email must be unique. Password must be 12+ chars with upper/lower/number/special.
            </p>

            {message && (
              <p
                className={`text-sm ${
                  messageType === 'success' ? 'text-green-300' : 'text-red-400'
                }`}
              >
                {message}
              </p>
            )}

            <GlassButton
              type="submit"
              variant="primary"
              className="w-full"
              loading={isSubmitting}
            >
              Create Admin
            </GlassButton>
          </form>
        </GlassCard>
      </div>
    </div>
  );
};
