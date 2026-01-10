import apiClient from './client';
import { Server, CreateServerData, ServerMetrics } from '@/types/server';

export const serversAPI = {
  getAll: async (): Promise<Server[]> => {
    const response = await apiClient.get<Server[]>('/servers');
    return response.data;
  },

  getById: async (id: string): Promise<Server> => {
    const response = await apiClient.get<Server>(`/servers/${id}`);
    return response.data;
  },

  create: async (data: CreateServerData): Promise<Server> => {
    const response = await apiClient.post<Server>('/servers', data);
    return response.data;
  },

  update: async (id: string, data: Partial<CreateServerData>): Promise<Server> => {
    const response = await apiClient.patch<Server>(`/servers/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/servers/${id}`);
  },

  start: async (id: string): Promise<void> => {
    await apiClient.post(`/servers/${id}/start`);
  },

  stop: async (id: string): Promise<void> => {
    await apiClient.post(`/servers/${id}/stop`);
  },

  restart: async (id: string): Promise<void> => {
    await apiClient.post(`/servers/${id}/restart`);
  },

  getMetrics: async (id: string): Promise<ServerMetrics> => {
    const response = await apiClient.get<ServerMetrics>(`/monitoring/servers/${id}/metrics`);
    return response.data;
  },

  getMetricsHistory: async (id: string): Promise<ServerMetrics[]> => {
    const response = await apiClient.get<{ history: ServerMetrics[] }>(
      `/monitoring/servers/${id}/metrics/history`
    );
    return response.data.history;
  },

  getPlayers: async (id: string): Promise<string[]> => {
    const response = await apiClient.get<{ players: string[] }>(
      `/monitoring/servers/${id}/players`
    );
    return response.data.players;
  },

  getLogs: async (id: string, tail?: number): Promise<string> => {
    const response = await apiClient.get<{ logs: string }>(`/servers/${id}/logs`, {
      params: { tail },
    });
    return response.data.logs;
  },

  getSettings: async (id: string): Promise<Record<string, any>> => {
    const response = await apiClient.get<Record<string, any>>(`/servers/${id}/settings`);
    return response.data;
  },

  getPermissions: async (id: string): Promise<string[]> => {
    const response = await apiClient.get<{ permissions: string[] }>(`/servers/${id}/permissions`);
    return response.data.permissions;
  },

  updateSettings: async (id: string, settings: Record<string, any>): Promise<{ settings: Record<string, any>; restart_required: boolean }> => {
    const response = await apiClient.put<{ settings: Record<string, any>; restart_required: boolean }>(
      `/servers/${id}/settings`,
      settings
    );
    return response.data;
  },

  sendCommand: async (id: string, command: string): Promise<{ result: string; command: string }> => {
    const response = await apiClient.post<{ result: string; command: string }>(
      `/servers/${id}/command`,
      { command }
    );
    return response.data;
  },
};
