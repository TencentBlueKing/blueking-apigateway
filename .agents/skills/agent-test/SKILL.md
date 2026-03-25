---
name: agent-test
description: "Browser-based regression test runner and test case generator for the BlueKing API Gateway dashboard. TRIGGER when: user says /agent-test, 'run regression tests', 'run test cases', 'test the dashboard', 'run agent tests', 'generate test cases', 'create test cases for this page', 'browser test'. DO NOT TRIGGER for: unit tests, API tests, pytest, backend tests."
---

# Agent Test Suite

You are a browser-based regression test runner for the BlueKing API Gateway dashboard. You execute structured markdown test cases using Playwright MCP browser tools and produce detailed reports.

**Before starting any test run, read `test/agent-tests/AGENTS.md`** — it contains critical knowledge about URL route mappings, form selectors, and common gotchas from previous runs.

## Arguments

All connection parameters are passed as arguments. **Nothing is hardcoded or read from config files.**

```
/agent-test run --url <URL> --user <USERNAME> --password <PASSWORD> [--cases <DIR>] [--excel <FILE>]
/agent-test run --url <URL> --cookie <COOKIE> [--cases <DIR>] [--excel <FILE>]
/agent-test generate --url <URL> --user <USERNAME> --password <PASSWORD> [--cases <DIR>]
```

| Parameter | Flag | Required | Default |
|-----------|------|----------|---------|
| Target URL | `--url` | **Yes** | None — must be provided |
| Username | `--user` | Yes* | None — must be provided |
| Password | `--password` | Yes* | None — must be provided |
| Cookie | `--cookie` | Yes* | None — alternative to user/password |
| Cases directory | `--cases` | No | `test/agent-tests/cases/` |
| Excel file | `--excel` | No | None — if provided, converts Excel to cases first |

*Authentication: Either `--user` + `--password` OR `--cookie` must be provided.

### Excel Input (`--excel`)

When `--excel` is provided, the skill converts the Excel file to markdown test cases **before** running tests:

1. Run `python3 test/agent-tests/convert_excel.py <EXCEL_FILE> --output-dir <CASES_DIR>` via Bash
2. The Excel file must be `.xlsx` format with columns: 模块 | 用例名称 | 用例等级 | 前置条件 | 用例步骤 | 预期结果 | 实际结果 | 备注 | 用例版本
3. The converter reads the first sheet by default (add `--sheet N` for other sheets)
4. Cases are grouped by module into subdirectories (e.g., `01-my-gateway/`, `02-resource-config/`)
5. After conversion completes, proceed with normal `run` mode using the generated cases directory

**The converter has no third-party dependencies** — it parses .xlsx XML directly with Python stdlib.

### Parameter Validation

Before starting any mode:

1. **Check `--url`**: If missing, prompt:
   > "Please provide the target URL. Example: `/agent-test run --url https://example.com --user admin --password xxx`"
2. **Check auth**: If neither `--password` nor `--cookie` provided, prompt:
   > "Please provide authentication. Either `--user <name> --password <pass>` or `--cookie <value>`"
3. **Check cases dir**: If `--cases` not provided, use default `test/agent-tests/cases/`. Verify the directory exists.
4. **Check `--excel`**: If provided, verify the file exists and ends with `.xlsx`. Run conversion before proceeding.
5. **For generate mode**: `--url` is the page to generate cases for (not just the base URL).

**NEVER read passwords from files. NEVER store passwords in config or skill files.**

### Permission Pre-Acquisition (CRITICAL)

Before starting any test execution, **verify all required permissions are pre-allowed** so the run never pauses for approval. Run this check at the very beginning:

```bash
# Verify these permissions exist in .claude/settings.local.json:
# - All mcp__plugin_playwright_playwright__browser_* tools
# - Bash(python3:*), Bash(mkdir:*), Bash(grep:*), Bash(ls:*), etc.
# - Read for the project directory
# - Write/Edit for test/agent-tests/**
```

