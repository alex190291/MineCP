import apiClient from './client';
import { User } from '@/types/user';

export const usersAPI = {
  update: async (id: string, data: Partial<User> & { password?: string }): Promise<User> => {
    const response = await apiClient.patch<User>(`/users/${id}`, data);
    return response.data;
  },
};
