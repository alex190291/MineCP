import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';

import { rolesAPI } from '@/api/roles';
import { usersAPI } from '@/api/users';
import { GlassCard } from '@/components/common/GlassCard';
import { GlassButton } from '@/components/common/GlassButton';
import { User } from '@/types/user';
import { Role } from '@/types/roles';

interface AccessTabProps {
  serverId: string;
}

export const AccessTab: React.FC<AccessTabProps> = ({ serverId }) => {
  const queryClient = useQueryClient();
  const [message, setMessage] = React.useState('');
  const [messageType, setMessageType] = React.useState<'success' | 'error'>('success');

  const rolesQuery = useQuery({
    queryKey: ['roles'],
    queryFn: rolesAPI.listRoles,
  });

  const usersQuery = useQuery({
    queryKey: ['users'],
    queryFn: usersAPI.list,
  });

  const assignmentsQuery = useQuery({
    queryKey: ['server-assignments', serverId],
    queryFn: () => rolesAPI.listServerAssignments(serverId),
  });

  const saveAssignment = useMutation({
    mutationFn: ({ userId, roleId }: { userId: string; roleId: string }) =>
      rolesAPI.saveServerAssignment(serverId, userId, roleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['server-assignments', serverId] });
      setMessage('Access updated.');
      setMessageType('success');
    },
    onError: (error) => {
      if (axios.isAxiosError(error)) {
        setMessage(error.response?.data?.error || 'Failed to update access.');
      } else {
        setMessage('Failed to update access.');
      }
      setMessageType('error');
    },
  });

  const removeAssignment = useMutation({
    mutationFn: (userId: string) => rolesAPI.removeServerAssignment(serverId, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['server-assignments', serverId] });
      setMessage('Access removed.');
      setMessageType('success');
    },
    onError: (error) => {
      if (axios.isAxiosError(error)) {
        setMessage(error.response?.data?.error || 'Failed to remove access.');
      } else {
        setMessage('Failed to remove access.');
      }
      setMessageType('error');
    },
  });

  const assignments = assignmentsQuery.data || [];
  const roles = rolesQuery.data || [];
  const users = (usersQuery.data || []).filter((user) => user.role !== 'bootstrap');

  const assignmentFor = (userId: string) =>
    assignments.find((assignment) => assignment.user_id === userId);

  const handleChange = (user: User, roleId: string) => {
    setMessage('');
    if (!roleId) {
      removeAssignment.mutate(user.id);
      return;
    }
    saveAssignment.mutate({ userId: user.id, roleId });
  };

  if (rolesQuery.isLoading || usersQuery.isLoading || assignmentsQuery.isLoading) {
    return (
      <div className="text-center py-8">
        <p className="text-white/60">Loading access roles...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
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

      <GlassCard className="p-6">
        <h3 className="text-lg font-semibold mb-4">Server Access</h3>
        <div className="space-y-3">
          {users.map((user) => {
            const assignment = assignmentFor(user.id);
            const selectedRole = assignment?.role_id || '';
            const isGlobalAdmin = user.role === 'admin';

            return (
              <div key={user.id} className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-white">{user.username}</p>
                  <p className="text-xs text-white/50">{user.email}</p>
                </div>
                {isGlobalAdmin ? (
                  <div className="text-xs text-white/60">Global admin</div>
                ) : (
                  <select
                    className="px-3 py-2 rounded-lg bg-white/10 border border-white/20 text-white"
                    value={selectedRole}
                    onChange={(event) => handleChange(user, event.target.value)}
                  >
                    <option value="">No access</option>
                    {roles.map((role: Role) => (
                      <option key={role.id} value={role.id} className="text-black">
                        {role.name}
                      </option>
                    ))}
                  </select>
                )}
              </div>
            );
          })}
        </div>
      </GlassCard>

      <div className="flex justify-end">
        <GlassButton
          variant="secondary"
          onClick={() => queryClient.invalidateQueries({ queryKey: ['server-assignments', serverId] })}
        >
          Refresh
        </GlassButton>
      </div>
    </div>
  );
};
