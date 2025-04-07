// Learn more https://docs.expo.io/guides/customizing-metro
const { getDefaultConfig } = require('expo/metro-config')
const path = require('path')

// Get the project root (mobile directory)
const projectRoot = __dirname
// Calculate the workspace root (assuming mobile is one level down from root)
const workspaceRoot = path.resolve(projectRoot, '..')

/** @type {import('expo/metro-config').MetroConfig} */
const config = getDefaultConfig(projectRoot, {
  // Enable CSS support
  isCSSEnabled: true,
})

// --- Monorepo Configuration ---

// 1. Watch the entire monorepo
config.watchFolders = [workspaceRoot]

// --- End Monorepo Configuration ---

// Add custom source extensions if needed (keep existing)
config.resolver.sourceExts = [...config.resolver.sourceExts, 'mjs', 'cjs']

module.exports = config 