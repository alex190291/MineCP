import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User } from '@/types/user';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  requirePasswordChange: boolean;
  setAuth: (
    user: User,
    accessToken: string,
    refreshToken: string,
    requirePasswordChange?: boolean
  ) => void;
  clearAuth: () => void;
  updateUser: (user: User) => void;
  setRequirePasswordChange: (required: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      requirePasswordChange: false,

      setAuth: (user, accessToken, refreshToken, requirePasswordChange = false) => {
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
        set({
          user,
          accessToken,
          refreshToken,
          isAuthenticated: true,
          requirePasswordChange,
        });
      },

      clearAuth: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          requirePasswordChange: false,
        });
      },

      updateUser: (user) => {
        set({ user });
      },

      setRequirePasswordChange: (required) => {
        set({ requirePasswordChange: required });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        requirePasswordChange: state.requirePasswordChange,
      }),
    }
  )
);
