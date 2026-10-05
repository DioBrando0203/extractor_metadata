import { defineConfig } from '@playwright/test'

const backendCommand =
  process.platform === 'win32' ? 'py ../iniciar.py --sin-navegador' : 'python3 ../iniciar.py --sin-navegador'

export default defineConfig({
  testDir: './e2e',
  use: { baseURL: 'http://127.0.0.1:5173', browserName: 'chromium' },
  webServer: [
    {
      command: backendCommand,
      url: 'http://127.0.0.1:8000/api/health',
      reuseExistingServer: true,
      timeout: 30_000,
    },
    {
      command: 'npm run dev',
      url: 'http://127.0.0.1:5173',
      reuseExistingServer: true,
      timeout: 30_000,
    },
  ],
})