If any Playwright MCP browser tool or Bash command triggers a permission prompt during execution, **STOP and tell the user** to add it to `.claude/settings.local.json` before continuing. The test run must execute end-to-end without any interactive permission prompts.

The required permissions are already configured in `.claude/settings.local.json`. If running in a fresh session or different project, ensure these are set:

1. **All Playwright MCP tools**: `mcp__plugin_playwright_playwright__browser_*` (navigate, snapshot, click, run_code, type, evaluate, take_screenshot, etc.)
2. **Bash tools**: `python3:*`, `mkdir:*`, `grep:*`, `ls:*`, `find:*`, `head:*`, `tail:*`, `wc:*`
3. **Read**: project directory and `/private/tmp/**`
4. **Write/Edit**: `test/agent-tests/**`

## Data Safety Rules (CRITICAL)

**These rules are non-negotiable and override any test case instructions that conflict with them.**

### Rule 1: Never Modify Existing Gateways

- **Existing gateways are READ-ONLY.** You may navigate to them, view their pages, verify UI elements, and read data — but you MUST NOT create, update, or delete any resources, environments, stages, plugins, permissions, backend services, or any other data within an existing gateway.
- This applies to ALL gateways that existed before the test run started.
- "View-only" operations include: page navigation, reading tables/lists, using filters/search/sort, expanding details, viewing logs, checking tooltips — anything that does not change server-side state.

### Rule 2: Use a Dedicated Test Gateway for Mutating Operations

- **All create / update / delete test cases MUST be executed in a newly created test gateway**, not in any pre-existing gateway.
- At the start of `run` mode (after authentication, before executing cases), create a dedicated test gateway:
  1. Click "新建网关" on the home page
  2. Use a unique name like `test-agent-<timestamp>` (e.g., `test-agent-20260325`)
  3. Select "普通网关" type, set to "不公开" (private), fill required fields
  4. Submit and record the new gateway's ID from the URL
- All cases that involve creating resources, editing configurations, publishing, deleting, or any write operation MUST target this test gateway.
- At the end of the test run (after all cases complete and the report is written), **clean up**: navigate to the test gateway's basic info page and delete it. If deletion fails, note it in the report.

### Rule 3: How to Classify Cases

When reading test cases, classify each case as **read-only** or **mutating**:

| Operation Type | Examples | Where to Run |
|----------------|----------|--------------|
| **Read-only** | View page, filter list, search, sort, check UI elements, verify text, navigate | Any existing gateway |
| **Mutating** | Create resource, edit config, delete record, publish version, update permissions, toggle settings | Test gateway ONLY |

If a case is ambiguous, treat it as **mutating** and run it in the test gateway.

### Rule 4: Never Skip Cases

- **Every single test case MUST be executed.** You are not allowed to skip cases, batch them as "page-load only", or mark them as "skipped" to save time.
- For each case, you MUST: read its steps, translate them into Playwright actions, execute them in the browser, and verify the expected outcomes.
- **If a case cannot be executed** (e.g., missing prerequisite data, UI element not found, page error, unclear steps), you MUST:
  1. Mark it as **BLOCKED** (not SKIPPED) in the report
  2. Include the **specific reason** why it cannot run (e.g., "Button '发布' not found on page", "Requires pre-existing published version which does not exist")
  3. **Tell the user immediately** during execution — do not silently skip and only mention it in the final report
- **If execution is taking too long**, tell the user the progress (e.g., "Completed 200/835 cases, currently on module 12") and ask whether to continue — do NOT decide on your own to skip remaining cases.
- **"Too many cases" is not a valid reason to skip.** The skill is designed for large-scale execution. Batch aggressively, but execute every case.
- The only acceptable reasons for not executing a case are:
  - The target page returns a server error (500, 502, etc.)
  - Authentication fails and cannot be recovered
  - The user explicitly asks to stop or skip
  - A prerequisite case failed and this case depends on its result (mark as BLOCKED with dependency noted)

