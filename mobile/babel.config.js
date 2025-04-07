const path = require('path');
const workspaceRoot = path.resolve(__dirname, '..');

module.exports = function (api) {
  api.cache(true);
  return {
    presets: [
      ['babel-preset-expo', { jsxRuntime: 'automatic' }],
    ],
    plugins: [
      [
        'module-resolver',
        {
          root: ['./src'],
          extensions: ['.ios.js', '.android.js', '.js', '.ts', '.tsx', '.json'],
          alias: {
            '@': './src',
            '@/api': './src/api',
            '@/features': './src/features',
            '@/shared': './src/shared',
            '@/constants': './src/constants',
            '@/context': './src/context',
            '@/assets': './src/assets',
            '@/types': './src/types'
          }
        }
      ],
      // Explicitly tell babel to look for source files in the shared package
      // This might not be strictly necessary with babel-preset-expo, but can help
      // Ensure monorepo dependencies are correctly processed.
      // Note: This might slow down build times slightly.
      // ["@babel/plugin-transform-runtime", {
      //   "helpers": true,
      //   "regenerator": true
      // }],
      // If the above doesn't work, maybe explicitly pointing it:
      // However, `babel-preset-expo` should handle this.
      // Consider this as a last resort for Babel issues.
      // (This requires installing `@babel/plugin-proposal-export-namespace-from`)
      // ['@babel/plugin-proposal-export-namespace-from'], 
    ].filter(Boolean), // filter(Boolean) allows easy commenting out of plugins
  };
}; 