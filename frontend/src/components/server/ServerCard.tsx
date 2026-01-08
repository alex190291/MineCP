import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Play, Square, Trash2 } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';

import { Server } from '@/types/server';
import { serversAPI } from '@/api/servers';
import { GlassCard } from '@/components/common/GlassCard';
import { GlassButton } from '@/components/common/GlassButton';
import { StatusBadge } from '@/components/common/StatusBadge';
import { formatBytes } from '@/utils/formatters';

interface ServerCardProps {
  server: Server;
}

export const ServerCard: React.FC<ServerCardProps> = ({ server }) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const startMutation = useMutation({
    mutationFn: () => serversAPI.start(server.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['servers'] });
    },
  });

  const stopMutation = useMutation({
    mutationFn: () => serversAPI.stop(server.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['servers'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => serversAPI.delete(server.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['servers'] });
    },
  });

  const handleAction = (action: () => void, e: React.MouseEvent) => {
    e.stopPropagation();
    action();
  };

  return (
    <GlassCard
      hover
      onClick={() => navigate(`/servers/${server.id}`)}
    >
      <div className="space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-xl font-bold">{server.name}</h3>
            <p className="text-white/60 text-sm">
              {server.type} {server.version}
            </p>
          </div>
          <StatusBadge status={server.status} />
        </div>

        <div className="grid grid-cols-2 gap-4 py-3 border-y border-white/10">
          <div>
            <p className="text-white/60 text-xs">{t('serverCard.memory')}</p>
            <p className="font-semibold">{formatBytes(server.memory_limit * 1024 * 1024)}</p>
          </div>
          <div>
            <p className="text-white/60 text-xs">{t('serverCard.port')}</p>
            <p className="font-semibold">{server.host_port}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {server.status === 'stopped' && (
            <GlassButton
              size="sm"
              variant="primary"
              onClick={(e) => handleAction(() => startMutation.mutate(), e)}
              loading={startMutation.isPending}
            >
              <Play className="w-4 h-4 mr-1" />
              {t('serverCard.start')}
            </GlassButton>
          )}

          {server.status === 'running' && (
            <GlassButton
              size="sm"
              variant="danger"
              onClick={(e) => handleAction(() => stopMutation.mutate(), e)}
              loading={stopMutation.isPending}
            >
              <Square className="w-4 h-4 mr-1" />
              {t('serverCard.stop')}
            </GlassButton>
          )}

          <GlassButton
            size="sm"
            variant="ghost"
            onClick={(e) => handleAction(() => deleteMutation.mutate(), e)}
            loading={deleteMutation.isPending}
            title={t('serverCard.delete')}
          >
            <Trash2 className="w-4 h-4" />
          </GlassButton>
        </div>
      </div>
    </GlassCard>
  );
};
