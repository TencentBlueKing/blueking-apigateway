// This command passes only when every deliberately broken probe fails for its
// intended reason. Probe failures are not site bugs or an ordinary suite failure.
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { spawnSync } = require('node:child_process');
const assert = require('node:assert/strict');

const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'bdd-guard-'));
const report = path.join(dir, 'results.json');
const run = spawnSync(process.execPath, [
  require.resolve('@playwright/test/cli'), 'test',
  '--config', path.join(__dirname, 'guard-integration.config.js'),
], {
  env: { ...process.env, BDD_GUARD_REPORT: report, BDD_GUARD_OUTPUT: path.join(dir, 'artifacts') },
  encoding: 'utf8',
  timeout: 60000,
});
assert.equal(run.status, 1, run.stderr || run.stdout);
const results = JSON.parse(fs.readFileSync(report, 'utf8'));
const specs = results.suites.flatMap(suite => suite.specs);
assert.equal(specs.length, 3);
for (const spec of specs) {
  const result = spec.tests[0].results[0];
  assert.equal(result.status, 'failed', `${spec.title} incorrectly passed`);
  assert.match(result.errors.map(error => error.message).join('\n'), /BDD hard failure guard detected/);
  assert.ok(result.duration < 10000, `${spec.title} failed by timeout instead of detecting the defect`);
}
console.log('PASS: uncaught exception, immediate HTTP 500, and delayed HTTP 500 all fail the test.');
console.log(`Probe report: ${report}`);
