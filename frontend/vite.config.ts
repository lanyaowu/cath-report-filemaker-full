import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// /api は Node 版 / Spring Boot 版どちらのバックエンドにも転送されます（既定: 8080）
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/api': { target: process.env.API_TARGET ?? 'http://localhost:8080', changeOrigin: true } },
  },
});
