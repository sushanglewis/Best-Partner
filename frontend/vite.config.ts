import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // 同时读取顶层 .env（SSoT）与当前 frontend/.env，当前目录优先覆盖
  const rootDir = path.resolve(process.cwd(), '..')
  const envRoot = loadEnv(mode, rootDir, '')
  const envLocal = loadEnv(mode, process.cwd(), '')
  const env = { ...envRoot, ...envLocal, ...process.env }

  const backendPortRaw = env.VITE_BACKEND_PORT || env.BACKEND_PORT
  const devPortRaw = env.VITE_DEV_PORT || env.VITE_PORT || env.FRONTEND_PORT

  if (!backendPortRaw) {
    throw new Error('[vite.config] Missing VITE_BACKEND_PORT in environment (.env).')
  }
  if (!devPortRaw) {
    throw new Error('[vite.config] Missing VITE_DEV_PORT (or VITE_PORT/FRONTEND_PORT) in environment (.env).')
  }

  const backendPort = Number(backendPortRaw)
  const devPort = Number(devPortRaw)

  return {
    plugins: [react()],
    server: {
      port: devPort,
      host: true,
      strictPort: true, // 禁止端口漂移
      proxy: {
        '/api': {
          target: `http://localhost:${backendPort}`,
          changeOrigin: true,
        },
      },
    },
  }
})
