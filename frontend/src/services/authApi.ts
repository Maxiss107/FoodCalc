import { api, tokenStorage } from './api';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token?: string;
  token?: string;
}

export const authApi = {
  async login(credentials: LoginRequest, remember: boolean) {
    // Эндпоинт авторизации Django Ninja (уточнить у Киры при стыковке: /auth/login или /accounts/login)
    const response = await api.post<AuthResponse>('/auth/login', credentials);
    const token = response.access_token || response.token;

    if (token) {
      tokenStorage.set(token, remember);
    }

    return response;
  },

  logout() {
    tokenStorage.clear();
  },
};