## Session Re-Authentication

During `run` mode, if ANY `browser_run_code` call detects the page has redirected to the login page:

```javascript
const currentUrl = page.url();
if (currentUrl.includes('/login/')) {
  // Session expired — re-authenticate using the same credentials from args
}
```

**Re-auth flow:**
1. Log the session expiry: "Session expired at batch [X]. Re-authenticating..."
2. Execute the full login flow via `browser_run_code` using the original `--user`/`--password` or `--cookie` args
3. Navigate back to the page that was being tested
4. Retry the batch that triggered the expiry detection
5. If re-auth fails, mark ALL remaining cases as ERROR with reason "Authentication failed after session expiry"

## Performance Rules (CRITICAL)

The #1 bottleneck is **LLM round-trip overhead per tool call** (~5-10s each). Minimizing the number of `browser_run_code` calls is the single most important optimization.

### Batching Strategy

**Batch ALL cases that share the same page into ONE `browser_run_code` call.** This is the core optimization.

```
# BAD: 1 call per case step = N*M tool calls for N cases with M steps
# Each tool call adds ~5-10s LLM overhead regardless of browser execution time

# GOOD: 1 call per page batch = drastically fewer tool calls
# All cases for the same page run in one browser_run_code block
```

**How to batch:**
1. After parsing all cases, group them by their **Page** field
2. For each page group, generate ONE `browser_run_code` call that:
   - Navigates to the page once
   - Executes ALL cases for that page sequentially within the same function
   - Collects results for each case in a structured object
   - Takes screenshots ONLY on failure
   - Returns all results at once

**Batch size limit**: If a page group has more than ~15 cases, split into sub-batches of 10-15 cases per `browser_run_code` call to avoid timeouts. Set `timeout: 120000` (2 minutes) for large batches.

### Screenshot Rules

- **NEVER take screenshots for passing cases** — they waste ~10s per call
- **ONLY take screenshots on failure** — capture the failure state for debugging
- Take failure screenshots INSIDE the `browser_run_code` call using `await page.screenshot({ path: '...' })` to avoid an extra tool call
- For the final report, note which cases have failure screenshots

### Wait Time Rules

- Use `waitForTimeout(800)` as the standard wait after UI interactions (dropdown select, search submit, sort change)
- Use `waitForTimeout(300)` for dropdown animation open/close
- Use `waitForSelector` or `waitForResponse` instead of fixed waits when possible
- NEVER use `waitForTimeout(1500)` or higher unless waiting for a known slow API

### Token Efficiency

**NEVER use `browser_snapshot` in run mode.** Use `browser_run_code` for everything.

**`browser_snapshot`** is ONLY allowed in `generate` mode (discovering unknown pages).

### Dropdown Interaction Pattern

Always use `force: true` on dropdown clicks and `Escape` before re-opening to avoid overlay issues:

```javascript
await page.keyboard.press('Escape');
await page.waitForTimeout(100);
await dropdownLocator.click({ force: true });
await page.waitForTimeout(300);
await page.locator('.bk-select-option').filter({ hasText: 'option text' }).click();
await page.waitForTimeout(800);
```

## Subcommands

- **`run`** — Execute test cases from a cases directory against the target URL
- **`generate`** — Explore a page and generate new test case files

Parse the user's input to determine which mode. Default to `run` if no subcommand specified.

---

## Run Mode: `/agent-test run`

### Step 1: Pre-Analyze Pages (Source Code First)

Before touching the browser, understand what you'll be testing:

1. Read all test case files from the cases directory
2. Extract the **Page** field from each case (e.g., `/`, `/gateways/123/resources`)
3. **Group cases by Page** — this determines your batching
4. For each unique page, read the corresponding Vue component:
   - Read the router config at `src/dashboard-front/src/router/index.ts` to map URL paths to component files
   - Read the Vue component file (e.g., `src/dashboard-front/src/views/home/Index.vue` for `/`)
   - Extract: element selectors, CSS classes, component structure, v-model bindings, event handlers
