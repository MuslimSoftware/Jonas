// Learn more https://docs.expo.io/guides/customizing-metro
const { getDefaultConfig } = require('expo/metro-config')
const path = require('path')

// Get the project root (web directory)
const projectRoot = __dirname
// Calculate the workspace root 
const workspaceRoot = path.resolve(projectRoot, '..')

/** @type {import('expo/metro-config').MetroConfig} */
const config = getDefaultConfig(projectRoot, {
  // Enable CSS support (optional, depends on your styling)
  // isCSSEnabled: true,
})

// --- Monorepo Configuration ---

// Point to the shared node_modules
config.resolver.nodeModulesPaths = [
  path.resolve(projectRoot, 'node_modules'),
  path.resolve(workspaceRoot, 'node_modules'),
]

// Watch the entire monorepo
config.watchFolders = [workspaceRoot]

// Force resolving certain dependencies from the web app's node_modules
// (React, ReactDOM, React Native Web are key)
config.resolver.extraNodeModules = {
  'react': path.resolve(projectRoot, 'node_modules/react'),
  'react-dom': path.resolve(projectRoot, 'node_modules/react-dom'),
  'react-native-web': path.resolve(projectRoot, 'node_modules/react-native-web'),
}

// Use TS path aliases defined in tsconfig.json
config.resolver.sourceExts.push('ts', 'tsx')
config.resolver.useTsconfigPaths = true;

// --- End Monorepo Configuration ---

module.exports = config 