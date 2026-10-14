const { defineConfig } = require('@playwright/test');
module.exports = defineConfig({
  testDir: '.',
  testMatch: 'guard-probe.fixture.js',
  timeout: 10000,
  workers: 1,
  use: { screenshot: 'only-on-failure', trace: 'retain-on-failure' },
  reporter: [['json', { outputFile: process.env.BDD_GUARD_REPORT || '/tmp/bdd-guard-probe.json' }]],
  outputDir: process.env.BDD_GUARD_OUTPUT || '/tmp/bdd-guard-probe-results',
});
