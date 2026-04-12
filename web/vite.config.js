import { defineConfig } from 'vite';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.resolve(__dirname, '../data');

export default defineConfig({
  root: '.',
  base: '/OvernightRadar/',
  build: {
    outDir: 'dist',
  },
  server: {
    open: true,
  },
  plugins: [
    {
      name: 'serve-data',
      configureServer(server) {
        server.middlewares.use((req, res, next) => {
          if (req.url && req.url.startsWith('/data/')) {
            const relativePath = req.url.replace('/data/', '');
            const filePath = path.join(dataDir, relativePath);
            if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
              res.setHeader('Content-Type', 'application/json');
              res.setHeader('Access-Control-Allow-Origin', '*');
              fs.createReadStream(filePath).pipe(res);
              return;
            }
          }
          next();
        });
      },
    },
  ],
});
