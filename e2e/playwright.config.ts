import { defineConfig, devices } from "@playwright/test"

// Scripted UI tests run against the isolated stack from scripts/stack.sh (frontend :5174,
// backend :8001, database ticketlens_e2e, mock providers), never the dev servers or real data.
export default defineConfig({
  testDir: "tests",
  outputDir: "output/test-results",
  reporter: [
    ["list"],
    ["html", { outputFolder: "output/playwright-report", open: "never" }],
  ],
  workers: 1, // every test shares one database
  use: { baseURL: "http://localhost:5174", trace: "retain-on-failure" },
  expect: {
    toHaveScreenshot: { maxDiffPixelRatio: 0.01, animations: "disabled" },
  },
  projects: [
    {
      name: "chromium-desktop",
      use: { ...devices["Desktop Chrome"], viewport: { width: 1280, height: 800 } },
    },
    { name: "chromium-mobile", use: { ...devices["Pixel 7"] } },
  ],
  webServer: {
    command: "scripts/stack.sh",
    url: "http://localhost:5174",
    reuseExistingServer: false,
    timeout: 120_000,
  },
})
