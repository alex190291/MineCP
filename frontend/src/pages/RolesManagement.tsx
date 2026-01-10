import React from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';

import { rolesAPI } from '@/api/roles';
import { serversAPI } from '@/api/servers';
import { GlassCard } from '@/components/common/GlassCard';
import { GlassButton } from '@/components/common/GlassButton';
import { Role, Permission, LdapGroup, LdapGroupAssignment } from '@/types/roles';
import { useAuthStore } from '@/store/authStore';

export const RolesManagement: React.FC = () => {
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  const [selectedRoleId, setSelectedRoleId] = React.useState<string>('');
  const [selectedServerId, setSelectedServerId] = React.useState<string>('');
  const [message, setMessage] = React.useState('');
  const [messageType, setMessageType] = React.useState<'success' | 'error'>('success');

  const rolesQuery = useQuery({
    queryKey: ['roles'],
    queryFn: rolesAPI.listRoles,
    enabled: user?.role === 'admin',
  });

  const permissionsQuery = useQuery({
    queryKey: ['permissions'],
    queryFn: rolesAPI.listPermissions,
    enabled: user?.role === 'admin',
  });

  const serversQuery = useQuery({
    queryKey: ['servers'],
    queryFn: serversAPI.getAll,
    enabled: user?.role === 'admin',
  });

  const ldapGroupsQuery = useQuery({
    queryKey: ['ldap-groups'],
    queryFn: rolesAPI.listLdapGroups,
    enabled: user?.role === 'admin',
  });

  const groupAssignmentsQuery = useQuery({
    queryKey: ['group-assignments', selectedServerId],
    queryFn: () => rolesAPI.listGroupAssignments(selectedServerId),
    enabled: user?.role === 'admin' && !!selectedServerId,
  });

  React.useEffect(() => {
    if (!selectedRoleId && rolesQuery.data?.length) {
      setSelectedRoleId(rolesQuery.data[0].id);
    }
  }, [rolesQuery.data, selectedRoleId]);

  React.useEffect(() => {
    if (!selectedServerId && serversQuery.data?.length) {
      setSelectedServerId(serversQuery.data[0].id);
    }
  }, [serversQuery.data, selectedServerId]);

  const createMutation = useMutation({
    mutationFn: (data: { name: string; description?: string; permissions: string[] }) =>
      rolesAPI.createRole(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] });
      setMessage('Role created.');
      setMessageType('success');
    },
    onError: (error) => {
      if (axios.isAxiosError(error)) {
        setMessage(error.response?.data?.error || 'Failed to create role.');
      } else {
        setMessage('Failed to create role.');
      }
      setMessageType('error');
    },
  });

  const updateMutation = useMutation({
    mutationFn: (payload: { id: string; data: { name?: string; description?: string; permissions?: string[] } }) =>
      rolesAPI.updateRole(payload.id, payload.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] });
      setMessage('Role updated.');
      setMessageType('success');
    },
    onError: (error) => {
      if (axios.isAxiosError(error)) {
        setMessage(error.response?.data?.error || 'Failed to update role.');
      } else {
        setMessage('Failed to update role.');
      }
      setMessageType('error');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => rolesAPI.deleteRole(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] });
      setSelectedRoleId('');
      setMessage('Role deleted.');
      setMessageType('success');
    },
    onError: (error) => {
      if (axios.isAxiosError(error)) {
        setMessage(error.response?.data?.error || 'Failed to delete role.');
      } else {
        setMessage('Failed to delete role.');
      }
      setMessageType('error');
    },
  });

  if (user?.role !== 'admin') {
    return (
      <div className="p-8">
        <GlassCard className="p-8 text-center">
          <p className="text-white/70">You don't have permission to manage roles.</p>
        </GlassCard>
      </div>
    );
  }

  const roles = rolesQuery.data || [];
  const permissions = permissionsQuery.data || [];
  const servers = serversQuery.data || [];
  const ldapGroups = ldapGroupsQuery.data || [];
  const groupAssignments = groupAssignmentsQuery.data || [];
  const selectedRole = roles.find((role) => role.id === selectedRoleId);

  const assignmentForGroup = (group: LdapGroup): LdapGroupAssignment | undefined =>
    groupAssignments.find((assignment) => assignment.group_dn === group.dn);

  const saveGroupAssignment = useMutation({
    mutationFn: (payload: { group: LdapGroup; roleId: string }) =>
      rolesAPI.saveGroupAssignment(
        selectedServerId,
        payload.group.dn,
        payload.group.name,
        payload.roleId
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['group-assignments', selectedServerId] });
      setMessage('LDAP group access updated.');
      setMessageType('success');
    },
    onError: (error) => {
      if (axios.isAxiosError(error)) {
        setMessage(error.response?.data?.error || 'Failed to update LDAP group access.');
      } else {
        setMessage('Failed to update LDAP group access.');
      }
      setMessageType('error');
    },
  });

  const removeGroupAssignment = useMutation({
    mutationFn: (groupDn: string) => rolesAPI.removeGroupAssignment(selectedServerId, groupDn),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['group-assignments', selectedServerId] });
      setMessage('LDAP group access removed.');
      setMessageType('success');
    },
    onError: (error) => {
      if (axios.isAxiosError(error)) {
        setMessage(error.response?.data?.error || 'Failed to remove LDAP group access.');
      } else {
        setMessage('Failed to remove LDAP group access.');
      }
      setMessageType('error');
    },
  });

  const handleGroupRoleChange = (group: LdapGroup, roleId: string) => {
    setMessage('');
    if (!roleId) {
      removeGroupAssignment.mutate(group.dn);
      return;
    }
    saveGroupAssignment.mutate({ group, roleId });
  };

  const handleCreate = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const name = String(formData.get('name') || '').trim();
    const description = String(formData.get('description') || '').trim();
    if (!name) {
      setMessage('Role name is required.');
      setMessageType('error');
      return;
    }
    createMutation.mutate({
      name,
      description: description || undefined,
      permissions: [],
    });
    event.currentTarget.reset();
  };

  const handlePermissionToggle = (permissionName: string, checked: boolean) => {
    if (!selectedRole) return;
    const current = new Set(selectedRole.permissions || []);
    if (checked) {
      current.add(permissionName);
    } else {
      current.delete(permissionName);
    }
    updateMutation.mutate({
      id: selectedRole.id,
      data: { permissions: Array.from(current) },
    });
  };

  const handleRoleUpdate = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedRole) return;
    const formData = new FormData(event.currentTarget);
    const name = String(formData.get('name') || '').trim();
    const description = String(formData.get('description') || '').trim();
    updateMutation.mutate({
      id: selectedRole.id,
      data: {
        name: name || selectedRole.name,
        description: description || undefined,
      },
    });
  };

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Roles</h1>
        <p className="text-white/60 mt-1">Create roles and define server permissions.</p>
      </div>

      {message && (
        <GlassCard
          className={`p-4 ${
            messageType === 'success'
              ? 'bg-green-500/10 border-green-500/30'
              : 'bg-red-500/10 border-red-500/30'
          }`}
        >
          <p
            className={`text-sm ${
              messageType === 'success' ? 'text-green-200' : 'text-red-200'
            }`}
          >
            {message}
          </p>
        </GlassCard>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <GlassCard className="p-6 space-y-4">
          <h2 className="text-xl font-semibold text-white">Create Role</h2>
          <form className="space-y-3" onSubmit={handleCreate}>
            <input
              name="name"
              placeholder="Role name"
              className="w-full px-3 py-2 rounded-lg bg-white/10 border border-white/20 text-white"
            />
            <input
              name="description"
              placeholder="Short description"
              className="w-full px-3 py-2 rounded-lg bg-white/10 border border-white/20 text-white"
            />
            <GlassButton type="submit" variant="primary">
              Create Role
            </GlassButton>
          </form>
        </GlassCard>

        <GlassCard className="p-6 space-y-3">
          <h2 className="text-xl font-semibold text-white">Roles</h2>
          <div className="space-y-2">
            {roles.map((role: Role) => (
              <button
                key={role.id}
                onClick={() => setSelectedRoleId(role.id)}
                className={`w-full text-left px-3 py-2 rounded-lg border ${
                  selectedRoleId === role.id
                    ? 'bg-white/15 border-white/30 text-white'
                    : 'bg-white/5 border-white/10 text-white/70 hover:bg-white/10'
                }`}
              >
                <div className="text-sm font-semibold">{role.name}</div>
                {role.description && (
                  <div className="text-xs text-white/50">{role.description}</div>
                )}
              </button>
            ))}
          </div>
        </GlassCard>

        <GlassCard className="p-6 space-y-4">
          <h2 className="text-xl font-semibold text-white">Role Details</h2>
          {!selectedRole ? (
            <p className="text-white/60">Select a role to edit.</p>
          ) : (
            <div className="space-y-4">
              <form key={selectedRole.id} className="space-y-3" onSubmit={handleRoleUpdate}>
                <input
                  name="name"
                  defaultValue={selectedRole.name}
                  className="w-full px-3 py-2 rounded-lg bg-white/10 border border-white/20 text-white"
                />
                <input
                  name="description"
                  defaultValue={selectedRole.description || ''}
                  className="w-full px-3 py-2 rounded-lg bg-white/10 border border-white/20 text-white"
                />
                <GlassButton type="submit" variant="secondary">
                  Update Role
                </GlassButton>
              </form>

              <div>
                <h3 className="text-sm font-semibold text-white mb-2">Permissions</h3>
                <div className="space-y-2 max-h-64 overflow-y-auto pr-2">
                  {permissions.map((permission: Permission) => {
                    const checked = selectedRole.permissions.includes(permission.name);
                    return (
                      <label key={permission.id} className="flex items-center gap-2 text-sm text-white/80">
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={(event) =>
                            handlePermissionToggle(permission.name, event.target.checked)
                          }
                        />
                        <span>{permission.name}</span>
                      </label>
                    );
                  })}
                </div>
              </div>

              {!selectedRole.is_system && (
                <GlassButton
                  variant="danger"
                  onClick={() => deleteMutation.mutate(selectedRole.id)}
                >
                  Delete Role
                </GlassButton>
              )}
              {selectedRole.is_system && (
                <p className="text-xs text-white/50">System roles cannot be deleted.</p>
              )}
            </div>
          )}
        </GlassCard>
      </div>

      <GlassCard className="p-6 space-y-4">
        <h2 className="text-xl font-semibold text-white">LDAP Group Access</h2>
        {!ldapGroupsQuery.isSuccess ? (
          <p className="text-white/60">LDAP is not configured or no groups are available.</p>
        ) : (
          <>
            <div className="flex items-center gap-3">
              <label className="text-sm text-white/70">Server</label>
              <select
                className="px-3 py-2 rounded-lg bg-white/10 border border-white/20 text-white"
                value={selectedServerId}
                onChange={(event) => setSelectedServerId(event.target.value)}
              >
                {servers.map((server) => (
                  <option key={server.id} value={server.id} className="text-black">
                    {server.name}
                  </option>
                ))}
              </select>
            </div>

            {groupAssignmentsQuery.isLoading ? (
              <p className="text-white/60">Loading group assignments...</p>
            ) : (
              <div className="space-y-3">
                {ldapGroups.length === 0 && (
                  <p className="text-white/60">No LDAP groups found.</p>
                )}
                {ldapGroups.map((group) => {
                  const assignment = assignmentForGroup(group);
                  return (
                    <div key={group.dn} className="flex items-center justify-between gap-4">
                      <div>
                        <p className="text-white">{group.name}</p>
                        <p className="text-xs text-white/40">{group.dn}</p>
                      </div>
                      <select
                        className="px-3 py-2 rounded-lg bg-white/10 border border-white/20 text-white"
                        value={assignment?.role_id || ''}
                        onChange={(event) => handleGroupRoleChange(group, event.target.value)}
                        disabled={!selectedServerId}
                      >
                        <option value="">No access</option>
                        {roles.map((role) => (
                          <option key={role.id} value={role.id} className="text-black">
                            {role.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  );
                })}
              </div>
            )}
          </>
        )}
      </GlassCard>
    </div>
  );
};
