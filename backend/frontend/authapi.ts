import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

// 1. Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Helper functions to handle token storage
const getToken = () => localStorage.getItem('access_token');
const getRefreshToken = () => localStorage.getItem('refresh_token');
const setTokens = (access: string, refresh: string | null) => {
  localStorage.setItem('access_token', access);
  if (refresh) localStorage.setItem('refresh_token', refresh);
};
const clearTokens = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};

/**
 * REQUEST INTERCEPTOR
 * Automatically adds the Bearer token to every request
 */
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

/**
 * RESPONSE INTERCEPTOR
 * Handles 401 errors by attempting to refresh the token
 */
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // If the error is 401 and we haven't retried this request yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = getRefreshToken();

      if (!refreshToken) {
        clearTokens();
        window.location.href = '/login';
        return Promise.reject(error);
      }

      try {
        // Call the refresh endpoint defined in your backend (RefreshTokenRequest)
        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const { access_token, refresh_token } = response.data;
        setTokens(access_token, refresh_token);

        // Update the original request with the new token and retry it
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
        }
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh token is also expired or invalid -> Force logout
        clearTokens();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);

/**
 * AUTH API METHODS
 * These map directly to your backend schemes (LoginRequest, RegisterRequest, etc.)
 */
export const authApi = {
  async login(credentials: { email: string; password: string }) {
    const { data } = await api.post('/auth/login', credentials);
    setTokens(data.access_token, data.refresh_token);
    return data;
  },

  async register(userData: { email: string; password: string }) {
    const { data } = await api.post('/auth/register', userData);
    return data;
  },

  async logout() {
    const refreshToken = getRefreshToken();
    if (refreshToken) {
      await api.post('/auth/logout', { refresh_token: refreshToken });
    }
    clearTokens();
  },

  async verifyEmail(token: string) {
    const { data } = await api.post('/auth/verify-email', { token });
    return data;
  },

  async resetPassword(token: string, newPassword: string) {
    const { data } = await api.post('/auth/reset-password', { token, new_password: newPassword });
    return data;
  }
};

export default api;
