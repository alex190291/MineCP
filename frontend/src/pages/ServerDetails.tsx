import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import {
  Play,
  Square,
  RotateCw,
  Trash2,
  Settings,
  Package,
  Users,
  Database,
  Terminal,
  BarChart3,
  FolderOpen,
} from 'lucide-react';

import { serversAPI } from '@/api/servers';
import { GlassCard } from '@/components/common/GlassCard';
import { GlassButton } from '@/components/common/GlassButton';
import { StatusBadge } from '@/components/common/StatusBadge';
import { Tabs } from '@/components/common/Tabs';
import { ModsTab } from '@/components/server/ModsTab';
import { SettingsTab } from '@/components/server/SettingsTab';
import { PlayersTab } from '@/components/server/PlayersTab';
import { BackupsTab } from '@/components/server/BackupsTab';
import { ConsoleTab } from '@/components/server/ConsoleTab';
import { FilesTab } from '@/components/server/FilesTab';
import { formatBytes, formatPercent, formatRelativeTime } from '@/utils/formatters';

export const ServerDetails: React.FC = () => {
  const { t } = useTranslation();
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const {
    data: server,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ['server', id],
    queryFn: () => serversAPI.getById(id as string),
    enabled: !!id,
  });

  const metricsQuery = useQuery({
    queryKey: ['server-metrics', id],
    queryFn: () => serversAPI.getMetrics(id as string),
    enabled: !!id && server?.status === 'running',
    refetchInterval: 5000,
  });

  const startMutation = useMutation({
    mutationFn: () => serversAPI.start(id as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['servers'] });
      queryClient.invalidateQueries({ queryKey: ['server', id] });
    },
  });

  const stopMutation = useMutation({
    mutationFn: () => serversAPI.stop(id as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['servers'] });
      queryClient.invalidateQueries({ queryKey: ['server', id] });
    },
  });

  const restartMutation = useMutation({
    mutationFn: () => serversAPI.restart(id as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['servers'] });
      queryClient.invalidateQueries({ queryKey: ['server', id] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => serversAPI.delete(id as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['servers'] });
      navigate('/');
    },
  });

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto" />
      </div>
    );
  }

  if (isError || !server) {
    return (
      <GlassCard>
        <p className="text-white/70">Server not found.</p>
      </GlassCard>
    );
  }

  const metrics = metricsQuery.data;

  const handleDelete = () => {
    if (window.confirm(t('serverDetails.deleteConfirm'))) {
      deleteMutation.mutate();
    }
  };

  const tabs = [
    { id: 'overview', label: t('serverDetails.overview'), icon: <BarChart3 className="w-4 h-4" /> },
    { id: 'settings', label: t('nav.settings'), icon: <Settings className="w-4 h-4" /> },
    { id: 'mods', label: t('serverDetails.mods'), icon: <Package className="w-4 h-4" /> },
    { id: 'players', label: t('serverDetails.players'), icon: <Users className="w-4 h-4" /> },
    { id: 'backups', label: t('serverDetails.backups'), icon: <Database className="w-4 h-4" /> },
    { id: 'console', label: t('serverDetails.console'), icon: <Terminal className="w-4 h-4" /> },
    { id: 'files', label: t('serverDetails.files'), icon: <FolderOpen className="w-4 h-4" /> },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gradient">{server.name}</h1>
          <p className="text-white/60 mt-1">
            {server.type} {server.version} - Port {server.host_port}
          </p>
        </div>
        <StatusBadge status={server.status} />
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-2">
        {server.status === 'stopped' && (
          <GlassButton
            variant="primary"
            onClick={() => startMutation.mutate()}
            loading={startMutation.isPending}
          >
            <Play className="w-4 h-4 mr-2" />
            {t('serverDetails.start')}
          </GlassButton>
        )}
        {server.status === 'running' && (
          <GlassButton
            variant="danger"
            onClick={() => stopMutation.mutate()}
            loading={stopMutation.isPending}
            disabled={!server.container_id}
          >
            <Square className="w-4 h-4 mr-2" />
            {t('serverDetails.stop')}
          </GlassButton>
        )}
        <GlassButton
          variant="secondary"
          onClick={() => restartMutation.mutate()}
          loading={restartMutation.isPending}
          disabled={!server.container_id}
        >
          <RotateCw className="w-4 h-4 mr-2" />
          {t('serverDetails.restart')}
        </GlassButton>
        <GlassButton variant="ghost" onClick={handleDelete} loading={deleteMutation.isPending}>
          <Trash2 className="w-4 h-4 mr-2" />
          {t('serverDetails.deleteServer')}
        </GlassButton>
      </div>

      {/* Tabs */}
      <Tabs tabs={tabs} defaultTab="overview">
        {(activeTab) => {
          switch (activeTab) {
            case 'overview':
              return (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <GlassCard>
                      <h3 className="text-lg font-semibold mb-4">{t('serverDetails.configuration')}</h3>
                      <div className="space-y-2 text-sm text-white/70">
                        <div className="flex justify-between">
                          <span>{t('serverDetails.memory')}</span>
                          <span className="text-white">
                            {formatBytes(server.memory_limit * 1024 * 1024)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>{t('serverDetails.cpu')}</span>
                          <span className="text-white">{server.cpu_limit} {t('serverDetails.cores')}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>{t('serverDetails.created')}</span>
                          <span className="text-white">{formatRelativeTime(server.created_at)}</span>
                        </div>
                      </div>
                    </GlassCard>

                    <GlassCard className="lg:col-span-2">
                      <h3 className="text-lg font-semibold mb-4">{t('serverDetails.liveMetrics')}</h3>
                      {server.status !== 'running' ? (
                        <p className="text-white/60">{t('serverDetails.startServerToSeeMetrics')}</p>
                      ) : metrics ? (
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <div className="p-4 rounded-xl bg-white/5">
                            <p className="text-xs text-white/60">{t('serverDetails.cpu')}</p>
                            <p className="text-2xl font-semibold">
                              {formatPercent(metrics.cpu_percent)}
                            </p>
                          </div>
                          <div className="p-4 rounded-xl bg-white/5">
                            <p className="text-xs text-white/60">{t('serverDetails.memory')}</p>
                            <p className="text-2xl font-semibold">
                              {formatBytes(metrics.memory_usage)} / {formatBytes(metrics.memory_limit)}
                            </p>
                          </div>
                          <div className="p-4 rounded-xl bg-white/5">
                            <p className="text-xs text-white/60">{t('serverDetails.players')}</p>
                            <p className="text-2xl font-semibold">{metrics.online_players}</p>
                          </div>
                        </div>
                      ) : (
                        <p className="text-white/60">{t('serverDetails.waitingForMetrics')}</p>
                      )}
                    </GlassCard>
                  </div>
                </div>
              );

            case 'settings':
              return <SettingsTab serverId={id as string} serverStatus={server.status} />;

            case 'mods':
              return <ModsTab serverId={id as string} />;

            case 'players':
              return <PlayersTab serverId={id as string} serverStatus={server.status} />;

            case 'backups':
              return <BackupsTab serverId={id as string} serverStatus={server.status} />;

            case 'console':
              return <ConsoleTab serverId={id as string} serverStatus={server.status} />;

            case 'files':
              return <FilesTab serverId={id as string} />;

            default:
              return null;
          }
        }}
      </Tabs>
    </div>
  );
};
