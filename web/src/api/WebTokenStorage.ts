import { TokenStorage } from '@shared/src/api';

const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

export class WebTokenStorage implements TokenStorage {
  async getAccessToken(): Promise<string | null> {
    try {
      return localStorage.getItem(ACCESS_TOKEN_KEY);
    } catch (error) {
      console.error('Failed to get access token from localStorage', error);
      return null;
    }
  }

  async setAccessToken(token: string): Promise<void> {
    try {
      localStorage.setItem(ACCESS_TOKEN_KEY, token);
    } catch (error) {
      console.error('Failed to set access token in localStorage', error);
    }
  }

  async getRefreshToken(): Promise<string | null> {
    try {
      return localStorage.getItem(REFRESH_TOKEN_KEY);
    } catch (error) {
      console.error('Failed to get refresh token from localStorage', error);
      return null;
    }
  }

  async setRefreshToken(token: string): Promise<void> {
    try {
      localStorage.setItem(REFRESH_TOKEN_KEY, token);
    } catch (error) {
      console.error('Failed to set refresh token in localStorage', error);
    }
  }

  async clearTokens(): Promise<void> {
    try {
      localStorage.removeItem(ACCESS_TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
    } catch (error) {
      console.error('Failed to clear tokens from localStorage', error);
    }
  }
} 