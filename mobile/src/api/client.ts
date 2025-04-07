import { config } from '@/config';
import { ApiClient as SharedApiClient } from '@shared/src/api';
import { MobileTokenStorage } from './MobileTokenStorage';

const mobileTokenStorage = new MobileTokenStorage();

export const apiClient = new SharedApiClient(
  config.apiUrl, 
  mobileTokenStorage
);