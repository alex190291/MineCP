import apiClient from './client';

export interface Mod {
  id: string;
  server_id: string;
  name: string;
  source: string;
  source_id?: string;
  version?: string;
  file_name: string;
  file_path: string;
  file_size: number;
  enabled: boolean;
  created_at: string;
}

export interface ModSearchResult {
  project_id: string;
  slug: string;
  title: string;
  description: string;
  icon_url?: string;
  downloads: number;
  categories: string[];
}

export const modsAPI = {
  searchMods: async (query: string, version?: string, serverType?: string): Promise<ModSearchResult[]> => {
    const response = await apiClient.get<{ results: ModSearchResult[] }>('/mods/search', {
      params: { query, version, serverType },
    });
    return response.data.results;
  },

  uploadMod: async (file: File): Promise<{ file_name: string; file_path: string }> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<{ file_name: string; file_path: string }>(
      '/mods/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  listServerMods: async (serverId: string): Promise<Mod[]> => {
    const response = await apiClient.get<Mod[]>(`/servers/${serverId}/mods`);
    return response.data;
  },

  installMod: async (
    serverId: string,
    data: {
      mod_name?: string;
      mod_url?: string;
      source?: string;
      source_id?: string;
      version?: string;
      file_path?: string;
    }
  ): Promise<Mod> => {
    const response = await apiClient.post<Mod>(`/servers/${serverId}/mods`, data);
    return response.data;
  },

  deleteMod: async (serverId: string, modId: string): Promise<void> => {
    await apiClient.delete(`/servers/${serverId}/mods/${modId}`);
  },
};
