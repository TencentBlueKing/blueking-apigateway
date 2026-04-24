# Contract: Test Script Format

**Version**: 1.0
**Date**: 2026-03-30

## File Location

```
test/bdd-scripts/<NN-模块名>/<NN-场景名>.spec.js
```

Mirrors the BDD case directory structure with `.spec.js` extension.

## Environment Variables (Required at Runtime)

| Variable | Required | Description |
|----------|----------|-------------|
| `TEST_URL` | Yes | Base URL of the target environment |
| `TEST_USER` | Yes* | Username for authentication |
| `TEST_PASSWORD` | Yes* | Password for authentication |
| `TEST_COOKIE` | Yes* | Cookie string (alternative to user/password) |
| `TEST_GATEWAY_ID` | Auto | Set by setup.js, ID of the test gateway |

*Either `TEST_USER` + `TEST_PASSWORD` or `TEST_COOKIE` must be provided.

## Script Structure

```javascript
// @generated from: test/bdd-cases/<module>/<case>.md
// @generated-date: YYYY-MM-DD

const { test, expect } = require('@playwright/test');
const { login, reAuth, createTestData } = require('../helpers');

const BASE_URL = process.env.TEST_URL;
const GATEWAY_ID = process.env.TEST_GATEWAY_ID;

test.describe('功能: [模块名] - [功能描述]', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate to the target page
    await page.goto(`${BASE_URL}/[page-path]`);
    await page.waitForLoadState('networkidle');
  });

  test('场景: [场景名称]', async ({ page }) => {
    // 假设: [precondition]
    // ... setup assertions

    // 当: [user action]
    // ... playwright interactions

    // 那么: [expected outcome]
    // ... expect assertions
  });

  test('场景: [another scenario]', async ({ page }) => {
    // ...
  });
});
```

## Rules

1. Each script file has a `@generated from:` comment linking to its BDD source
2. One `test.describe` per `# 功能`
3. One `test()` per `## 场景`
4. All URLs are relative to `TEST_URL` environment variable
5. Authentication is handled by `helpers.js` — scripts do not hardcode credentials
6. Mutating tests use `GATEWAY_ID` (the shared test gateway)
7. Read-only tests may use any existing gateway
8. On session expiry detection, call `reAuth()` from helpers
9. Screenshots captured automatically on failure by Playwright Test runner
10. No `console.log` in scripts — use Playwright's built-in reporting

## Shared Files

### helpers.js

```javascript
module.exports = {
  login(page),           // Full login flow using env vars
  reAuth(page),          // Re-authenticate on session expiry
  waitForPageReady(page), // Wait for page load + API calls
  fillForm(page, fields), // Fill multiple form fields
  selectDropdown(page, selector, text), // BkSelect dropdown interaction
  closeSlider(page),     // Close sideslider with confirmation
  getToastMessage(page), // Read toast notification text
  getTableRowCount(page), // Count visible table rows
};
```

### setup.js

- Logs in using `TEST_URL` + credentials
- Creates a test gateway (普通网关, private)
- Configures backend service (httpbin.org:80)
- Creates a test resource
- Generates a resource version and publishes to prod
- Exports `TEST_GATEWAY_ID` for downstream scripts

### teardown.js

- Navigates to test gateway basic info
- Deactivates (停用) and deletes (删除) the test gateway
- Verifies deletion on home page
