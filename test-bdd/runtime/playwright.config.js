// @ts-check
const { defineConfig } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const { BASE_URL, USERNAME, PASSWORD, COOKIE } = require('./test-env');

// Export config values as process.env so spec files that read process.env.TEST_URL work
process.env.TEST_URL = BASE_URL;
process.env.TEST_USERNAME = USERNAME;
process.env.TEST_PASSWORD = PASSWORD;
if (COOKIE) process.env.TEST_COOKIE = COOKIE;

// Generate timestamped report directory
const now = new Date();
const timestamp = [
  now.getFullYear(),
  String(now.getMonth() + 1).padStart(2, '0'),
  String(now.getDate()).padStart(2, '0'),
  '-',
  String(now.getHours()).padStart(2, '0'),
  String(now.getMinutes()).padStart(2, '0'),
  String(now.getSeconds()).padStart(2, '0'),
].join('');
const reportDir = path.join(__dirname, 'reports', timestamp);

module.exports = defineConfig({
  testDir: '../scripts',
  testMatch: '**/*.spec.js',

  // Sequential execution — shared test gateway state
  workers: 1,
  fullyParallel: false,

  // No retries — deterministic execution
  retries: 0,

  // Timeouts
  timeout: 60_000,          // 60s per test
  globalTimeout: 1_800_000, // 30 minutes for entire suite

  // Global setup/teardown — test gateway lifecycle
  globalSetup: './setup.js',
  globalTeardown: './teardown.js',

  // Reporters — output to timestamped directory
  reporter: [
    ['json', { outputFile: path.join(reportDir, 'results.json') }],
    ['html', { outputFolder: path.join(reportDir, 'html') }],
    ['line'],
  ],

  // Test results (screenshots, traces) — also in timestamped dir
  outputDir: path.join(reportDir, 'test-results'),

  // Browser configuration
  use: {
    baseURL: BASE_URL,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    actionTimeout: 10_000,
    navigationTimeout: 30_000,
  },

  projects: [
    {
      name: 'bdd-tests',
      use: {
        browserName: 'chromium',
        // Reuse storage state from setup for authenticated sessions
        storageState: fs.existsSync(path.join(__dirname, 'storage-state.json'))
          ? path.join(__dirname, 'storage-state.json')
          : undefined,
      },
    },
  ],
});
