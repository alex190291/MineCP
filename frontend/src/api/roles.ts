import apiClient from './client';
import { Role, Permission, ServerRoleAssignment, LdapGroup, LdapGroupAssignment } from '@/types/roles';

export const rolesAPI = {
  listRoles: async (): Promise<Role[]> => {
    const response = await apiClient.get<Role[]>('/roles');
    return response.data;
  },

  listPermissions: async (): Promise<Permission[]> => {
    const response = await apiClient.get<Permission[]>('/permissions');
    return response.data;
  },

  createRole: async (data: { name: string; description?: string; permissions: string[] }): Promise<Role> => {
    const response = await apiClient.post<Role>('/roles', data);
    return response.data;
  },

  updateRole: async (
    id: string,
    data: { name?: string; description?: string; permissions?: string[] }
  ): Promise<Role> => {
    const response = await apiClient.patch<Role>(`/roles/${id}`, data);
    return response.data;
  },

  deleteRole: async (id: string): Promise<void> => {
    await apiClient.delete(`/roles/${id}`);
  },

  listServerAssignments: async (serverId: string): Promise<ServerRoleAssignment[]> => {
    const response = await apiClient.get<ServerRoleAssignment[]>(
      `/servers/${serverId}/assignments`
    );
    return response.data;
  },

  saveServerAssignment: async (serverId: string, user_id: string, role_id: string): Promise<void> => {
    await apiClient.post(`/servers/${serverId}/assignments`, { user_id, role_id });
  },

  removeServerAssignment: async (serverId: string, userId: string): Promise<void> => {
    await apiClient.delete(`/servers/${serverId}/assignments/${userId}`);
  },

  listLdapGroups: async (): Promise<LdapGroup[]> => {
    const response = await apiClient.get<LdapGroup[]>('/ldap/groups');
    return response.data;
  },

  listGroupAssignments: async (serverId: string): Promise<LdapGroupAssignment[]> => {
    const response = await apiClient.get<LdapGroupAssignment[]>(
      `/servers/${serverId}/group-assignments`
    );
    return response.data;
  },

  saveGroupAssignment: async (
    serverId: string,
    group_dn: string,
    group_name: string,
    role_id: string
  ): Promise<void> => {
    await apiClient.post(`/servers/${serverId}/group-assignments`, {
      group_dn,
      group_name,
      role_id,
    });
  },

  removeGroupAssignment: async (serverId: string, group_dn: string): Promise<void> => {
    await apiClient.delete(`/servers/${serverId}/group-assignments`, {
      params: { group_dn },
    });
  },
};
