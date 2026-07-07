// Shared Playwright test wrapper for BDD specs that need production-gate checks.
const base = require('@playwright/test');
const {
  attachHardFailureGuard,
  assertNoHardFailure,
} = require('./helpers');

const test = base.test.extend({
  page: async ({ page }, use, testInfo) => {
    attachHardFailureGuard(page);
    await use(page);
    await assertNoHardFailure(page, testInfo.title);
  },
});

module.exports = {
  ...base,
  test,
  expect: base.expect,
};
