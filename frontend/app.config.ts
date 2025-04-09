// frontend/app.config.ts
const path = require('path');
const dotenv = require('dotenv');

// --- Configuration Loading --- 
const ENV = process.env.APP_ENV || 'development';
dotenv.config({ path: path.resolve(__dirname, '.env') }); // Load root .env
dotenv.config({ path: path.resolve(__dirname, `.env.${ENV}`), override: true }); // Load specific env

// Read needed values directly from process.env
const brandName = process.env.BRAND_NAME || 'DefaultAppName';
const brandSlug = process.env.BRAND_SLUG || 'default-app-slug';
const apiUrl = process.env.API_URL;
const bypassAuth = process.env.BYPASS_AUTH === 'true';
const autoFillCredentials = process.env.AUTO_FILL_CREDENTIALS === 'true';
const autoFillEmail = process.env.AUTO_FILL_EMAIL;
const autoFillPassword = process.env.AUTO_FILL_PASSWORD;

// --- Expo Config Export --- 
import { ExpoConfig, ConfigContext } from 'expo/config';

export default ({ config }: ConfigContext): ExpoConfig => {
  
  // Build the 'extra' object for runtime access
  const extraConfig = {
    env: ENV,
    API_URL: apiUrl, // Pass the value read from process.env
    BYPASS_AUTH: bypassAuth,
    AUTO_FILL_CREDENTIALS: autoFillCredentials,
    AUTO_FILL_EMAIL: autoFillEmail,
    AUTO_FILL_PASSWORD: autoFillPassword,
    BRAND_NAME: brandName,
    BRAND_SLUG: brandSlug,
    eas: {
      projectId: 'your-project-id' // Replace if needed
    }
  };

  return {
    name: brandName,
    slug: brandSlug,
    version: '1.0.0',
    orientation: 'portrait',
    icon: './src/assets/images/splash-icon.png',
    userInterfaceStyle: 'automatic',
    splash: {
      image: './src/assets/images/splash-icon.png',
      resizeMode: 'contain',
      backgroundColor: '#ffffff'
    },
    assetBundlePatterns: ['**/*'],
    ios: {
      supportsTablet: true,
      bundleIdentifier: 'com.yourusername.' + brandSlug, // Update if needed
      infoPlist: {
        NSAppTransportSecurity: {
          NSAllowsArbitraryLoads: ENV === 'development'
        }
      }
    },
    android: {
      adaptiveIcon: {
        foregroundImage: './src/assets/images/adaptive-icon.png',
        backgroundColor: '#ffffff'
      },
      package: 'com.yourusername.' + brandSlug, // Update if needed
    },
    web: {
      favicon: './src/assets/images/favicon.png'
    },
    plugins: ['expo-router', 'expo-secure-store'],
    experiments: {
      typedRoutes: true
    },
    scheme: brandSlug,
    extra: extraConfig,
    updates: {
      fallbackToCacheTimeout: 0
    },
    newArchEnabled: true,
  };
}; 