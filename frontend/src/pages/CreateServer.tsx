import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { RefreshCw } from 'lucide-react';

import { GlassCard } from '@/components/common/GlassCard';
import { GlassInput } from '@/components/common/GlassInput';
import { GlassButton } from '@/components/common/GlassButton';
import { serversAPI } from '@/api/servers';
import { versionsAPI } from '@/api/versions';
import { DEFAULT_SERVER_PROPERTIES, MINECRAFT_VERSIONS, SERVER_TYPES } from '@/utils/constants';
import { CreateServerData, ServerType } from '@/types/server';
import { useAuthStore } from '@/store/authStore';

interface CreateServerFormData {
  name: string;
  type: ServerType;
  version: string;
  memory_limit: number;
  cpu_limit: number;
  host_port: number;
  max_players: number;
  motd: string;
  java_args?: string;
}

export const CreateServer: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  const [errorMessage, setErrorMessage] = useState('');
  const [availableVersions, setAvailableVersions] = useState<string[]>(MINECRAFT_VERSIONS);
  const [isFetchingVersions, setIsFetchingVersions] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<CreateServerFormData>({
    defaultValues: {
      type: 'paper',
      version: MINECRAFT_VERSIONS[0],
      memory_limit: 2048,
      cpu_limit: 1,
      host_port: 25565,
      max_players: DEFAULT_SERVER_PROPERTIES.max_players,
      motd: DEFAULT_SERVER_PROPERTIES.motd,
    },
  });

  const createMutation = useMutation({
    mutationFn: (data: CreateServerData) => serversAPI.create(data),
    onSuccess: (server) => {
      queryClient.invalidateQueries({ queryKey: ['servers'] });
      navigate(`/servers/${server.id}`);
    },
    onError: (error) => {
      if (axios.isAxiosError(error)) {
        setErrorMessage(error.response?.data?.error || 'Failed to create server');
      } else {
        setErrorMessage('Failed to create server');
      }
    },
  });

  const fetchLatestVersions = async () => {
    setIsFetchingVersions(true);
    try {
      const versions = await versionsAPI.getMinecraftVersions();

      // Merge fetched versions with static ones, removing duplicates
      const allVersions = [...new Set([...versions.all, ...MINECRAFT_VERSIONS])];

      // Sort versions (newest first)
      const sortedVersions = allVersions.sort((a, b) => {
        const aParts = a.split('.').map(Number);
        const bParts = b.split('.').map(Number);

        for (let i = 0; i < Math.max(aParts.length, bParts.length); i++) {
          const aNum = aParts[i] || 0;
          const bNum = bParts[i] || 0;
          if (aNum !== bNum) return bNum - aNum;
        }
        return 0;
      });

      setAvailableVersions(sortedVersions);
    } catch (error) {
      console.error('Failed to fetch versions:', error);
      // Keep using static versions on error
    } finally {
      setIsFetchingVersions(false);
    }
  };

  const onSubmit = (data: CreateServerFormData) => {
    setErrorMessage('');
    const payload: CreateServerData = {
      name: data.name,
      type: data.type,
      version: data.version,
      memory_limit: data.memory_limit,
      cpu_limit: data.cpu_limit,
      host_port: data.host_port,
      java_args: data.java_args || undefined,
      server_properties: {
        ...DEFAULT_SERVER_PROPERTIES,
        max_players: data.max_players,
        motd: data.motd,
      },
    };
    createMutation.mutate(payload);
  };

  if (user?.role !== 'admin') {
    return (
      <div className="p-8">
        <GlassCard className="p-8 text-center">
          <p className="text-white/70">You don't have permission to create servers.</p>
        </GlassCard>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gradient">Create Server</h1>
        <p className="text-white/60 mt-1">Provision a new Minecraft server</p>
      </div>

      <GlassCard>
        <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <GlassInput
              label="Server Name"
              placeholder="Survival Realm"
              {...register('name', { required: 'Server name is required' })}
              error={errors.name?.message}
            />

            <div className="space-y-2">
              <label className="block text-sm font-medium text-white/80">Server Type</label>
              <select
                className="glass-input w-full rounded-lg px-4 py-2.5 text-white"
                {...register('type', { required: 'Server type is required' })}
              >
                {SERVER_TYPES.map((type) => (
                  <option key={type.value} value={type.value} className="text-black">
                    {type.label}
                  </option>
                ))}
              </select>
              {errors.type?.message && (
                <p className="text-sm text-red-400">{errors.type.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="block text-sm font-medium text-white/80">Minecraft Version</label>
                <button
                  type="button"
                  onClick={fetchLatestVersions}
                  disabled={isFetchingVersions}
                  className="text-xs text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1"
                  title="Fetch latest versions from Paper API"
                >
                  <RefreshCw className={`w-3 h-3 ${isFetchingVersions ? 'animate-spin' : ''}`} />
                  {isFetchingVersions ? 'Fetching...' : 'Refresh Versions'}
                </button>
              </div>
              <select
                className="glass-input w-full rounded-lg px-4 py-2.5 text-white"
                {...register('version', { required: 'Version is required' })}
              >
                {availableVersions.map((version) => (
                  <option key={version} value={version} className="text-black">
                    {version}
                  </option>
                ))}
              </select>
              {errors.version?.message && (
                <p className="text-sm text-red-400">{errors.version.message}</p>
              )}
            </div>

            <GlassInput
              label="Memory (MB)"
              type="number"
              {...register('memory_limit', {
                valueAsNumber: true,
                required: 'Memory limit is required',
                min: { value: 512, message: 'Minimum 512MB' },
              })}
              error={errors.memory_limit?.message}
            />

            <GlassInput
              label="CPU Cores"
              type="number"
              step="0.5"
              {...register('cpu_limit', {
                valueAsNumber: true,
                required: 'CPU limit is required',
                min: { value: 0.5, message: 'Minimum 0.5 cores' },
              })}
              error={errors.cpu_limit?.message}
            />

            <GlassInput
              label="Host Port"
              type="number"
              {...register('host_port', {
                valueAsNumber: true,
                required: 'Host port is required',
                min: { value: 1024, message: 'Use a port above 1024' },
              })}
              error={errors.host_port?.message}
            />

            <GlassInput
              label="Max Players"
              type="number"
              {...register('max_players', {
                valueAsNumber: true,
                required: 'Max players is required',
                min: { value: 1, message: 'Minimum 1 player' },
              })}
              error={errors.max_players?.message}
            />

            <GlassInput
              label="MOTD"
              placeholder="Welcome to the server!"
              {...register('motd', { required: 'MOTD is required' })}
              error={errors.motd?.message}
            />

            <GlassInput
              label="Java Args (optional)"
              placeholder="-XX:+UseG1GC"
              {...register('java_args')}
            />
          </div>

          {errorMessage && (
            <p className="text-sm text-red-400">{errorMessage}</p>
          )}

          <div className="flex items-center gap-3">
            <GlassButton type="submit" variant="primary" loading={createMutation.isPending}>
              Create Server
            </GlassButton>
            <GlassButton
              type="button"
              variant="ghost"
              onClick={() => navigate('/')}
            >
              Cancel
            </GlassButton>
          </div>
        </form>
      </GlassCard>
    </div>
  );
};
