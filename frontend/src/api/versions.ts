import apiClient from './client';

export interface MinecraftVersions {
  vanilla: string[];
  paper: string[];
  forge: string[];
  fabric: string[];
  all: string[];
}

export const versionsAPI = {
  getMinecraftVersions: async (): Promise<MinecraftVersions> => {
    const response = await apiClient.get<MinecraftVersions>('/versions/minecraft');
    return response.data;
  },
};
