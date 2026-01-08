import apiClient from './client';
import { LDAPConfig, LDAPTestPayload } from '@/types/ldap';

export const ldapAPI = {
  getConfig: async (): Promise<LDAPConfig> => {
    const response = await apiClient.get<LDAPConfig>('/ldap');
    return response.data;
  },

  updateConfig: async (data: Partial<LDAPConfig>): Promise<LDAPConfig> => {
    const response = await apiClient.put<LDAPConfig>('/ldap', data);
    return response.data;
  },

  testConnection: async (data: LDAPTestPayload): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>('/ldap/test', data);
    return response.data;
  },
};
