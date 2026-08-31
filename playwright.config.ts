import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [["list"], ["html", { outputFolder: "playwright-report", open: "never" }]],
  use: {
    baseURL: process.env.BASE_URL ?? "http://127.0.0.1:3000",
    channel: "chrome",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    actionTimeout: 10_000,
  },
  webServer: process.env.E2E_EXTERNAL ? undefined : [
    {
      command: "APP_ENV=test DEMO_MODE=true JWT_SECRET=e2e-only-secret-that-is-long-enough DATABASE_URL=sqlite+aiosqlite:///:memory: CORS_ORIGINS=http://127.0.0.1:3000,http://localhost:3000 apps/api/.venv/bin/python -m uvicorn main:app --app-dir apps/api --host 127.0.0.1 --port 8000",
      url: "http://127.0.0.1:8000/api/v1/health",
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      command: "cd apps/web && NEXT_PUBLIC_DEMO_MODE=true AWAKENING_API_INTERNAL_URL=http://127.0.0.1:8000/api/v1 npx next build && AWAKENING_API_INTERNAL_URL=http://127.0.0.1:8000/api/v1 npx next start -p 3000",
      url: "http://127.0.0.1:3000",
      reuseExistingServer: false,
      timeout: 120_000,
    },
  ],
});
