/**
 * Simple asynchronous key-value storage interface.
 * Used for persisting theme preference across platforms.
 */
export interface StorageInterface {
  getItem(key: string): Promise<string | null>;
  setItem(key: string, value: string): Promise<void>;
  removeItem(key: string): Promise<void>;
} 