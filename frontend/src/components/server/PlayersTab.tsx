import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { Users, Ban, Shield, UserX, RefreshCw } from 'lucide-react';

import { playersAPI, PlayerInfo } from '@/api/players';
import { GlassCard } from '@/components/common/GlassCard';
import { GlassButton } from '@/components/common/GlassButton';

interface PlayersTabProps {
  serverId: string;
  serverStatus: string;
}

export const PlayersTab: React.FC<PlayersTabProps> = ({ serverId, serverStatus }) => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [selectedPlayer, setSelectedPlayer] = useState<string | null>(null);

  const { data: players, isLoading, refetch } = useQuery<PlayerInfo[]>({
    queryKey: ['server-all-players', serverId],
    queryFn: () => playersAPI.getAllPlayers(serverId),
    refetchInterval: 5000,
  });

  const { data: bannedPlayers, isLoading: bannedLoading, refetch: refetchBanned } = useQuery({
    queryKey: ['server-banned-players', serverId],
    queryFn: () => playersAPI.getBannedPlayers(serverId),
    enabled: serverStatus === 'running',
    refetchInterval: serverStatus === 'running' ? 10000 : false,
  });

  const banMutation = useMutation({
    mutationFn: (playerName: string) => playersAPI.banPlayer(serverId, playerName, 'Banned by admin'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['server-all-players', serverId] });
      queryClient.invalidateQueries({ queryKey: ['server-banned-players', serverId] });
      setSelectedPlayer(null);
    },
    onError: (error: any) => {
      console.error('Ban error:', error);
      alert(`Failed to ban player: ${error?.response?.data?.error || error.message}`);
    },
  });

  const unbanMutation = useMutation({
    mutationFn: (playerName: string) => playersAPI.unbanPlayer(serverId, playerName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['server-banned-players', serverId] });
      queryClient.invalidateQueries({ queryKey: ['server-all-players', serverId] });
      setSelectedPlayer(null);
    },
    onError: (error: any) => {
      console.error('Unban error:', error);
      alert(`Failed to unban player: ${error?.response?.data?.error || error.message}`);
    },
  });

  const opMutation = useMutation({
    mutationFn: (playerName: string) => playersAPI.opPlayer(serverId, playerName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['server-all-players', serverId] });
      setSelectedPlayer(null);
    },
    onError: (error: any) => {
      console.error('OP error:', error);
      alert(`Failed to give OP: ${error?.response?.data?.error || error.message}`);
    },
  });

  const deopMutation = useMutation({
    mutationFn: (playerName: string) => playersAPI.deopPlayer(serverId, playerName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['server-all-players', serverId] });
      setSelectedPlayer(null);
    },
    onError: (error: any) => {
      console.error('De-OP error:', error);
      alert(`Failed to remove OP: ${error?.response?.data?.error || error.message}`);
    },
  });

  const kickMutation = useMutation({
    mutationFn: (playerName: string) => playersAPI.kickPlayer(serverId, playerName, 'Kicked by admin'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['server-all-players', serverId] });
      setSelectedPlayer(null);
    },
    onError: (error: any) => {
      console.error('Kick error:', error);
      alert(`Failed to kick player: ${error?.response?.data?.error || error.message}`);
    },
  });

  const handleAction = (action: () => void, playerName: string, confirmKey: string) => {
    if (window.confirm(t(confirmKey, { name: playerName }))) {
      action();
    }
  };

  const handleRefresh = async () => {
    queryClient.invalidateQueries({ queryKey: ['server-all-players', serverId] });
    await refetch();
  };

  const handleRefreshBanned = async () => {
    queryClient.invalidateQueries({ queryKey: ['server-banned-players', serverId] });
    await refetchBanned();
  };

  const onlinePlayers = players?.filter(p => p.is_online && !p.is_banned) || [];
  const offlinePlayers = players?.filter(p => !p.is_online && !p.is_banned) || [];
  const allNonBannedPlayers = players?.filter(p => !p.is_banned) || [];

  return (
    <div className="space-y-6">
      <GlassCard>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold">{t('players.title')}</h3>
            <p className="text-sm text-white/60 mt-1">
              {t('players.stats', {
                online: onlinePlayers.length,
                offline: offlinePlayers.length,
                total: allNonBannedPlayers.length
              })}
            </p>
          </div>
          <GlassButton
            size="sm"
            variant="ghost"
            onClick={handleRefresh}
            disabled={isLoading}
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </GlassButton>
        </div>

        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto" />
          </div>
        ) : allNonBannedPlayers.length > 0 ? (
          <div className="space-y-2">
            {allNonBannedPlayers.map((player) => (
              <div
                key={player.username}
                className="p-4 rounded-lg bg-white/5 flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${player.is_online ? 'bg-green-500/20' : 'bg-gray-500/20'}`}>
                    <Users className={`w-5 h-5 ${player.is_online ? 'text-green-400' : 'text-gray-400'}`} />
                  </div>
                  <div>
                    <h4 className="font-semibold">{player.username}</h4>
                    <p className={`text-xs ${player.is_online ? 'text-green-400' : 'text-gray-400'}`}>
                      {player.is_online ? t('players.online') : t('players.offline')}
                    </p>
                  </div>
                </div>

                <div className="flex gap-2">
                  <GlassButton
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      setSelectedPlayer(player.username);
                      if (player.is_op) {
                        handleAction(() => deopMutation.mutate(player.username), player.username, 'players.confirmDeop');
                      } else {
                        handleAction(() => opMutation.mutate(player.username), player.username, 'players.confirmOp');
                      }
                    }}
                    loading={(opMutation.isPending || deopMutation.isPending) && selectedPlayer === player.username}
                    title={player.is_op ? t('players.actions.deop') : t('players.actions.op')}
                    className={player.is_op ? 'text-green-400 shadow-[0_0_10px_rgba(74,222,128,0.3)]' : ''}
                  >
                    <Shield className={`w-4 h-4 ${player.is_op ? 'fill-green-400' : ''}`} />
                  </GlassButton>

                  {player.is_online && (
                    <GlassButton
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        setSelectedPlayer(player.username);
                        handleAction(() => kickMutation.mutate(player.username), player.username, 'players.confirmKick');
                      }}
                      loading={kickMutation.isPending && selectedPlayer === player.username}
                      title={t('players.actions.kick')}
                    >
                      <UserX className="w-4 h-4" />
                    </GlassButton>
                  )}

                  <GlassButton
                    size="sm"
                    variant="danger"
                    onClick={() => {
                      setSelectedPlayer(player.username);
                      handleAction(() => banMutation.mutate(player.username), player.username, 'players.confirmBan');
                    }}
                    loading={banMutation.isPending && selectedPlayer === player.username}
                    title={t('players.actions.ban')}
                  >
                    <Ban className="w-4 h-4" />
                  </GlassButton>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <Users className="w-16 h-16 text-white/20 mx-auto mb-4" />
            <h3 className="text-xl font-semibold mb-2">{t('players.noPlayers')}</h3>
            <p className="text-white/60">{t('players.noPlayersDesc')}</p>
          </div>
        )}
      </GlassCard>

      {/* Banned Players Section */}
      <GlassCard>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold">{t('players.bannedPlayers')}</h3>
            <p className="text-sm text-white/60 mt-1">
              {t('players.bannedCount', { count: bannedPlayers?.length || 0 })}
            </p>
          </div>
          <GlassButton
            size="sm"
            variant="ghost"
            onClick={handleRefreshBanned}
            disabled={bannedLoading}
          >
            <RefreshCw className={`w-4 h-4 ${bannedLoading ? 'animate-spin' : ''}`} />
          </GlassButton>
        </div>

        {bannedLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto" />
          </div>
        ) : bannedPlayers && bannedPlayers.length > 0 ? (
          <div className="space-y-2">
            {bannedPlayers.map((playerName) => (
              <div
                key={playerName}
                className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <div className="bg-red-500/20 p-2 rounded-lg">
                    <Ban className="w-5 h-5 text-red-400" />
                  </div>
                  <div>
                    <h4 className="font-semibold">{playerName}</h4>
                    <p className="text-xs text-red-400">{t('players.banned')}</p>
                  </div>
                </div>

                <GlassButton
                  size="sm"
                  variant="primary"
                  onClick={() => {
                    setSelectedPlayer(playerName);
                    handleAction(() => unbanMutation.mutate(playerName), playerName, 'players.confirmUnban');
                  }}
                  loading={unbanMutation.isPending && selectedPlayer === playerName}
                  title={t('players.actions.unbanPlayer')}
                >
                  {t('players.actions.unban')}
                </GlassButton>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <Ban className="w-16 h-16 text-white/20 mx-auto mb-4" />
            <h3 className="text-xl font-semibold mb-2">{t('players.noBanned')}</h3>
            <p className="text-white/60">{t('players.noBannedDesc')}</p>
          </div>
        )}
      </GlassCard>

      {/* Player Management Info */}
      <GlassCard className="bg-blue-500/10 border-blue-500/20">
        <h4 className="font-semibold mb-2">{t('players.management.title')}</h4>
        <div className="space-y-2 text-sm text-white/70">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-green-400 fill-green-400" />
            <span>{t('players.management.opToggle')}</span>
          </div>
          <div className="flex items-center gap-2">
            <UserX className="w-4 h-4 text-orange-400" />
            <span>{t('players.management.kick')}</span>
          </div>
          <div className="flex items-center gap-2">
            <Ban className="w-4 h-4 text-red-400" />
            <span>{t('players.management.ban')}</span>
          </div>
        </div>
      </GlassCard>
    </div>
  );
};
