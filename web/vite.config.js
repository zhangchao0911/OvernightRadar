import { defineConfig } from 'vite';
import path from 'path';

export default defineConfig({
  root: '.',
  build: {
    outDir: 'dist',
  },
  server: {
    open: true,
    proxy: {
      '/data': {
        target: 'http://localhost:5173',
        rewrite: (path) => path.replace('/data', '../data'),
      },
    },
  },
});
