import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { isAxiosError } from 'axios';
import type { User, LoginCredentials, AuthResponse } from '@/types/api';
import { apiClient } from '@/api/client';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  refreshAccessToken: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Login action
      login: async (credentials: LoginCredentials) => {
        set({ isLoading: true, error: null });

        try {
          const response = await apiClient.post<AuthResponse>('/auth/login/', credentials);
          const { access, refresh, user } = response.data;

          // Store tokens
          localStorage.setItem('access_token', access);
          localStorage.setItem('refresh_token', refresh);

          set({
            user,
            accessToken: access,
            refreshToken: refresh,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error: unknown) {
          const errorMessage = extractAuthError(error);
          set({
            error: errorMessage,
            isLoading: false,
            isAuthenticated: false,
          });
          throw error;
        }
      },

      // Logout action
      logout: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');

        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          error: null,
        });
      },

      // Refresh access token
      refreshAccessToken: async () => {
        const { refreshToken } = get();

        if (!refreshToken) {
          throw new Error('No refresh token available');
        }

        try {
          const response = await apiClient.post<{ access: string }>('/auth/refresh/', {
            refresh: refreshToken,
          });

          const { access } = response.data;
          localStorage.setItem('access_token', access);

          set({ accessToken: access });
        } catch (error: unknown) {
          // Refresh failed, logout user
          get().logout();
          throw error;
        }
      },

      // Clear error
      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

const extractAuthError = (error: unknown): string => {
  if (isAxiosError(error)) {
    const detail = error.response?.data as { detail?: string } | undefined;
    return detail?.detail || error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'Login fallito';
};
