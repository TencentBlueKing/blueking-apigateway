const { defineConfig } = require('@playwright/test');
module.exports = defineConfig({
  testDir: '.', testMatch: 'control-probe.fixture.js', workers: 1, timeout: 10000,
  outputDir: '/tmp/bdd-control-results',
});
