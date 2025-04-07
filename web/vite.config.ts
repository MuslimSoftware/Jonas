import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'; // Import necessary function

// Get current directory path using import.meta.url
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'), // Now __dirname is defined
      // Add alias for react-native to react-native-web
      'react-native': 'react-native-web',
    },
  },
  // Ensure shared package is optimized and not externalized if needed
  optimizeDeps: {
    include: ['@jonas/shared'], // Adjust based on actual package name if needed
  },
  build: {
    commonjsOptions: {
      include: [/shared/, /node_modules/], // Process commonjs in shared and node_modules
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