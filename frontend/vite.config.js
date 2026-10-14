import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// In dev, Vite proxies /api to the local FastAPI server so the browser
// uses the same relative URLs it uses behind Nginx / the Ingress.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/api': 'http://localhost:8000' },
  },
});
