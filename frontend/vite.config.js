import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: 5173,
    host: true,
    open: true,
    allowedHosts: ['xiaocheng.natapp1.cc'],
  },
  publicDir: 'public',
  // 添加 CSS 配置
  css: {
    postcss: './postcss.config.js'
  }
})