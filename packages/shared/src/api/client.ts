import { HttpMethod, ApiResponse, ApiError } from './types/api.types';
import { TokenStorage } from './TokenStorage';
import { AuthResponse } from './types/auth.types'; // For refresh response

class ApiClient {
  private baseUrl: string;
  private tokenStorage: TokenStorage;
  private defaultHeaders: Record<string, string>;

  constructor(baseUrl: string, tokenStorage: TokenStorage) {
    if (!baseUrl) {
      throw new Error('ApiClient requires a baseUrl');
    }
    if (!tokenStorage) {
      throw new Error('ApiClient requires a tokenStorage implementation');
    }
    this.baseUrl = baseUrl;
    this.tokenStorage = tokenStorage;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    };
  }

  private async refreshToken(): Promise<boolean> {
    try {
      const refreshToken = await this.tokenStorage.getRefreshToken();
      if (!refreshToken) return false;

      // Assuming refresh endpoint is always /auth/refresh relative to baseUrl
      const refreshUrl = `${this.baseUrl}/auth/refresh`; 
      const rawResponse = await fetch(refreshUrl, {
        method: HttpMethod.POST,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      const response: ApiResponse<AuthResponse> = await rawResponse.json();
      if (!response.success || !response.data?.access_token) {
        // Consider clearing tokens if refresh fails definitively
        // await this.tokenStorage.clearTokens(); 
        return false;
      }

      await this.tokenStorage.setAccessToken(response.data.access_token);
      // Optionally update refresh token if the endpoint returns a new one
      if (response.data.refresh_token) {
        await this.tokenStorage.setRefreshToken(response.data.refresh_token);
      }
      return true;
    } catch (error) {
      console.error('Token refresh failed:', error);
      // Consider clearing tokens on unexpected errors during refresh
      // await this.tokenStorage.clearTokens();
      return false;
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    isRetry: boolean = false // Prevent infinite refresh loops
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = { ...this.defaultHeaders };

    const token = await this.tokenStorage.getAccessToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers: { ...headers, ...options.headers },
      });

      if (response.status === 401 && token && !isRetry) {
        const refreshed = await this.refreshToken();
        if (refreshed) {
          // Retry the original request with the new token
          return this.request<T>(endpoint, options, true);
        } else {
          // Refresh failed, clear tokens and throw original 401 error
          await this.tokenStorage.clearTokens();
           // Re-throw or handle as appropriate for the app (e.g., redirect to login)
           // For now, just throw a generic error after clearing tokens
          throw { 
            message: 'Session expired or invalid. Please log in again.',
            error_code: 'UNAUTHENTICATED',
            status_code: 401,
          } as ApiError;
        }
      }

      const text = await response.text();
      let data: ApiResponse<T> | null = null;
      try {
        data = text ? JSON.parse(text) : null;
      } catch (parseError) {
         // Handle non-JSON responses or empty responses on success codes (e.g., 204)
        if (response.ok && !text) {
           return { success: true, message: 'Success', data: null as T }; 
        } 
        console.error('API response parsing error:', parseError, 'Raw text:', text);
        throw {
          message: `Invalid JSON response from server: ${response.status} ${response.statusText}`,
          error_code: 'INVALID_RESPONSE',
          status_code: response.status,
        } as ApiError;
      }
      
      if (!response.ok) {
        throw {
          message: data?.message || `Request failed: ${response.status} ${response.statusText}`,
          error_code: (data as any)?.error_code || 'UNKNOWN_ERROR',
          status_code: response.status,
        } as ApiError;
      }

      // Ensure the parsed data conforms to ApiResponse structure
      if (data === null || typeof data !== 'object' || typeof data.success !== 'boolean') {
         throw {
            message: 'Invalid API response structure.',
            error_code: 'INVALID_RESPONSE_STRUCTURE',
            status_code: response.status,
          } as ApiError;
      }

      return data;
    } catch (error) {
      // Don't re-throw network errors if they are AbortError
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('Request aborted');
         throw { // Re-throw specifically as ApiError for consistent handling
          message: 'Request aborted by user.',
          error_code: 'REQUEST_ABORTED',
          status_code: 0, // Or appropriate status code
        } as ApiError;
      }
      // If it's already an ApiError, re-throw it
      if (error && typeof error === 'object' && 'error_code' in error) {
        throw error;
      }
      // Otherwise, wrap it as a generic network error
      console.error('Network or unexpected error:', error);
      throw {
        message: (error instanceof Error) ? error.message : 'An unexpected network error occurred.',
        error_code: 'NETWORK_ERROR',
        status_code: 0, // Or appropriate status code
      } as ApiError;
    }
  }

  private async makeRequest<T>(
    method: HttpMethod,
    endpoint: string,
    data?: any,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const requestOptions: RequestInit = {
      ...options,
      method,
      ...(data && { body: JSON.stringify(data) }),
    };
    return this.request<T>(endpoint, requestOptions);
  }

  public async get<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
    return this.makeRequest<T>(HttpMethod.GET, endpoint, undefined, options);
  }

  public async post<T>(endpoint: string, data?: any, options: RequestInit = {}): Promise<ApiResponse<T>> {
    return this.makeRequest<T>(HttpMethod.POST, endpoint, data, options);
  }

  public async put<T>(endpoint: string, data?: any, options: RequestInit = {}): Promise<ApiResponse<T>> {
    return this.makeRequest<T>(HttpMethod.PUT, endpoint, data, options);
  }

  public async delete<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
    return this.makeRequest<T>(HttpMethod.DELETE, endpoint, undefined, options);
  }
}

// Note: We don't export a singleton instance here.
// Each app (web, mobile) will create its own instance with its specific config.
export { ApiClient }; 