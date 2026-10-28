import { defineConfig } from '@playwright/test'

const PORT = 8100
const python = process.env.PYTHON ?? 'python'

// Runs the real stack: migrations on a fresh database, then the API serving the built frontend.
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['github'], ['html', { open: 'never' }]] : 'list',
  use: { baseURL: `http://127.0.0.1:${PORT}`, trace: 'retain-on-failure' },
  webServer: {
    command: `rm -f e2e.db && ${python} -m alembic upgrade head && ${python} -m uvicorn app.main:app --app-dir backend --port ${PORT}`,
    cwd: '..',
    url: `http://127.0.0.1:${PORT}/health/ready`,
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
    env: {
      DATABASE_URL: 'sqlite:///./e2e.db',
      STATIC_DIR: 'frontend/dist',
      RATE_LIMIT_PER_MINUTE: '10000',
      APP_ENV: 'development',
    },
  },
})
