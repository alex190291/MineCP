import React, { useState, useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { Save, AlertCircle } from 'lucide-react';

import { serversAPI } from '@/api/servers';
import { GlassCard } from '@/components/common/GlassCard';
import { GlassButton } from '@/components/common/GlassButton';
import { GlassInput } from '@/components/common/GlassInput';

interface SettingsTabProps {
  serverId: string;
  serverStatus: string;
  canEdit?: boolean;
}

interface SettingDefinition {
  key: string;
  label: string;
  type: 'text' | 'number' | 'boolean' | 'select';
  description: string;
  options?: { value: string; label: string }[];
  default?: any;
}

const COMMON_SETTINGS: SettingDefinition[] = [
  {
    key: 'difficulty',
    label: 'Difficulty',
    type: 'select',
    description: 'Game difficulty level',
    options: [
      { value: 'peaceful', label: 'Peaceful' },
      { value: 'easy', label: 'Easy' },
      { value: 'normal', label: 'Normal' },
      { value: 'hard', label: 'Hard' },
    ],
    default: 'normal',
  },
  {
    key: 'gamemode',
    label: 'Game Mode',
    type: 'select',
    description: 'Default game mode',
    options: [
      { value: 'survival', label: 'Survival' },
      { value: 'creative', label: 'Creative' },
      { value: 'adventure', label: 'Adventure' },
      { value: 'spectator', label: 'Spectator' },
    ],
    default: 'survival',
  },
  {
    key: 'max-players',
    label: 'Max Players',
    type: 'number',
    description: 'Maximum number of players',
    default: 20,
  },
  {
    key: 'pvp',
    label: 'PvP',
    type: 'boolean',
    description: 'Enable player vs player combat',
    default: true,
  },
  {
    key: 'spawn-protection',
    label: 'Spawn Protection',
    type: 'number',
    description: 'Radius around spawn that is protected',
    default: 16,
  },
  {
    key: 'view-distance',
    label: 'View Distance',
    type: 'number',
    description: 'Server view distance in chunks',
    default: 10,
  },
  {
    key: 'simulation-distance',
    label: 'Simulation Distance',
    type: 'number',
    description: 'Distance from players that entities are updated',
    default: 10,
  },
  {
    key: 'allow-nether',
    label: 'Allow Nether',
    type: 'boolean',
    description: 'Allow players to travel to the Nether',
    default: true,
  },
  {
    key: 'enable-command-block',
    label: 'Enable Command Blocks',
    type: 'boolean',
    description: 'Enable command blocks',
    default: false,
  },
  {
    key: 'spawn-monsters',
    label: 'Spawn Monsters',
    type: 'boolean',
    description: 'Spawn hostile mobs',
    default: true,
  },
  {
    key: 'spawn-animals',
    label: 'Spawn Animals',
    type: 'boolean',
    description: 'Spawn passive mobs',
    default: true,
  },
  {
    key: 'motd',
    label: 'MOTD',
    type: 'text',
    description: 'Message of the day (server description)',
    default: 'A Minecraft Server',
  },
];

export const SettingsTab: React.FC<SettingsTabProps> = ({
  serverId,
  serverStatus,
  canEdit = false,
}) => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [settings, setSettings] = useState<Record<string, any>>({});
  const [hasChanges, setHasChanges] = useState(false);

  const { data: serverSettings, isLoading } = useQuery({
    queryKey: ['server-settings', serverId],
    queryFn: () => serversAPI.getSettings(serverId),
  });

  useEffect(() => {
    if (serverSettings) {
      setSettings(serverSettings);
    }
  }, [serverSettings]);

  const saveMutation = useMutation({
    mutationFn: () => serversAPI.updateSettings(serverId, settings),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['server-settings', serverId] });
      queryClient.invalidateQueries({ queryKey: ['server', serverId] });
      setHasChanges(false);

      if (data.restart_required) {
        alert(t('serverSettings.restartRequired'));
      }
    },
  });

  const handleSettingChange = (key: string, value: any) => {
    if (!canEdit) {
      return;
    }
    setSettings((prev) => ({ ...prev, [key]: value }));
    setHasChanges(true);
  };

  const renderSettingInput = (setting: SettingDefinition) => {
    const value = settings[setting.key] ?? setting.default;

    switch (setting.type) {
      case 'boolean':
        return (
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={value === true || value === 'true'}
              onChange={(e) => handleSettingChange(setting.key, e.target.checked)}
              disabled={!canEdit}
              className="w-4 h-4 rounded border-white/20 bg-white/10 text-blue-500 focus:ring-2 focus:ring-blue-500"
            />
            <span className="text-sm">{t('serverSettings.enabled')}</span>
          </label>
        );

      case 'select':
        return (
          <select
            value={value || setting.default}
            onChange={(e) => handleSettingChange(setting.key, e.target.value)}
            disabled={!canEdit}
            className="w-full px-4 py-2 rounded-lg bg-white/10 border border-white/20 text-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/50 outline-none transition-all"
          >
            {setting.options?.map((option) => (
              <option key={option.value} value={option.value}>
                {t(`serverSettings.${option.value}`)}
              </option>
            ))}
          </select>
        );

      case 'number':
        return (
          <GlassInput
            type="number"
            value={value ?? setting.default}
            onChange={(e) => handleSettingChange(setting.key, parseInt(e.target.value))}
            disabled={!canEdit}
          />
        );

      case 'text':
      default:
        return (
          <GlassInput
            type="text"
            value={value ?? setting.default}
            onChange={(e) => handleSettingChange(setting.key, e.target.value)}
            disabled={!canEdit}
          />
        );
    }
  };

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {serverStatus === 'running' && (
        <GlassCard className="bg-orange-500/10 border-orange-500/20">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-orange-400 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-orange-400">{t('serverSettings.serverIsRunning')}</h4>
              <p className="text-sm text-white/70 mt-1">
                {t('serverSettings.restartWarning')}
              </p>
            </div>
          </div>
        </GlassCard>
      )}

      <GlassCard>
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold">{t('serverSettings.title')}</h3>
          <GlassButton
            variant="primary"
            onClick={() => saveMutation.mutate()}
            loading={saveMutation.isPending}
            disabled={!hasChanges || !canEdit}
          >
            <Save className="w-4 h-4 mr-2" />
            {t('serverSettings.saveChanges')}
          </GlassButton>
        </div>

        <div className="space-y-6">
          {COMMON_SETTINGS.map((setting) => {
            // Convert kebab-case to camelCase: "max-players" -> "maxPlayers"
            const labelKey = setting.key.split('-').map((part, index) =>
              index === 0 ? part : part.charAt(0).toUpperCase() + part.slice(1)
            ).join('');
            return (
              <div key={setting.key}>
                <label className="block text-sm font-medium mb-2">
                  {t(`serverSettings.${labelKey}`)}
                </label>
                <p className="text-xs text-white/60 mb-2">
                  {t(`serverSettings.${labelKey}Desc`)}
                </p>
                {renderSettingInput(setting)}
              </div>
            );
          })}
        </div>
      </GlassCard>

      {hasChanges && canEdit && (
        <div className="fixed bottom-6 right-6 z-50">
          <GlassCard className="bg-blue-500/20 border-blue-500/30">
            <div className="flex items-center gap-3">
              <p className="text-sm font-medium">{t('serverSettings.unsavedChanges')}</p>
              <GlassButton
                size="sm"
                variant="primary"
                onClick={() => saveMutation.mutate()}
                loading={saveMutation.isPending}
              >
                {t('serverSettings.saveNow')}
              </GlassButton>
            </div>
          </GlassCard>
        </div>
      )}
    </div>
  );
};
