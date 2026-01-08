import apiClient from './client';

export interface PlayerInfo {
  username: string;
  minecraft_uuid: string;
  is_online: boolean;
  first_seen: string;
  last_seen: string;
  is_banned: boolean;
  ban_reason?: string;
  is_op: boolean;
}

export const playersAPI = {
  getOnlinePlayers: async (serverId: string): Promise<string[]> => {
    const response = await apiClient.get<{ players: string[] }>(
      `/monitoring/servers/${serverId}/players`
    );
    return response.data.players;
  },

  getAllPlayers: async (serverId: string): Promise<PlayerInfo[]> => {
    const response = await apiClient.get<{ players: PlayerInfo[] }>(
      `/monitoring/servers/${serverId}/players/all`
    );
    return response.data.players;
  },

  banPlayer: async (serverId: string, playerName: string, reason?: string): Promise<void> => {
    await apiClient.post(`/monitoring/servers/${serverId}/players/ban`, {
      player_name: playerName,
      reason,
    });
  },

  unbanPlayer: async (serverId: string, playerName: string): Promise<void> => {
    await apiClient.post(`/monitoring/servers/${serverId}/players/unban`, {
      player_name: playerName,
    });
  },

  opPlayer: async (serverId: string, playerName: string): Promise<void> => {
    await apiClient.post(`/monitoring/servers/${serverId}/players/op`, {
      player_name: playerName,
    });
  },

  deopPlayer: async (serverId: string, playerName: string): Promise<void> => {
    await apiClient.post(`/monitoring/servers/${serverId}/players/deop`, {
      player_name: playerName,
    });
  },

  kickPlayer: async (serverId: string, playerName: string, reason?: string): Promise<void> => {
    await apiClient.post(`/monitoring/servers/${serverId}/players/kick`, {
      player_name: playerName,
      reason,
    });
  },

  getBannedPlayers: async (serverId: string): Promise<string[]> => {
    const response = await apiClient.get<{ banned_players: string[] }>(
      `/monitoring/servers/${serverId}/players/banned`
    );
    return response.data.banned_players;
  },
};
