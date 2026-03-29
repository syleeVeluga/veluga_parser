import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': { target: 'http://localhost:8001', changeOrigin: false },
      '/health': { target: 'http://localhost:8001', changeOrigin: false },
    },
  },
  build: {
    outDir: 'dist',
  },
})
