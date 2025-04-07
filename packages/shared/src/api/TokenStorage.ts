/**
 * Abstract interface for storing authentication tokens.
 * Implementations will vary by platform (e.g., SecureStore for mobile, localStorage for web).
 */
export interface TokenStorage {
  getAccessToken(): Promise<string | null>;
  setAccessToken(token: string): Promise<void>;
  getRefreshToken(): Promise<string | null>;
  setRefreshToken(token: string): Promise<void>;
  clearTokens(): Promise<void>;
} 