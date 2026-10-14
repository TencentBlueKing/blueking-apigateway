// Shared Playwright test wrapper for BDD specs that need production-gate checks.
const base = require('@playwright/test');
const {
  attachHardFailureGuard,
  assertNoHardFailure,
  waitForBackendRequests,
} = require('./helpers');

const test = base.test.extend({
  expectedPageErrors: [[], { option: true }],
  page: async ({ page, expectedPageErrors }, use, testInfo) => {
    const state = attachHardFailureGuard(page, { expectedPageErrors });
    await use(page);
    await waitForBackendRequests(page);
    if (state.diagnostics.length) await testInfo.attach('expected-validation-events', {
      body: state.diagnostics.join('\n'), contentType: 'text/plain',
    });
    await assertNoHardFailure(page, testInfo.title);
  },
});

module.exports = {
  ...base,
  test,
  expect: base.expect,
};
