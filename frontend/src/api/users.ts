import apiClient from './client';
import { User } from '@/types/user';

export interface CreateUserData {
  username: string;
  email: string;
  role_id: string;  // UUID of role
  password?: string;
  is_ldap_user?: boolean;
  is_active?: boolean;
}

export interface UpdateUserData {
  username?: string;
  email?: string;
  role_id?: string;  // UUID of role
  password?: string;
  is_ldap_user?: boolean;
  is_active?: boolean;
}

export const usersAPI = {
  list: async (): Promise<User[]> => {
    const response = await apiClient.get<User[]>('/users');
    return response.data;
  },

  get: async (id: string): Promise<User> => {
    const response = await apiClient.get<User>(`/users/${id}`);
    return response.data;
  },

  create: async (data: CreateUserData): Promise<User> => {
    const response = await apiClient.post<User>('/users', data);
    return response.data;
  },

  update: async (id: string, data: UpdateUserData): Promise<User> => {
    const response = await apiClient.patch<User>(`/users/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/users/${id}`);
  },
};
