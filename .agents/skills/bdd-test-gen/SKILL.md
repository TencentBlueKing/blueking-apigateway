---
name: bdd-test-gen
description: "Generate executable Playwright test scripts from BDD case files by exploring a live BlueKing API Gateway environment. TRIGGER when: user says 'bdd-test-gen', 'generate test scripts', 'generate scripts from bdd', 'convert bdd to scripts'. DO NOT TRIGGER for: running tests (use make test-bdd), editing BDD cases, unit tests."
---

# BDD Test Script Generator

You are a test script generator for the BlueKing API Gateway dashboard. You read BDD case files (Chinese Gherkin markdown), explore a live environment via Playwright MCP browser tools, and generate executable Playwright test scripts.

## Agent Compatibility

This skill works with **any AI coding agent** that has access to:

1. **Playwright MCP browser tools** — `browser_navigate`, `browser_snapshot`, `browser_click`, `browser_run_code`, `browser_type`, etc.
2. **File system tools** — ability to read and write files
3. **Shell/terminal access** — ability to run `node`, `npx`, etc.

## Arguments

```
bdd-test-gen generate --url <URL> --user <USERNAME> --password <PASSWORD> [--case <BDD_FILE>] [--all]
bdd-test-gen generate --url <URL> --cookie <COOKIE> [--case <BDD_FILE>] [--all]
```

| Parameter | Flag | Required | Description |
|-----------|------|----------|-------------|
| Target URL | `--url` | **Yes** | Base URL of a deployed BlueKing API Gateway environment |
| Username | `--user` | Yes* | Login username |
| Password | `--password` | Yes* | Login password |
| Cookie | `--cookie` | Yes* | Cookie string (alternative to user/password) |
| BDD Case | `--case` | No | Path to a specific BDD case file to convert |
| All Cases | `--all` | No | Convert all BDD cases in `test-bdd/cases/` |

*Authentication: Either `--user` + `--password` OR `--cookie` must be provided.

### Parameter Validation

1. **Check `--url`**: If missing, prompt the user for the environment URL.
2. **Check auth**: If neither `--password` nor `--cookie` provided, prompt:
   > "Please provide authentication. Either `--user <name> --password <pass>` or `--cookie <value>`"
3. **Check `--case` or `--all`**: If neither provided, prompt for which BDD case to convert.

## Key Files Reference

- **BDD cases directory**: `test-bdd/cases/` — source BDD case files (Chinese markdown)
- **Scripts output directory**: `test-bdd/scripts/` — where generated scripts are saved
- **Shared helpers**: `test-bdd/runtime/helpers.js` — reusable functions (login, reAuth, selectDropdown, etc.)
- **Setup script**: `test-bdd/runtime/setup.js` — creates test gateway (runs before tests)
- **Teardown script**: `test-bdd/runtime/teardown.js` — deletes test gateway (runs after tests)
- **Playwright config**: `test-bdd/runtime/playwright.config.js` — test runner configuration
- **Business context**: `test-bdd/AGENTS.md` — module classification, execution order, domain gotchas
- **BDD format contract**: `specs/002-bdd-test-refactor/contracts/bdd-case-format.md`
- **Script format contract**: `specs/002-bdd-test-refactor/contracts/test-script-format.md`

**Before starting, read `test-bdd/AGENTS.md`** — it contains critical knowledge about UI patterns, selectors, and gotchas.

## Workflow

### Step 1: Authenticate

Log into the target environment using the provided credentials:

```javascript
async (page) => {
  await page.goto('{{URL}}');
  await page.waitForTimeout(3000);

  if (page.url().includes('/login/')) {
    await page.locator('input[placeholder="请输入用户名"]').click();
    await page.locator('input[placeholder="请输入用户名"]').type('{{USERNAME}}');
    await page.locator('input[placeholder="请输入密码"]').click();
    await page.locator('input[placeholder="请输入密码"]').type('{{PASSWORD}}');
    await page.locator('button').filter({ hasText: '立即登录' }).click();

    for (let i = 0; i < 30; i++) {
      await page.waitForTimeout(500);
      if (!page.url().includes('/login/')) break;
    }
  }

  return { url: page.url(), loggedIn: !page.url().includes('/login/') };
}
```

### Step 2: Parse BDD Case File

Read the target BDD case file and extract:

1. **功能** (Feature): The `# 功能:` header — becomes `test.describe()` label
2. **模块** (Module): The `**模块**:` field — determines output directory
3. **页面** (Page): The `**页面**:` field — the URL path to navigate to
4. **前置条件** (Prerequisites): Runtime dependencies
5. **场景[]** (Scenarios): Each `## 场景:` section — becomes a `test()` block
   - **假设** steps → test preconditions/assertions
   - **当** / **并且** steps → Playwright interactions
   - **那么** / **并且** steps → `expect()` assertions

### Step 3: Explore the Live Page

For each **页面** (page path) in the BDD case:

1. Navigate to `{{URL}}` + page path (replace `:gatewayId` with a real gateway ID)
2. Use `browser_run_code` with a compact element extraction to understand the page:

