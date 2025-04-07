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

// 2. Tell Metro where to resolve modules (mobile first, then root)
config.resolver.nodeModulesPaths = [
  path.resolve(projectRoot, 'node_modules'),
  path.resolve(workspaceRoot, 'node_modules'),
]

// 3. Block potential duplicate dependencies from the shared package
// Prevents Metro from resolving react-native within the shared package's node_modules
config.resolver.blockList = [
  new RegExp(
    `${path.resolve(workspaceRoot, 'packages/shared/node_modules/react-native')}/.*`
  ),
  new RegExp(
    `${path.resolve(workspaceRoot, 'packages/shared/node_modules/react')}/.*`
  ),
];

// 4. Force Metro to resolve react & react-native from the mobile app's node_modules
const mobileReactNativePath = path.resolve(projectRoot, 'node_modules/react-native')
const mobileReactPath = path.resolve(projectRoot, 'node_modules/react')
config.resolver.extraNodeModules = {
  'react-native': mobileReactNativePath,
  'react': mobileReactPath,
}

// Optional: Enable symlink resolution (can sometimes help with pnpm)
// config.resolver.unstable_enableSymlinks = true;

// --- End Monorepo Configuration ---

// Add custom source extensions if needed (keep existing)
config.resolver.sourceExts = [...config.resolver.sourceExts, 'mjs', 'cjs']

module.exports = config 