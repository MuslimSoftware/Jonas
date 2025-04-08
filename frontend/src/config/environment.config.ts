import Constants from 'expo-constants';

export type Environment = 'development' | 'staging' | 'production';

export interface EnvironmentConfig {
  env: Environment;
  API_URL: string; 
  BYPASS_AUTH: boolean;
  AUTO_FILL_CREDENTIALS: boolean;
  AUTO_FILL_EMAIL?: string;
  AUTO_FILL_PASSWORD?: string;
  BRAND_NAME: string;
  BRAND_SLUG: string;
  eas?: {
    projectId?: string;
  };
}

// Helper function to safely access the extra config and validate
function loadAndValidateConfig(): EnvironmentConfig {
  const extra = Constants.expoConfig?.extra ?? {};

  const env = extra.env ?? 'development';
  if (!['development', 'staging', 'production'].includes(env)) {
    throw new Error(`Invalid environment specified: ${env}`);
  }

  const API_URL = extra.API_URL;
  if (!API_URL) {
    throw new Error('API_URL is not configured in environment variables.');
  }

  const config: EnvironmentConfig = {
    env: env as Environment,
    API_URL: API_URL,
    BYPASS_AUTH: extra.BYPASS_AUTH ?? false,
    AUTO_FILL_CREDENTIALS: extra.AUTO_FILL_CREDENTIALS ?? false,
    AUTO_FILL_EMAIL: extra.AUTO_FILL_EMAIL,
    AUTO_FILL_PASSWORD: extra.AUTO_FILL_PASSWORD,
    BRAND_NAME: extra.BRAND_NAME ?? 'DefaultAppName',
    BRAND_SLUG: extra.BRAND_SLUG ?? 'default-app-slug',
    eas: extra.eas,
  };

  return config;
}

// Load, validate, and export the config immediately
export const config: EnvironmentConfig = loadAndValidateConfig();

// Optional: Helper functions for environment checks (similar to the old index.ts)
export const isDev = (): boolean => config.env === 'development';
export const isStaging = (): boolean => config.env === 'staging';
export const isProd = (): boolean => config.env === 'production'; 