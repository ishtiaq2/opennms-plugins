import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: '.',
  timeout: 60_000,
  retries: 0,
  reporter: [['list']],
  use: {
    baseURL: process.env.ONMS_URL ?? 'http://localhost:8980',
    browserName: 'chromium',
    viewport: { width: 1400, height: 900 },
    screenshot: 'only-on-failure'
  }
})
