import { apiClient } from '../client'; // Import the configured mobile client instance
import { authApi as sharedAuthApi } from '@shared/src/api'; // Import shared endpoint factories

// Re-export the factory functions, pre-configured with the mobile apiClient
export const requestOTP = sharedAuthApi.requestOTP(apiClient);
export const validateOTP = sharedAuthApi.validateOTP(apiClient);
export const authenticate = sharedAuthApi.authenticate(apiClient);
export const refreshToken = sharedAuthApi.refreshToken(apiClient);