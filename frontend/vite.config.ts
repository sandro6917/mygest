import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    host: true,          // <-- IMPORTANTE per accesso remoto
    proxy: {
      '/api': {
        target: 'http://100.99.234.12:8000',
        changeOrigin: true,
      },
      '/guide': {
        target: 'http://100.99.234.12:8000',
        changeOrigin: true,
      },
      '/etichette': {
        target: 'http://100.99.234.12:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://100.99.234.12:8001',
        ws: true,
      },
    },
  },
})
