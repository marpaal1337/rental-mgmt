import { defineConfig } from '@playwright/test'

const API_PORT = 8765
const WEB_PORT = 5174
const E2E_DB = '/tmp/rental-mgmt-e2e.db'

export default defineConfig({
  testDir: './e2e',
  timeout: 30000,
  retries: 1,
  use: {
    baseURL: `http://localhost:${WEB_PORT}`,
    headless: true,
  },
  webServer: [
    {
      command:
        `sh -c "rm -f ${E2E_DB} ${E2E_DB}-wal ${E2E_DB}-shm && ` +
        `DATABASE_URL=sqlite:///${E2E_DB} .venv/bin/python -m alembic upgrade head && ` +
        `DATABASE_URL=sqlite:///${E2E_DB} .venv/bin/python -m uvicorn app.main:app --port ${API_PORT}"`,
      cwd: '..',
      port: API_PORT,
      reuseExistingServer: false,
      timeout: 60000,
    },
    {
      command: `npx vite --port ${WEB_PORT}`,
      port: WEB_PORT,
      reuseExistingServer: true,
      timeout: 30000,
      env: {
        VITE_API_TARGET: `http://localhost:${API_PORT}`,
      },
    },
  ],
})
