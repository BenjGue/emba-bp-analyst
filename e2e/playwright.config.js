// @ts-check
const { defineConfig, devices } = require("@playwright/test");

/**
 * Configuration Playwright pour la suite E2E de BizPlan-IA (BIZ-39).
 *
 * La suite cible l'application déployée (Azure Container Apps) en production,
 * surchargée par la variable d'environnement E2E_BASE_URL en CI.
 * Artefacts publiés pour audit : rapport HTML, traces, vidéos, captures.
 */
const BASE_URL =
  process.env.E2E_BASE_URL ||
  "https://bizplan-api-dev.salmondune-1b29666f.westeurope.azurecontainerapps.io";

module.exports = defineConfig({
  testDir: "./tests",
  // Échoue le run si un test.only est laissé par mégarde.
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  timeout: 60_000,
  expect: { timeout: 15_000 },
  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: "playwright-report" }],
    ["json", { outputFile: "results.json" }],
  ],
  use: {
    baseURL: BASE_URL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
