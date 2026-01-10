import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Plus, Server as ServerIcon, Users, Activity } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import { serversAPI } from '@/api/servers';
import { GlassCard } from '@/components/common/GlassCard';
import { GlassButton } from '@/components/common/GlassButton';
import { ServerCard } from '@/components/server/ServerCard';
import { useAuthStore } from '@/store/authStore';

export const Dashboard: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user } = useAuthStore();

  const { data: servers, isLoading } = useQuery({
    queryKey: ['servers'],
    queryFn: serversAPI.getAll,
    refetchInterval: 5000,
  });

  const runningServers = servers?.filter((server) => server.status === 'running').length || 0;
  const totalPlayers = 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">{t('dashboard.title')}</h1>
          <p className="text-white/60 mt-1">{t('dashboard.subtitle')}</p>
        </div>

        {user?.role === 'admin' && (
          <GlassButton
            variant="primary"
            onClick={() => navigate('/servers/new')}
          >
            <Plus className="w-5 h-5 mr-2" />
            {t('nav.createServer')}
          </GlassButton>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <GlassCard>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white/60 text-sm">{t('dashboard.totalServers')}</p>
              <p className="text-3xl font-bold mt-1">{servers?.length || 0}</p>
            </div>
            <div className="bg-blue-500/20 p-3 rounded-xl">
              <ServerIcon className="w-8 h-8 text-blue-400" />
            </div>
          </div>
        </GlassCard>

        <GlassCard>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white/60 text-sm">{t('dashboard.running')}</p>
              <p className="text-3xl font-bold mt-1">{runningServers}</p>
            </div>
            <div className="bg-green-500/20 p-3 rounded-xl">
              <Activity className="w-8 h-8 text-green-400" />
            </div>
          </div>
        </GlassCard>

        <GlassCard>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white/60 text-sm">{t('dashboard.onlinePlayers')}</p>
              <p className="text-3xl font-bold mt-1">{totalPlayers}</p>
            </div>
            <div className="bg-purple-500/20 p-3 rounded-xl">
              <Users className="w-8 h-8 text-purple-400" />
            </div>
          </div>
        </GlassCard>
      </div>

      <div>
        <h2 className="text-2xl font-bold mb-4">{t('dashboard.yourServers')}</h2>
        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto" />
          </div>
        ) : servers && servers.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {servers.map((server) => (
              <ServerCard key={server.id} server={server} />
            ))}
          </div>
        ) : (
          <GlassCard>
            <div className="text-center py-12">
              <ServerIcon className="w-16 h-16 text-white/20 mx-auto mb-4" />
              <h3 className="text-xl font-semibold mb-2">{t('dashboard.noServers')}</h3>
              <p className="text-white/60 mb-4">{t('dashboard.noServersDesc')}</p>
              {user?.role === 'admin' && (
                <GlassButton
                  variant="primary"
                  onClick={() => navigate('/servers/new')}
                >
                  <Plus className="w-5 h-5 mr-2" />
                  {t('nav.createServer')}
                </GlassButton>
              )}
            </div>
          </GlassCard>
        )}
      </div>
    </div>
  );
};