5. Build a **selector map** for each page — used in `browser_run_code` calls

### Step 2: Authenticate and Create Test Gateway

Use a single `browser_run_code` call for the entire login flow. Substitute `{{URL}}`, `{{USERNAME}}`, `{{PASSWORD}}` with the actual values from the command args.

**Login page has TWO possible forms** (detected dynamically):
- Chinese form: fields by `#user` and `#password` IDs, button `.login-btn`
- English form: fields by role `textbox` with name, button by role

**Credentials mode** (`--user` + `--password`):

```javascript
async (page) => {
  await page.goto('{{URL}}');
  await page.waitForTimeout(3000);
  const url = page.url();

  if (url.includes('/login/')) {
    const hasIdUser = await page.locator('#user').isVisible().catch(() => false);
    if (hasIdUser) {
      // Chinese form — use .type() for special chars
      await page.locator('#user').click();
      await page.locator('#user').type('{{USERNAME}}');
      await page.locator('#password').click();
      await page.locator('#password').type('{{PASSWORD}}');
      await page.locator('.login-btn').click();
    } else {
      // English form
      await page.getByRole('textbox', { name: 'Please enter your username' }).fill('{{USERNAME}}');
      await page.getByRole('textbox', { name: 'Please enter your password' }).fill('{{PASSWORD}}');
      await page.getByRole('button', { name: 'Log in' }).click();
    }
    for (let i = 0; i < 30; i++) {
      await page.waitForTimeout(500);
      if (!page.url().includes('/login/')) break;
    }
  }

  await page.getByText('新建网关').waitFor({ timeout: 10000 });
  return { url: page.url(), loggedIn: true };
}
```

**Cookie mode** (`--cookie`):

```javascript
async (page) => {
  const domain = new URL('{{URL}}').hostname.split('.').slice(-2).join('.');
  await page.context().addCookies([{ name: 'COOKIE_NAME', value: '{{COOKIE}}', domain: '.' + domain, path: '/' }]);
  await page.goto('{{URL}}');
  await page.getByText('新建网关').waitFor({ timeout: 10000 });
  return { url: page.url(), loggedIn: true };
}
```

**Auth failure**: If login fails (timeout on dashboard content, or "密码错误" message), report and STOP.

**After successful authentication, create the test gateway** (see Data Safety Rules above):

```javascript
// After login, create test gateway for mutating operations
async (page) => {
  await page.getByText('新建网关').first().click({ force: true });
  await page.waitForTimeout(800);
  const ni = page.locator('input[placeholder*="小写字母"]');
  const testName = 'test-agent-' + Date.now().toString().slice(-8);
  await ni.fill(testName);
  // ... fill other required fields, set to private, submit
  // Record the gateway ID from the resulting URL
  return { testGatewayName: testName, testGatewayId: '...' };
}
```

Use the test gateway ID for ALL mutating test cases. Use any existing gateway ID for read-only cases.

### Step 3: Execute Test Cases (BATCHED)

**This is where batching matters most.**

For each page group (cases sharing the same Page field):

1. **Generate ONE `browser_run_code` function** that executes ALL cases for that page
2. The function should:
   - Navigate to the page once at the start (using `{{URL}}` + page path)
   - Wait for page load
   - For each case in the group:
     - Execute all steps sequentially
     - Run all verifications
     - On failure: take screenshot with `await page.screenshot({ path: 'FILENAME' })`
     - Record result as PASSED/FAILED with details
     - Reset page state for next case (e.g., clear filters, restore defaults)
   - Return a structured results object

**Batch template:**

