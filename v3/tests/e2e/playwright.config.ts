import { existsSync, readFileSync } from 'node:fs'
import path from 'node:path'
import { defineConfig } from '@playwright/test'

// Read the repository's .env like scripts/lib.sh does: KEY=VALUE lines, one pair of quotes
// stripped, and a variable already set in the environment wins.
const envFile = path.resolve(__dirname, '../../.env')
if (existsSync(envFile)) {
  for (const line of readFileSync(envFile, 'utf8').split(/\r?\n/)) {
    if (/^\s*(#|$)/.test(line)) continue
    const m = /^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$/.exec(line)
    if (m && process.env[m[1]] === undefined) process.env[m[1]] = m[2].replace(/^(['"])(.*)\1$/, '$2')
  }
}

export default defineConfig({
  testDir: '.',
  timeout: 60_000,
  retries: 0,
  reporter: [['list']],
  use: {
    baseURL: process.env.ONMS_URL ?? `http://localhost:${process.env.ONMS_HTTP_PORT ?? '8980'}`,
    browserName: 'chromium',
    viewport: { width: 1400, height: 900 },
    screenshot: 'only-on-failure'
  }
})
