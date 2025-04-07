import { ApiClient as SharedApiClient } from '@jonas/shared/src/api';
import { WebTokenStorage } from './WebTokenStorage';

// Read API URL from Vite environment variables
// Ensure you have VITE_API_URL set in your .env file(s)
const apiUrl = import.meta.env.VITE_API_URL;

if (!apiUrl) {
  console.warn(
    'VITE_API_URL environment variable is not set. API calls may fail. '
    + 'Create a .env file in the web/ directory with VITE_API_URL=your_api_url'
  );
}

const webTokenStorage = new WebTokenStorage();

// Create a configured singleton instance for the web app
export const apiClient = new SharedApiClient(
  apiUrl || '', // Use empty string as fallback, though warnings are shown
  webTokenStorage
);

// Optional: Export the storage instance if needed elsewhere
export { webTokenStorage }; 