import react from '@vitejs/plugin-react'
import { configDefaults, defineConfig } from 'vitest/config'

const backend = 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: { proxy: { '/api': backend, '/health': backend } },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: false,
    exclude: [...configDefaults.exclude, 'e2e/**'],
    coverage: { provider: 'v8', include: ['src/**'], exclude: ['src/test/**', 'src/main.tsx'] },
  },
})