```javascript
async (page) => {
  const results = {};

  // Navigate once
  await page.goto('{{URL}}' + PAGE_PATH);
  await page.waitForTimeout(1500); // initial page load

  // --- Case: [case-name-1] ---
  try {
    // Steps...
    await page.locator('...').click({ force: true });
    await page.waitForTimeout(800);

    // Verify...
    const count = await page.locator('...').count();
    const pass = count > 0;

    if (!pass) {
      await page.screenshot({ path: 'case-name-1-FAIL.png' });
    }
    results['case-name-1'] = { pass, details: { count }, steps: '3/3' };
  } catch (e) {
    await page.screenshot({ path: 'case-name-1-ERROR.png' }).catch(() => {});
    results['case-name-1'] = { pass: false, error: e.message, steps: 'error' };
  }

  // Reset state for next case
  // (e.g., clear search, reset filters to defaults)

  // --- Case: [case-name-2] ---
  try {
    // ...same pattern...
  } catch (e) { /* ... */ }

  return results;
}
```

**Important batching rules:**
- Each case in the batch is wrapped in its own `try/catch` — one failure does NOT skip remaining cases
- Reset UI state between cases (clear inputs, reset dropdowns to defaults)
- Use `force: true` on clicks to avoid overlay interception issues
- Always `Escape` before opening a new dropdown
- **Data Safety**: Read-only cases use an existing gateway ID; mutating cases (create/update/delete) use the test gateway ID only (see Data Safety Rules)

### Step 4: Verify Outcomes

Verifications are done INSIDE the batch function (Step 3), not as separate tool calls.

### Step 5: Generate Report

After all batches executed:

1. Create report directory: `test/agent-tests/reports/YYYY-MM-DDTHH-MM-SS/`
2. Move any failure screenshots to `screenshots/` subdirectory
3. Write `report.md`:

```markdown
# Test Run Report

**Date**: [YYYY-MM-DD HH:MM:SS]
**Target**: [base URL from --url]
**Auth Method**: [credentials | cookie]
**Duration**: [total time]
**Batches**: [N browser_run_code calls for M cases]

## Summary

| Metric   | Count |
|----------|-------|
| Total    | [N]   |
| Passed   | [N]   |
| Failed   | [N]   |
| Skipped  | [N]   |
| Errors   | [N]   |

## Results

### [icon] [case-filename] — [STATUS] ([duration])

Steps completed: [completed]/[total]
[If FAILED: **Failure at step N**: Expected ... but observed ...]
[If FAILED: Screenshot: [link to failure screenshot]]
[If SKIPPED: **Reason**: ...]

---
```

Status icons: ✅ PASSED, ❌ FAILED, ⏭️ SKIPPED, ⚠️ ERROR

4. Output report path and summary to user.

### Step 6: Clean Up Test Gateway

After the report is written, delete the test gateway created in Step 2:

1. Navigate to the test gateway's basic info page (`{{URL}}/{{TEST_GW_ID}}/basic/info`)
2. Find and click the "删除网关" or "停用" button
3. Confirm deletion in the dialog
4. Verify the gateway no longer appears on the home page
5. If cleanup fails, note it in the report under a "Cleanup" section

**NEVER skip cleanup** — leftover test gateways pollute the environment.

### Error Handling

- **Site unreachable**: Report error, do not attempt cases
- **Auth failure**: Report, suggest cookie mode fallback
- **Element not found**: Record error with selector attempted, screenshot inside batch + mark failed + continue to next case in batch
- **Timeout**: 10 second max wait per element. If exceeded, mark error, continue to next case.
- **Session expired**: If page redirects to login mid-batch, re-authenticate via `browser_run_code` using original args, retry the batch. If re-auth fails, mark remaining as errors.

---

## Generate Mode: `/agent-test generate`

```
/agent-test generate --url <PAGE_URL> --user <USERNAME> --password <PASSWORD> [--cases <DIR>]
```

`--url` is the specific page to explore (e.g., `https://example.com/gateways/123/resources`).

### Step 1: Map URL to Vue Component (Source Code First)

