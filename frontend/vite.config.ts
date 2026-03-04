import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  // 生产构建使用相对路径，确保 Electron 从本地文件系统加载时资源可访问
  base: process.env.ELECTRON === 'true' ? './' : '/',
  server: {
    port: 722,
    open: false,
    strictPort: true,   // 端口被占时直接报错，不自动换端口
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
})
