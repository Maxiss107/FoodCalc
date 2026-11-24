import { api, tokenStorage } from './api';

export interface LoginRequest {
  email: string;
  password: string;
  remember_me: boolean;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface TokenPairResponse {
  access: string;
  refresh: string;
  token_type: string;
}

export interface UserProfile {
  id: string;
  email: string;
  is_active: boolean;
  created_at: string;
}

export const authApi = {
  async login(credentials: LoginRequest) {
    if (import.meta.env.VITE_MOCK_AUTH === 'true') {
      tokenStorage.setTokens('mock_access_token', 'mock_refresh_token', credentials.remember_me);
      return { access: 'mock_access_token', refresh: 'mock_refresh_token', token_type: 'bearer' };
    }

    const response = await api.post<TokenPairResponse>('/auth/login', credentials);
    tokenStorage.setTokens(response.access, response.refresh, credentials.remember_me);
    return response;
  },

  async register(data: RegisterRequest) {
    const response = await api.post<TokenPairResponse>('/auth/register', data);
    tokenStorage.setTokens(response.access, response.refresh, true);
    return response;
  },

  async getMe() {
    return api.get<UserProfile>('/auth/me');
  },

  logout() {
    tokenStorage.clear();
  },
};
