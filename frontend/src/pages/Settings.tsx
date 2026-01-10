import React from 'react';
import { useForm } from 'react-hook-form';
import { useMutation, useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { Palette, Languages } from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { GlassCard } from '@/components/common/GlassCard';
import { GlassInput } from '@/components/common/GlassInput';
import { GlassButton } from '@/components/common/GlassButton';
import { useAuthStore } from '@/store/authStore';
import { usersAPI } from '@/api/users';
import { ldapAPI } from '@/api/ldap';
import { LDAPConfig } from '@/types/ldap';
import { colorPresets, applyColorPreset, loadSavedColorPreset } from '@/utils/colorPresets';

interface AccountFormData {
  username: string;
  email: string;
  password?: string;
}

interface LDAPFormData {
  enabled: boolean;
  server_uri: string;
  bind_dn: string;
  bind_password: string;
  user_search_base: string;
  user_search_filter: string;
  group_search_base: string;
  group_search_filter: string;
}

const languageOptions = [
  { code: 'en', name: 'English', flag: '🇬🇧' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
  { code: 'it', name: 'Italiano', flag: '🇮🇹' },
];

export const Settings: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { user, updateUser, setRequirePasswordChange } = useAuthStore();
  const [accountMessage, setAccountMessage] = React.useState('');
  const [ldapMessage, setLdapMessage] = React.useState('');
  const [selectedPreset, setSelectedPreset] = React.useState(0);

  const {
    register: registerAccount,
    handleSubmit: handleAccountSubmit,
    reset: resetAccount,
    formState: { errors: accountErrors, isSubmitting: accountSubmitting },
  } = useForm<AccountFormData>();

  React.useEffect(() => {
    if (user) {
      resetAccount({
        username: user.username,
        email: user.email,
      });
    }
  }, [user, resetAccount]);

  const accountMutation = useMutation({
    mutationFn: (data: AccountFormData) => usersAPI.update(user?.id || '', data),
    onSuccess: (updated, variables) => {
      updateUser(updated);
      if (variables.password && variables.password.trim()) {
        setRequirePasswordChange(false);
      }
      setAccountMessage('Account updated successfully.');
    },
    onError: (error) => {
      if (axios.isAxiosError(error)) {
        setAccountMessage(error.response?.data?.error || 'Failed to update account.');
      } else {
        setAccountMessage('Failed to update account.');
      }
    },
  });

  const onAccountSubmit = (data: AccountFormData) => {
    setAccountMessage('');
    if (!user) {
      setAccountMessage('No authenticated user.');
      return;
    }
    const payload: AccountFormData = {
      username: data.username,
      email: data.email,
    };
    if (data.password && data.password.trim()) {
      payload.password = data.password;
    }
    accountMutation.mutate(payload);
  };

  const isAdmin = user?.role === 'admin';

  const ldapQuery = useQuery({
    queryKey: ['ldap-config'],
    queryFn: ldapAPI.getConfig,
    enabled: isAdmin,
  });

  const {
    register: registerLdap,
    handleSubmit: handleLdapSubmit,
    reset: resetLdap,
    formState: { errors: ldapErrors, isSubmitting: ldapSubmitting },
  } = useForm<LDAPFormData>({
    defaultValues: {
      enabled: false,
      server_uri: '',
      bind_dn: '',
      bind_password: '',
      user_search_base: '',
      user_search_filter: '',
      group_search_base: '',
      group_search_filter: '',
    },
  });

  React.useEffect(() => {
    if (ldapQuery.data) {
      const config = ldapQuery.data;
      resetLdap({
        enabled: config.enabled ?? false,
        server_uri: config.server_uri || '',
        bind_dn: config.bind_dn || '',
        bind_password: '',
        user_search_base: config.user_search_base || '',
        user_search_filter: config.user_search_filter || '',
        group_search_base: config.group_search_base || '',
        group_search_filter: config.group_search_filter || '',
      });
    }
  }, [ldapQuery.data, resetLdap]);

  const ldapUpdateMutation = useMutation({
    mutationFn: (data: Partial<LDAPConfig>) => ldapAPI.updateConfig(data),
    onSuccess: () => {
      setLdapMessage('LDAP settings saved.');
    },
    onError: (error) => {
      if (axios.isAxiosError(error)) {
        setLdapMessage(error.response?.data?.error || 'Failed to save LDAP settings.');
      } else {
        setLdapMessage('Failed to save LDAP settings.');
      }
    },
  });

  const ldapTestMutation = useMutation({
    mutationFn: (data: { server_uri: string; bind_dn: string; bind_password: string }) =>
      ldapAPI.testConnection(data),
    onSuccess: (response) => {
      setLdapMessage(response.message);
    },
    onError: (error) => {
      if (axios.isAxiosError(error)) {
        setLdapMessage(error.response?.data?.error || 'LDAP test failed.');
      } else {
        setLdapMessage('LDAP test failed.');
      }
    },
  });

  const onLdapSubmit = (data: LDAPFormData) => {
    setLdapMessage('');
    ldapUpdateMutation.mutate({
      enabled: data.enabled,
      server_uri: data.server_uri || null,
      bind_dn: data.bind_dn || null,
      bind_password: data.bind_password || null,
      user_search_base: data.user_search_base || null,
      user_search_filter: data.user_search_filter || null,
      group_search_base: data.group_search_base || null,
      group_search_filter: data.group_search_filter || null,
    });
  };

  const handleLdapTest = (data: LDAPFormData) => {
    setLdapMessage('');
    ldapTestMutation.mutate({
      server_uri: data.server_uri,
      bind_dn: data.bind_dn,
      bind_password: data.bind_password,
    });
  };

  const handleColorPresetChange = (presetIndex: number) => {
    setSelectedPreset(presetIndex);
    applyColorPreset(presetIndex);
  };

  const handleLanguageChange = (langCode: string) => {
    i18n.changeLanguage(langCode);
  };

  // Load saved color preset on mount to set the selected state
  React.useEffect(() => {
    const savedPresetIndex = loadSavedColorPreset();
    setSelectedPreset(savedPresetIndex);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gradient">{t('settings.title')}</h1>
        <p className="text-white/60 mt-1">{t('settings.subtitle')}</p>
      </div>

      <GlassCard>
        <h2 className="text-xl font-semibold mb-4">{t('settings.account.title')}</h2>
        <form className="space-y-4" onSubmit={handleAccountSubmit(onAccountSubmit)}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <GlassInput
              label={t('settings.account.username')}
              {...registerAccount('username', { required: 'Username is required' })}
              error={accountErrors.username?.message}
            />
            <GlassInput
              label={t('settings.account.email')}
              type="email"
              {...registerAccount('email', { required: 'Email is required' })}
              error={accountErrors.email?.message}
            />
          </div>
          <GlassInput
            label={t('settings.account.newPassword')}
            type="password"
            placeholder="********"
            {...registerAccount('password')}
          />
          {accountMessage && (
            <p className="text-sm text-white/70">{accountMessage}</p>
          )}
          <GlassButton type="submit" variant="primary" loading={accountSubmitting}>
            {t('settings.account.save')}
          </GlassButton>
        </form>
      </GlassCard>

      <GlassCard>
        <div className="flex items-center gap-2 mb-4">
          <Palette className="w-5 h-5 text-blue-400" />
          <h2 className="text-xl font-semibold">{t('settings.appearance.title')}</h2>
        </div>
        <p className="text-white/60 text-sm mb-6">{t('settings.appearance.subtitle')}</p>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {colorPresets.map((preset, index) => (
            <button
              key={preset.name}
              onClick={() => handleColorPresetChange(index)}
              className={`
                group relative p-4 rounded-xl transition-all
                ${selectedPreset === index
                  ? 'ring-2 ring-blue-400 bg-white/10'
                  : 'hover:bg-white/5 hover:scale-105'
                }
              `}
            >
              <div className="flex items-center gap-3">
                <div
                  className="w-12 h-12 rounded-lg"
                  style={{
                    background: `linear-gradient(-45deg, ${preset.colors.join(', ')})`,
                    backgroundSize: '200% 200%',
                  }}
                />
                <div className="text-left">
                  <p className="font-medium text-sm">{preset.name}</p>
                  {selectedPreset === index && (
                    <p className="text-xs text-blue-400">{t('settings.appearance.active')}</p>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>
      </GlassCard>

      <GlassCard>
        <div className="flex items-center gap-2 mb-4">
          <Languages className="w-5 h-5 text-blue-400" />
          <h2 className="text-xl font-semibold">{t('settings.language.title')}</h2>
        </div>
        <p className="text-white/60 text-sm mb-6">{t('settings.language.subtitle')}</p>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {languageOptions.map((lang) => (
            <button
              key={lang.code}
              onClick={() => handleLanguageChange(lang.code)}
              className={`
                group relative p-4 rounded-xl transition-all
                ${i18n.language === lang.code
                  ? 'ring-2 ring-blue-400 bg-white/10'
                  : 'hover:bg-white/5 hover:scale-105'
                }
              `}
            >
              <div className="flex items-center gap-3">
                <span className="text-3xl">{lang.flag}</span>
                <div className="text-left">
                  <p className="font-medium text-sm">{lang.name}</p>
                  {i18n.language === lang.code && (
                    <p className="text-xs text-blue-400">{t('settings.appearance.active')}</p>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>
      </GlassCard>

      <GlassCard>
        <h2 className="text-xl font-semibold mb-4">{t('settings.ldap.title')}</h2>
        {!isAdmin && (
          <p className="text-white/60">{t('settings.ldap.adminOnly')}</p>
        )}
        {isAdmin && (
          <>
            {ldapQuery.isLoading ? (
              <div className="text-center py-6">
                <div className="animate-spin w-6 h-6 border-4 border-blue-500 border-t-transparent rounded-full mx-auto" />
              </div>
            ) : (
              <form className="space-y-4" onSubmit={handleLdapSubmit(onLdapSubmit)}>
                <label className="flex items-center gap-2 text-sm text-white/70">
                  <input type="checkbox" className="accent-blue-500" {...registerLdap('enabled')} />
                  {t('settings.ldap.enable')}
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <GlassInput
                    label={t('settings.ldap.serverUri')}
                    placeholder="ldap://ldap.example.com"
                    {...registerLdap('server_uri')}
                    error={ldapErrors.server_uri?.message}
                  />
                  <GlassInput
                    label={t('settings.ldap.bindDn')}
                    placeholder="cn=admin,dc=example,dc=com"
                    {...registerLdap('bind_dn')}
                    error={ldapErrors.bind_dn?.message}
                  />
                  <GlassInput
                    label={t('settings.ldap.bindPassword')}
                    type="password"
                    placeholder="********"
                    {...registerLdap('bind_password')}
                    error={ldapErrors.bind_password?.message}
                  />
                  <GlassInput
                    label={t('settings.ldap.userSearchBase')}
                    placeholder="ou=users,dc=example,dc=com"
                    {...registerLdap('user_search_base')}
                  />
                  <GlassInput
                    label={t('settings.ldap.loginFilter')}
                    placeholder="(uid={username})"
                    {...registerLdap('user_search_filter')}
                  />
                  <GlassInput
                    label={t('settings.ldap.groupSearchBase')}
                    placeholder="ou=groups,dc=example,dc=com"
                    {...registerLdap('group_search_base')}
                  />
                  <GlassInput
                    label={t('settings.ldap.groupSearchFilter')}
                    placeholder="(member={userdn})"
                    {...registerLdap('group_search_filter')}
                  />
                </div>
                {ldapMessage && (
                  <p className="text-sm text-white/70">{ldapMessage}</p>
                )}
                <div className="flex flex-wrap gap-2">
                  <GlassButton type="submit" variant="primary" loading={ldapSubmitting}>
                    {t('settings.ldap.save')}
                  </GlassButton>
                  <GlassButton
                    type="button"
                    variant="ghost"
                    onClick={handleLdapSubmit(handleLdapTest)}
                    loading={ldapTestMutation.isPending}
                  >
                    {t('settings.ldap.test')}
                  </GlassButton>
                </div>
              </form>
            )}
          </>
        )}
      </GlassCard>
    </div>
  );
};
