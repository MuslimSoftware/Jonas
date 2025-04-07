import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'; // Import necessary function
import fs from 'fs/promises'; // Import fs module

// Get current directory path using import.meta.url
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
// Resolve from workspace root
const workspaceRoot = path.resolve(__dirname, '..', '..'); 

// Helper to resolve node_modules paths
const resolve = (pkg: string) => path.resolve(workspaceRoot, 'node_modules', pkg);

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    // Configure React plugin to handle Flow/TS in dependencies
    react({
      // Include node_modules that need transformation
      include: "**/*.{jsx,tsx,js,ts}",
      babel: {
        // Ensure necessary Babel plugins run on these files
        plugins: [
          // Add plugin to strip Flow types
          '@babel/plugin-transform-flow-strip-types',
          // Add other necessary plugins if needed (e.g., class properties)
        ],
      },
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      // Use simple alias - Vite should handle this if react-native-web is installed
      'react-native': 'react-native-web', 
    },
    // Keep Deduplicate
    dedupe: ['react', 'react-dom', 'react-native', 'react-native-web'],
  },
  // Ensure shared package is NOT optimized, as it's linked
  optimizeDeps: {
    exclude: [
      '@shared',
      '@react-native/assets-registry' // Exclude this problematic package
    ], 
    esbuildOptions: {
      loader: {
        '.js': 'jsx', // Keep default JS->JSX for other deps
      },
      // No specific plugins needed here now, rely on main Babel transform
      // plugins: [ ... ] 
    },
  },
  build: {
    commonjsOptions: {
      // Process commonjs in shared and node_modules
      include: [
        /shared/,
        /node_modules/,
        // Explicitly include paths requiring JSX transformation within node_modules
        /node_modules\/@expo\/vector-icons/,
        /node_modules\/react-native-vector-icons/,
      ],
      transformMixedEsModules: true, // Often needed when mixing CJS/ESM
    },
  },
  // Optional: Server config if needed (e.g., for proxy)
  // server: {
  //   port: 3000,
  //   proxy: {
  //     '/api': {
  //       target: 'http://localhost:8000', // Your backend URL
  //       changeOrigin: true,
  //       rewrite: (path) => path.replace(/^\/api/, ''),
  //     },
  //   },
  // },
}) 