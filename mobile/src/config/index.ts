import Constants from 'expo-constants'
import { AppConfig, Environment } from '@/features/shared/types/config'

const validateConfig = (config: Partial<AppConfig>): AppConfig => {
  if (!config.apiUrl) {
    throw new Error('API URL is not configured in environment')
  }

  if (!config.env) {
    throw new Error('Environment is not configured')
  }

  return {
    env: config.env as Environment,
    apiUrl: config.apiUrl,
    devMode: {
      bypassAuth: config.devMode?.bypassAuth ?? false,
      autoFillCredentials: {
        enabled: config.devMode?.autoFillCredentials?.enabled ?? false,
        email: config.devMode?.autoFillCredentials?.email ?? '',
        password: config.devMode?.autoFillCredentials?.password ?? '',
      },
    },
  }
}

const rawConfig: Partial<AppConfig> = {
  env: Constants.expoConfig?.extra?.env as Environment,
  apiUrl: Constants.expoConfig?.extra?.apiUrl,
  devMode: {
    bypassAuth: Constants.expoConfig?.extra?.bypassAuth,
    autoFillCredentials: {
      enabled: Constants.expoConfig?.extra?.autoFillCredentials,
      email: Constants.expoConfig?.extra?.autoFillEmail,
      password: Constants.expoConfig?.extra?.autoFillPassword,
    },
  },
}

export const config = validateConfig(rawConfig)

// Helper functions
export const isDev = () => config.env === 'development'
export const isStaging = () => config.env === 'staging'
export const isProd = () => config.env === 'production' 