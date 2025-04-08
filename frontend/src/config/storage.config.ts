import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';

// ----- Storage Interface -----
interface IStorage {
  saveItem(key: string, value: string): Promise<void>;
  getItem(key: string): Promise<string | null>;
  deleteItem(key: string): Promise<void>;
}

// ----- SecureStore Adapter (Native) -----
class SecureStorageAdapter implements IStorage {
  async saveItem(key: string, value: string): Promise<void> {
    try {
      await SecureStore.setItemAsync(key, value);
    } catch (error) {
      console.error('[Storage - SecureStore] Error saving item:', key, error);
      // Re-throw or handle as appropriate for your app's error strategy
      throw error;
    }
  }

  async getItem(key: string): Promise<string | null> {
    try {
      return await SecureStore.getItemAsync(key);
    } catch (error) {
      console.error('[Storage - SecureStore] Error getting item:', key, error);
      return null; // Return null on error
    }
  }

  async deleteItem(key: string): Promise<void> {
    try {
      await SecureStore.deleteItemAsync(key);
    } catch (error) {
      console.error('[Storage - SecureStore] Error deleting item:', key, error);
      // Re-throw or handle
      throw error;
    }
  }
}

// ----- LocalStorage Adapter (Web) -----
class LocalStorageAdapter implements IStorage {
  // Prefix to avoid potential collisions in localStorage
  private readonly keyPrefix = 'app_storage_';

  private prefixedKey(key: string): string {
    return `${this.keyPrefix}${key}`;
  }

  async saveItem(key: string, value: string): Promise<void> {
    try {
      localStorage.setItem(this.prefixedKey(key), value);
      console.warn(`[Storage - LocalStorage] Saved item '${key}' to non-secure localStorage.`);
    } catch (error) {
      console.error('[Storage - LocalStorage] Error saving item:', key, error);
      throw error;
    }
  }

  async getItem(key: string): Promise<string | null> {
    try {
      const value = localStorage.getItem(this.prefixedKey(key));
      if (value) {
        console.warn(`[Storage - LocalStorage] Retrieved item '${key}' from non-secure localStorage.`);
      }
      return value;
    } catch (error) {
      console.error('[Storage - LocalStorage] Error getting item:', key, error);
      return null;
    }
  }

  async deleteItem(key: string): Promise<void> {
    try {
      localStorage.removeItem(this.prefixedKey(key));
      console.warn(`[Storage - LocalStorage] Deleted item '${key}' from non-secure localStorage.`);
    } catch (error) {
      console.error('[Storage - LocalStorage] Error deleting item:', key, error);
      throw error;
    }
  }
}

// ----- Exported Storage Instance -----
let storageInstance: IStorage;

if (Platform.OS === 'web') {
  storageInstance = new LocalStorageAdapter();
} else {
  storageInstance = new SecureStorageAdapter();
}

export const storage: IStorage = storageInstance;

// ----- Convenience Token Functions (Optional but recommended) -----
const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

export const saveAccessToken = (token: string) => storage.saveItem(ACCESS_TOKEN_KEY, token);
export const getAccessToken = () => storage.getItem(ACCESS_TOKEN_KEY);
export const deleteAccessToken = () => storage.deleteItem(ACCESS_TOKEN_KEY);

export const saveRefreshToken = (token: string) => storage.saveItem(REFRESH_TOKEN_KEY, token);
export const getRefreshToken = () => storage.getItem(REFRESH_TOKEN_KEY);
export const deleteRefreshToken = () => storage.deleteItem(REFRESH_TOKEN_KEY); 