import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { Trash2, Edit2, UserPlus, X } from 'lucide-react';
import axios from 'axios';

import { GlassCard } from '@/components/common/GlassCard';
import { GlassInput } from '@/components/common/GlassInput';
import { GlassButton } from '@/components/common/GlassButton';
import { ConfirmModal } from '@/components/common/ConfirmModal';
import { usersAPI, CreateUserData, UpdateUserData } from '@/api/users';
import { User } from '@/types/user';
import { useAuthStore } from '@/store/authStore';
import { formatDate } from '@/utils/formatters';

interface UserFormData {
  username: string;
  email: string;
  role: 'admin' | 'user';
  password?: string;
  is_ldap_user: boolean;
  is_active: boolean;
}

export const UserManagement: React.FC = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const { user: currentUser } = useAuthStore();
  const [isCreating, setIsCreating] = React.useState(false);
  const [editingUser, setEditingUser] = React.useState<User | null>(null);
  const [message, setMessage] = React.useState('');
  const [messageType, setMessageType] = React.useState<'success' | 'error'>('success');
  const [deleteConfirmUser, setDeleteConfirmUser] = React.useState<User | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<UserFormData>({
    defaultValues: {
      username: '',
      email: '',
      role: 'user',
      password: '',
      is_ldap_user: false,
      is_active: true,
    },
  });

  const { data: users, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: usersAPI.list,
  });

  const createMutation = useMutation({
    mutationFn: (data: CreateUserData) => usersAPI.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setMessage(t('users.success.created'));
      setMessageType('success');
      setIsCreating(false);
      reset();
    },
    onError: (error) => {
      if (axios.isAxiosError(error)) {
        setMessage(error.response?.data?.error || t('users.error.create'));
      } else {
        setMessage(t('users.error.create'));
      }
      setMessageType('error');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateUserData }) =>
      usersAPI.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setMessage(t('users.success.updated'));
      setMessageType('success');
      setEditingUser(null);
      reset();
    },
    onError: (error) => {
      if (axios.isAxiosError(error)) {
        setMessage(error.response?.data?.error || t('users.error.update'));
      } else {
        setMessage(t('users.error.update'));
      }
      setMessageType('error');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => usersAPI.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setMessage(t('users.success.deleted'));
      setMessageType('success');
    },
    onError: (error) => {
      if (axios.isAxiosError(error)) {
        setMessage(error.response?.data?.error || t('users.error.delete'));
      } else {
        setMessage(t('users.error.delete'));
      }
      setMessageType('error');
    },
  });

  const handleCreateClick = () => {
    setIsCreating(true);
    setEditingUser(null);
    reset({
      username: '',
      email: '',
      role: 'user',
      password: '',
      is_ldap_user: false,
      is_active: true,
    });
    setMessage('');
  };

  const handleEditClick = (user: User) => {
    setEditingUser(user);
    setIsCreating(false);
    reset({
      username: user.username,
      email: user.email,
      role: user.role,
      password: '',
      is_ldap_user: user.is_ldap_user,
      is_active: user.is_active,
    });
    setMessage('');
  };

  const handleCancel = () => {
    setIsCreating(false);
    setEditingUser(null);
    reset();
    setMessage('');
  };

  const handleDeleteClick = (user: User) => {
    if (user.id === currentUser?.id) {
      setMessage(t('users.cannotDeleteSelf'));
      setMessageType('error');
      return;
    }

    setDeleteConfirmUser(user);
  };

  const handleConfirmDelete = () => {
    if (deleteConfirmUser) {
      deleteMutation.mutate(deleteConfirmUser.id);
      setDeleteConfirmUser(null);
    }
  };

  const onSubmit = (data: UserFormData) => {
    setMessage('');

    if (editingUser) {
      if (editingUser.is_ldap_user) {
        setMessage('Cannot edit LDAP users');
        setMessageType('error');
        return;
      }

      const updateData: UpdateUserData = {
        username: data.username,
        email: data.email,
        role: data.role,
        is_active: data.is_active,
      };

      if (data.password && data.password.trim()) {
        updateData.password = data.password;
      }

      updateMutation.mutate({ id: editingUser.id, data: updateData });
    } else {
      if (!data.password || !data.password.trim()) {
        setMessage(t('users.form.passwordRequired'));
        setMessageType('error');
        return;
      }

      const createData: CreateUserData = {
        username: data.username,
        email: data.email,
        role: data.role,
        password: data.password,
        is_ldap_user: false,
        is_active: data.is_active,
      };

      createMutation.mutate(createData);
    }
  };

  const isAdmin = currentUser?.role === 'admin';

  if (!isAdmin) {
    return (
      <div className="p-8">
        <GlassCard className="p-8 text-center">
          <p className="text-white/70">You don't have permission to access this page.</p>
        </GlassCard>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">{t('users.title')}</h1>
            <p className="text-white/60 mt-1">{t('users.subtitle')}</p>
          </div>
          {!isCreating && !editingUser && (
            <GlassButton onClick={handleCreateClick}>
              <UserPlus className="w-4 h-4" />
              {t('users.createUser')}
            </GlassButton>
          )}
        </div>

        {message && (
          <GlassCard
            className={`p-4 ${
              messageType === 'success'
                ? 'bg-green-500/10 border-green-500/30'
                : 'bg-red-500/10 border-red-500/30'
            }`}
          >
            <p
              className={`text-sm ${
                messageType === 'success' ? 'text-green-200' : 'text-red-200'
              }`}
            >
              {message}
            </p>
          </GlassCard>
        )}

        {(isCreating || editingUser) && (
          <GlassCard className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-white">
                {editingUser ? t('users.editUser') : t('users.createNewUser')}
              </h2>
              <button
                onClick={handleCancel}
                className="text-white/60 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-white/80 mb-2">
                    {t('users.username')}
                  </label>
                  <GlassInput
                    {...register('username', { required: t('users.form.usernameRequired') })}
                    type="text"
                    placeholder={t('users.username')}
                  />
                  {errors.username && (
                    <p className="text-red-400 text-sm mt-1">{errors.username.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-white/80 mb-2">
                    {t('users.email')}
                  </label>
                  <GlassInput
                    {...register('email', {
                      required: t('users.form.emailRequired'),
                      pattern: {
                        value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                        message: t('users.form.emailInvalid'),
                      },
                    })}
                    type="email"
                    placeholder={t('users.email')}
                  />
                  {errors.email && (
                    <p className="text-red-400 text-sm mt-1">{errors.email.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-white/80 mb-2">
                    {t('users.role')}
                  </label>
                  <select
                    {...register('role', { required: t('users.form.roleRequired') })}
                    className="w-full px-4 py-2 rounded-xl bg-white/10 border border-white/20 text-white backdrop-blur-xl focus:outline-none focus:ring-2 focus:ring-white/30"
                  >
                    <option value="user">{t('users.user')}</option>
                    <option value="admin">{t('users.admin')}</option>
                  </select>
                  {errors.role && (
                    <p className="text-red-400 text-sm mt-1">{errors.role.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-white/80 mb-2">
                    {t('users.password')}
                  </label>
                  <GlassInput
                    {...register('password')}
                    type="password"
                    placeholder={
                      editingUser
                        ? t('users.passwordOptional')
                        : t('users.passwordRequired')
                    }
                  />
                  {errors.password && (
                    <p className="text-red-400 text-sm mt-1">{errors.password.message}</p>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-6">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    {...register('is_active')}
                    type="checkbox"
                    className="w-4 h-4 rounded bg-white/10 border-white/20 text-blue-500 focus:ring-2 focus:ring-white/30"
                  />
                  <span className="text-sm text-white/80">{t('users.active')}</span>
                </label>
                <p className="text-xs text-white/50">
                  Note: LDAP users are managed through your LDAP server and cannot be created here.
                </p>
              </div>

              <div className="flex gap-3 pt-4">
                <GlassButton type="submit" disabled={isSubmitting}>
                  {isSubmitting ? t('common.loading') : t('common.save')}
                </GlassButton>
                <GlassButton type="button" onClick={handleCancel} variant="secondary">
                  {t('common.cancel')}
                </GlassButton>
              </div>
            </form>
          </GlassCard>
        )}

        <GlassCard className="p-6">
          <h2 className="text-xl font-semibold text-white mb-4">{t('users.allUsers')}</h2>

          {isLoading ? (
            <div className="text-center py-8">
              <p className="text-white/60">{t('common.loading')}</p>
            </div>
          ) : !users || users.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-white/60">{t('users.noUsers')}</p>
              <p className="text-white/40 text-sm mt-1">{t('users.noUsersDesc')}</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/10">
                    <th className="text-left py-3 px-4 text-sm font-medium text-white/80">
                      {t('users.username')}
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-white/80">
                      {t('users.email')}
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-white/80">
                      {t('users.role')}
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-white/80">
                      {t('users.type')}
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-white/80">
                      {t('users.status')}
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-white/80">
                      {t('users.lastLogin')}
                    </th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-white/80">
                      {t('users.actions')}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {users?.map((user: User) => (
                    <tr key={user.id} className="border-b border-white/5 hover:bg-white/5">
                      <td className="py-3 px-4 text-sm text-white">{user.username}</td>
                      <td className="py-3 px-4 text-sm text-white/70">{user.email}</td>
                      <td className="py-3 px-4 text-sm">
                        <span
                          className={`inline-flex items-center px-2 py-1 rounded-full text-xs ${
                            user.role === 'admin'
                              ? 'bg-purple-500/20 text-purple-200'
                              : 'bg-blue-500/20 text-blue-200'
                          }`}
                        >
                          {t(`users.${user.role}`)}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm text-white/70">
                        {user.is_ldap_user ? t('users.ldapUser') : t('users.localUser')}
                      </td>
                      <td className="py-3 px-4 text-sm">
                        <span
                          className={`inline-flex items-center px-2 py-1 rounded-full text-xs ${
                            user.is_active
                              ? 'bg-green-500/20 text-green-200'
                              : 'bg-gray-500/20 text-gray-200'
                          }`}
                        >
                          {user.is_active ? t('users.active') : t('users.inactive')}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm text-white/70">
                        {user.last_login
                          ? formatDate(user.last_login)
                          : t('users.neverLoggedIn')}
                      </td>
                      <td className="py-3 px-4 text-sm text-right">
                        <div className="flex items-center justify-end gap-2">
                          {user.is_ldap_user ? (
                            <span className="text-xs text-white/40 px-2">LDAP (read-only)</span>
                          ) : (
                            <>
                              <button
                                onClick={() => handleEditClick(user)}
                                className="p-2 rounded-lg hover:bg-white/10 text-white/70 hover:text-white transition-colors"
                                title={t('common.edit')}
                              >
                                <Edit2 className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleDeleteClick(user)}
                                className="p-2 rounded-lg hover:bg-red-500/20 text-white/70 hover:text-red-200 transition-colors"
                                title={t('common.delete')}
                                disabled={user.id === currentUser?.id}
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </GlassCard>

        <ConfirmModal
          isOpen={deleteConfirmUser !== null}
          onClose={() => setDeleteConfirmUser(null)}
          onConfirm={handleConfirmDelete}
          title={t('common.delete')}
          message={
            deleteConfirmUser
              ? t('users.confirmDelete', { username: deleteConfirmUser.username })
              : ''
          }
          confirmText={t('common.delete')}
          cancelText={t('common.cancel')}
          confirmVariant="danger"
        />
      </div>
    </div>
  );
};
