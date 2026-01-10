import React from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { Database, Download, RotateCcw, Trash2, Plus, Clock } from 'lucide-react';

import { backupsAPI } from '@/api/backups';
import { GlassCard } from '@/components/common/GlassCard';
import { GlassButton } from '@/components/common/GlassButton';
import { formatBytes, formatRelativeTime } from '@/utils/formatters';

interface BackupsTabProps {
  serverId: string;
  serverStatus: string;
  canManage?: boolean;
}

export const BackupsTab: React.FC<BackupsTabProps> = ({
  serverId,
  serverStatus,
  canManage = false,
}) => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  const { data: backups, isLoading } = useQuery({
    queryKey: ['server-backups', serverId],
    queryFn: () => backupsAPI.listServerBackups(serverId),
  });

  const createMutation = useMutation({
    mutationFn: () => backupsAPI.createBackup(serverId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['server-backups', serverId] });
    },
  });

  const restoreMutation = useMutation({
    mutationFn: (backupId: string) => backupsAPI.restoreBackup(backupId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['server-backups', serverId] });
      alert(t('backups.restoreSuccess'));
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (backupId: string) => backupsAPI.deleteBackup(backupId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['server-backups', serverId] });
    },
  });

  const downloadMutation = useMutation({
    mutationFn: (backupId: string) => backupsAPI.downloadBackup(backupId),
  });

  const handleCreateBackup = () => {
    if (serverStatus !== 'running') {
      alert(t('backups.serverMustBeRunning'));
      return;
    }
    createMutation.mutate();
  };

  const handleRestore = (backupId: string, backupName: string) => {
    if (serverStatus === 'running') {
      alert(t('backups.stopServerToRestore'));
      return;
    }

    if (window.confirm(t('backups.confirmRestore', { name: backupName }))) {
      restoreMutation.mutate(backupId);
    }
  };

  const handleDelete = (backupId: string, backupName: string) => {
    if (window.confirm(t('backups.confirmDelete', { name: backupName }))) {
      deleteMutation.mutate(backupId);
    }
  };

  return (
    <div className="space-y-6">
      {/* Create Backup Section */}
      <GlassCard>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">{t('backups.createBackup')}</h3>
            <p className="text-sm text-white/60 mt-1">
              {serverStatus === 'running'
                ? t('backups.createBackupDesc')
                : t('backups.serverMustBeRunning')}
            </p>
          </div>
          <GlassButton
            variant="primary"
            onClick={handleCreateBackup}
            loading={createMutation.isPending}
            disabled={serverStatus !== 'running' || createMutation.isPending || !canManage}
          >
            <Plus className="w-4 h-4 mr-2" />
            {t('backups.createBackup')}
          </GlassButton>
        </div>
      </GlassCard>

      {/* Restore Info */}
      {serverStatus === 'running' && (
        <GlassCard className="bg-orange-500/10 border-orange-500/20">
          <div className="flex items-start gap-3">
            <RotateCcw className="w-5 h-5 text-orange-400 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-orange-400">{t('backups.serverIsRunning')}</h4>
              <p className="text-sm text-white/70 mt-1">
                {t('backups.stopServerWarning')}
              </p>
            </div>
          </div>
        </GlassCard>
      )}

      {/* Backups List */}
      <GlassCard>
        <h3 className="text-lg font-semibold mb-4">{t('backups.backupHistory')}</h3>

        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto" />
          </div>
        ) : backups && backups.length > 0 ? (
          <div className="space-y-2">
            {backups.map((backup) => (
              <div
                key={backup.id}
                className="p-4 rounded-lg bg-white/5 flex items-center justify-between"
              >
                <div className="flex items-center gap-3 flex-1">
                  <div className="bg-green-500/20 p-2 rounded-lg">
                    <Database className="w-5 h-5 text-green-400" />
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold">{backup.name}</h4>
                    <div className="flex gap-4 text-xs text-white/60 mt-1">
                      <span className="flex items-center gap-1">
                        <Database className="w-3 h-3" />
                        {formatBytes(backup.size)}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatRelativeTime(backup.created_at)}
                      </span>
                      <span className="capitalize">{backup.type}</span>
                      {backup.compressed && <span>{t('backups.compressed')}</span>}
                    </div>
                  </div>
                </div>

                <div className="flex gap-2">
                  <GlassButton
                    size="sm"
                    variant="ghost"
                    onClick={() => downloadMutation.mutate(backup.id)}
                    loading={downloadMutation.isPending}
                    title={t('backups.actions.download')}
                  >
                    <Download className="w-4 h-4" />
                  </GlassButton>

                  {canManage && (
                    <GlassButton
                      size="sm"
                      variant="secondary"
                      onClick={() => handleRestore(backup.id, backup.name)}
                      loading={restoreMutation.isPending}
                      disabled={serverStatus === 'running'}
                      title={t('backups.actions.restore')}
                    >
                      <RotateCcw className="w-4 h-4" />
                    </GlassButton>
                  )}

                  {canManage && (
                    <GlassButton
                      size="sm"
                      variant="danger"
                      onClick={() => handleDelete(backup.id, backup.name)}
                      loading={deleteMutation.isPending}
                      title={t('backups.actions.delete')}
                    >
                      <Trash2 className="w-4 h-4" />
                    </GlassButton>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <Database className="w-16 h-16 text-white/20 mx-auto mb-4" />
            <h3 className="text-xl font-semibold mb-2">{t('backups.noBackups')}</h3>
            <p className="text-white/60">{t('backups.noBackupsDesc')}</p>
          </div>
        )}
      </GlassCard>

      {/* Backup Info */}
      <GlassCard className="bg-blue-500/10 border-blue-500/20">
        <h4 className="font-semibold mb-2">{t('backups.aboutBackups.title')}</h4>
        <div className="space-y-2 text-sm text-white/70">
          <p>{t('backups.aboutBackups.desc1')}</p>
          <p>{t('backups.aboutBackups.desc2')}</p>
          <p>{t('backups.aboutBackups.desc3')}</p>
          <p>{t('backups.aboutBackups.desc4')}</p>
        </div>
      </GlassCard>
    </div>
  );
};
