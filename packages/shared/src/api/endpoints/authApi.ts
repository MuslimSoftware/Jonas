import { ApiClient } from '../client'; // Corrected path
import { ApiResponse } from '../types/api.types'; // Corrected path
import { 
  RequestOTPResponse, 
  ValidateOTPResponse, 
  AuthResponse,
  OTPRequest,
  ValidateOTPRequest,
  AuthRequest,
  RefreshTokenRequest
} from '../types/auth.types'; // Corrected path

// Functions now accept an apiClient instance

export const requestOTP = (apiClient: ApiClient) => 
  async ({ email, signal }: OTPRequest): Promise<ApiResponse<RequestOTPResponse>> => {
    return apiClient.post('/auth/request-otp', { email }, { signal });
};

export const validateOTP = (apiClient: ApiClient) =>
  async ({ email, otp, signal }: ValidateOTPRequest): Promise<ApiResponse<ValidateOTPResponse>> => {
    return apiClient.post('/auth/validate-otp', { email, otp }, { signal });
};

export const authenticate = (apiClient: ApiClient) =>
  async ({ token, signal }: AuthRequest): Promise<ApiResponse<AuthResponse>> => {
    return apiClient.post('/auth/auth', { token }, { signal }); // Changed endpoint based on pattern
};

export const refreshToken = (apiClient: ApiClient) =>
  async ({ refreshToken, signal }: RefreshTokenRequest): Promise<ApiResponse<{ access_token: string }>> => {
    // The refresh logic is now primarily handled within the ApiClient itself.
    // This specific endpoint function might become redundant unless needed for direct calls.
    // For now, keep it matching the mobile version but pointing to the standard endpoint.
    return apiClient.post('/auth/refresh', { refresh_token: refreshToken }, { signal });
}; 