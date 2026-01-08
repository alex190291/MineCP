import apiClient from './client';

export interface FileItem {
  name: string;
  path: string;
  type: 'file' | 'directory';
  size: number;
  modified: number;
  extension?: string;
}

export interface DirectoryListing {
  path: string;
  items: FileItem[];
}

export interface FileContent {
  path: string;
  content: string;
  size: number;
  encoding: string;
}

export const filesAPI = {
  listFiles: async (serverId: string, path: string = ''): Promise<DirectoryListing> => {
    const response = await apiClient.get<DirectoryListing>(
      `/servers/${serverId}/files`,
      { params: { path } }
    );
    return response.data;
  },

  readFile: async (serverId: string, path: string): Promise<FileContent> => {
    const response = await apiClient.get<FileContent>(
      `/servers/${serverId}/files/read`,
      { params: { path } }
    );
    return response.data;
  },

  writeFile: async (serverId: string, path: string, content: string): Promise<void> => {
    await apiClient.post(`/servers/${serverId}/files/write`, { path, content });
  },

  deleteFile: async (serverId: string, path: string): Promise<void> => {
    await apiClient.delete(`/servers/${serverId}/files/delete`, { data: { path } });
  },

  uploadFile: async (serverId: string, file: File, targetPath: string = ''): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);
    if (targetPath) {
      formData.append('path', targetPath);
    }

    const response = await apiClient.post(
      `/servers/${serverId}/files/upload`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  downloadFile: (serverId: string, path: string): string => {
    const token = localStorage.getItem('token');
    const baseURL = apiClient.defaults.baseURL || '/api';
    return `${baseURL}/servers/${serverId}/files/download?path=${encodeURIComponent(path)}&token=${token}`;
  },
};
