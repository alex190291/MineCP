import apiClient from './client';

export interface Backup {
  id: string;
  server_id: string;
  name: string;
  size: number;
  backup_path: string;
  type: string;
  compressed: boolean;
  created_at: string;
  created_by: string;
}

export const backupsAPI = {
  listAll: async (): Promise<Backup[]> => {
    const response = await apiClient.get<Backup[]>('/backups');
    return response.data;
  },

  listServerBackups: async (serverId: string): Promise<Backup[]> => {
    const response = await apiClient.get<Backup[]>(`/servers/${serverId}/backups`);
    return response.data;
  },

  createBackup: async (serverId: string, name?: string): Promise<Backup> => {
    const response = await apiClient.post<Backup>(`/servers/${serverId}/backups`, {
      name,
    });
    return response.data;
  },

  restoreBackup: async (backupId: string): Promise<void> => {
    await apiClient.post(`/backups/${backupId}/restore`);
  },

  deleteBackup: async (backupId: string): Promise<void> => {
    await apiClient.delete(`/backups/${backupId}`);
  },

  downloadBackup: async (backupId: string): Promise<void> => {
    const response = await apiClient.get(`/backups/${backupId}/download`, {
      responseType: 'blob',
    });

    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;

    // Extract filename from Content-Disposition header or use default
    const contentDisposition = response.headers['content-disposition'];
    const filename = contentDisposition
      ? contentDisposition.split('filename=')[1]?.replace(/"/g, '')
      : `backup-${backupId}.zip`;

    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};