1. Read the Vue router at `src/dashboard-front/src/router/index.ts`
2. Match the given URL path to a route entry. Key mappings:
   - `/` → `src/dashboard-front/src/views/home/Index.vue`
   - `/:id` → `src/dashboard-front/src/layout/my-gateway/Index.vue` (with child routes)
   - `/:id/stage` → find in `src/dashboard-front/src/views/stage-management/route.ts`
   - `/:id/resource` → find in `src/dashboard-front/src/views/resource-management/route.ts`
   - `/component` → find in `src/dashboard-front/src/views/component-management/route.ts`
   - `/platform-tools` → find in `src/dashboard-front/src/views/platform-tools/routes.ts`
   - `/api-docs` → find in `src/dashboard-front/src/views/api-docs/route.ts`
3. If the URL has sub-route files (e.g., `route.ts` or `routes.ts` in the view directory), read those too.

### Step 2: Analyze Vue Component

Read the matched Vue component file and extract:

1. **Template section**: All interactive elements — `<bk-button>`, `<bk-select>`, `<bk-input>`, `<bk-table>`, `<bk-dialog>`, `<bk-form>`, links, etc.
2. **Script section**:
   - `v-model` bindings → tells you what data each form element controls
   - `@click`, `@change`, `@input`, `@submit` handlers → tells you what actions are possible
   - API calls (`fetch`, `axios`, composables) → tells you what data operations happen
   - `ref()` and `reactive()` → tells you what state the page manages
3. **Key UI patterns to identify**:
   - Dropdowns/filters → generate filter test cases
   - Search inputs → generate search test cases
   - Tables/lists → generate data display verification cases
   - Forms → generate form submission cases
   - Buttons → generate action trigger cases
   - Dialogs/modals → generate dialog interaction cases
   - Pagination → generate pagination test cases

### Step 3: Explore Page in Browser (ONE Snapshot)

1. Authenticate using `--user`/`--password` or `--cookie` args (same as run mode)
2. Navigate to `{{URL}}`
3. Use ONE `browser_snapshot` to capture the live accessibility tree
4. Use ONE `browser_run_code` to gather dynamic details:

```javascript
async (page) => {
  return {
    url: page.url(),
    title: await page.title(),
    buttons: await page.getByRole('button').count(),
    textboxes: await page.getByRole('textbox').count(),
    comboboxes: await page.getByRole('combobox').count(),
    links: await page.getByRole('link').count(),
    headings: await page.locator('h1, h2, h3').allTextContents(),
  };
}
```

### Step 4: Cross-Reference and Generate Cases

For each interactive element group found in BOTH source analysis AND live page:

1. **Determine test scenario**: What user action does this element support? What should happen?
2. **Write a markdown test case file** following the format:

```markdown
# Case: [Page Name] - [Interaction Description]

**Page**: [URL path]
**Prerequisites**: Logged in

## Steps

1. Navigate to [page description]
2. [Interaction step from source analysis]
3. [Wait for response]

## Verify

- [Expected outcome based on source code handlers and API calls]
```

3. **Name the file**: `case[N]-[page]-[interaction].md`
   - Determine the next available case number by reading existing files in the cases directory
4. **Group related interactions**: Don't create one case per button — group logically:
   - All filter dropdowns on a page → one case per filter type
   - Form with multiple fields → one case for the form
   - Table with sort/pagination → one case for data interaction

### Step 5: Write Files and Report

1. Write all generated case files to the cases directory
2. Output summary:
   - Number of cases generated
   - List of file names with brief descriptions
   - Any elements that were found in source but not on the live page (potential issues)
   - Any elements on the live page not found in source (dynamic content)

---

## Key Files Reference

- **Cases directory**: `test/agent-tests/cases/`
- **Reports directory**: `test/agent-tests/reports/`
- **Vue router**: `src/dashboard-front/src/router/index.ts`
- **Vue views**: `src/dashboard-front/src/views/`
- **Test case format contract**: `specs/001-agent-test-suite/contracts/test-case-format.md`
- **Report format contract**: `specs/001-agent-test-suite/contracts/test-report-format.md`
