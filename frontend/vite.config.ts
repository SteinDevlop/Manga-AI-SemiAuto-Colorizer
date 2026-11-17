import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [
    react(),
    {
      name: 'no-cache-headers',
      configureServer(server) {
        server.middlewares.use((_req, res, next) => {
          const originalWriteHead = res.writeHead.bind(res);
          res.writeHead = (statusCode: number, headers?: Record<string, string>) => {
            const newHeaders: Record<string, string> = {
              ...(headers ?? {}),
              'Cache-Control': 'no-cache, no-store, must-revalidate',
              'Pragma': 'no-cache',
              'Expires': '0',
            };
            return originalWriteHead(statusCode, newHeaders);
          };
          next();
        });
      },
    },
  ],
  server: {
    port: 5173,
    open: false,
    historyApiFallback: true,
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/__tests__/setup.ts'],
  },
});
