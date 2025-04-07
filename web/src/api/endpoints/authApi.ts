import { apiClient } from '../client'; // Import the configured web client instance
import { authApi as sharedAuthApi } from '@jonas/shared/src/api'; // Import shared endpoint factories

// Re-export the factory functions, pre-configured with the web apiClient
export const requestOTP = sharedAuthApi.requestOTP(apiClient);
export const validateOTP = sharedAuthApi.validateOTP(apiClient);
export const authenticate = sharedAuthApi.authenticate(apiClient);
export const refreshToken = sharedAuthApi.refreshToken(apiClient); 