```javascript
async (page) => {
  await page.goto('{{URL}}/{{PAGE_PATH}}');
  await page.waitForTimeout(2000);

  // Extract interactive elements
  const buttons = await page.locator('button').allTextContents();
  const inputs = await page.locator('input').evaluateAll(els =>
    els.map(e => ({ placeholder: e.placeholder, type: e.type, name: e.name }))
  );
  const selects = await page.locator('.bk-select, select').count();
  const tables = await page.locator('table, .bk-table').count();

  return { buttons, inputs, selects, tables };
}
```

3. For each **当** (When) step in the BDD scenario, actually perform the action on the live page:
   - Click buttons → discover the exact selector that works
   - Fill inputs → discover placeholder text and field selectors
   - Select dropdowns → discover option values and interaction patterns
   - Wait for responses → discover appropriate wait conditions

4. For each **那么** (Then) step, verify the expected outcome on the live page:
   - Check for success messages → discover toast/notification selectors
   - Verify table content → discover table row structure
   - Verify page state → discover state indicators

### Step 4: Generate the Test Script

Based on the discovered selectors and interactions, generate a `.spec.js` file:

```javascript
// @generated from: test-bdd/cases/{{MODULE}}/{{CASE}}.md
// @generated-date: {{DATE}}

const { test, expect } = require('@playwright/test');
const { login, reAuth, waitForPageReady, selectDropdown, closeSlider, getToastMessage, getTableRowCount } = require('../helpers');

const BASE_URL = process.env.TEST_URL;
const GATEWAY_ID = process.env.TEST_GATEWAY_ID;

test.describe('功能: {{FEATURE_TITLE}}', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/{{PAGE_PATH}}`);
    await waitForPageReady(page);

    // Re-authenticate if session expired
    if (page.url().includes('/login/')) {
      await reAuth(page);
      await page.goto(`${BASE_URL}/{{PAGE_PATH}}`);
      await waitForPageReady(page);
    }
  });

  test('场景: {{SCENARIO_NAME}}', async ({ page }) => {
    // 假设: {{PRECONDITION}}
    // {{precondition assertions}}

    // 当: {{ACTION}}
    // {{discovered playwright interactions}}

    // 那么: {{EXPECTED_OUTCOME}}
    // {{expect assertions}}
  });
});
```

### Step 5: Verify the Generated Script

1. Run the generated script to confirm it passes:

```bash
cd test-bdd/runtime && npx playwright test {{MODULE}}/{{CASE}}.spec.js --reporter=line
```

2. If the script fails:
   - Read the error message
   - Adjust selectors, waits, or interactions
   - Re-run (max 3 attempts)

3. If the script passes after adjustment, save the final version.

4. If the script still fails after 3 attempts, report the issue:
   > "Script for {{CASE}} fails after 3 attempts. Error: {{error}}. This may indicate a genuine application issue or a UI pattern not yet handled."

### Step 6: Save the Script

Save to: `test-bdd/scripts/{{MODULE_DIR}}/{{CASE_NAME}}.spec.js`

The output path mirrors the BDD case path:
- BDD: `test-bdd/cases/01-网关管理/01-创建网关.md`
- Script: `test-bdd/scripts/01-网关管理/01-创建网关.spec.js`

## Script Generation Rules

1. **Import from helpers.js** — never reimplement login, dropdown, or slider logic inline
2. **Use environment variables** — `TEST_URL`, `TEST_USER`, `TEST_PASSWORD`, `TEST_COOKIE`, `TEST_GATEWAY_ID`
3. **Mutating operations** use `GATEWAY_ID` (the test gateway); read-only use any gateway
4. **BkSelect dropdowns**: Never use `Escape` to close. Use `body.click()` at position (10,10)
5. **Timeouts**: Use `waitForTimeout(800)` standard, `waitForTimeout(300)` for dropdowns
6. **Screenshots**: Let Playwright Test capture automatically on failure — do not add manual screenshot code
7. **One `test.describe` per file**, one `test()` per `## 场景`
8. **Add `@generated from:` comment** at the top linking to the source BDD case

## Batch Mode (`--all`)

When `--all` is specified:

1. List all `.md` files in `test-bdd/cases/` recursively
2. For each BDD case file, run Steps 2-6
3. Report progress: "Generating script X/N: {{module}}/{{case}}"
4. At the end, report summary: "Generated N scripts, M passed verification, K failed"

## Incremental Mode

When a specific `--case` is provided:

1. Read only that BDD case file
2. If a corresponding `.spec.js` already exists, overwrite it
3. Run Steps 2-6 for that single case
4. Report result

## Domain Gotchas

**Read `test-bdd/AGENTS.md` for the full list.** Key gotchas:

- **Login form**: Two variants — Chinese (`请输入用户名/请输入密码/立即登录`) and English (`#user/#password/.login-btn`)
- **BkSelect dropdowns**: Never use `Escape`. Click `body` at (10,10) to dismiss, then click the dropdown to open
- **Sideslider close**: May trigger a confirmation dialog — handle with `closeSlider()` from helpers
- **Backend service**: Must be configured before resource creation — backend address cannot be empty
- **Version generation**: Button is disabled if no resource changes since last version
- **Publish flow**: "生成版本" → "下一步" → "确定" → "立即发布" → select stage → "下一步" → "确认发布" → InfoBox confirm
- **Gateway deletion**: Must deactivate (停用) first, then delete (删除), may require typing gateway name in confirm dialog
