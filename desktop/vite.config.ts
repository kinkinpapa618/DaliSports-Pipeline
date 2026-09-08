import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import electron from 'vite-plugin-electron'
import renderer from 'vite-plugin-electron-renderer'
import path from 'path'

import fs from 'fs'

const copyPreloadPlugin = () => ({
  name: 'copy-preload',
  buildStart() {
    const src = path.resolve(__dirname, 'electron/preload.cjs');
    const dest = path.resolve(__dirname, 'dist-electron/preload.cjs');
    const destJs = path.resolve(__dirname, 'dist-electron/preload.js');
    if (fs.existsSync(src)) {
      fs.mkdirSync(path.dirname(dest), { recursive: true });
      fs.copyFileSync(src, dest);
      fs.copyFileSync(src, destJs);
    }
  },
  closeBundle() {
    const src = path.resolve(__dirname, 'electron/preload.cjs');
    const dest = path.resolve(__dirname, 'dist-electron/preload.cjs');
    const destJs = path.resolve(__dirname, 'dist-electron/preload.js');
    if (fs.existsSync(src)) {
      fs.mkdirSync(path.dirname(dest), { recursive: true });
      fs.copyFileSync(src, dest);
      fs.copyFileSync(src, destJs);
    }
  },
});

// https://vitejs.dev/config/
export default defineConfig({
  base: './',
  plugins: [
    react(),
    copyPreloadPlugin(),
    electron([
      {
        entry: 'electron/main.ts',
        onstart(options) {
          options.startup()
        },
      },
    ]),
    renderer(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
})
