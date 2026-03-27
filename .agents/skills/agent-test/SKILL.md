---
name: agent-test
description: "Browser-based regression test runner and test case generator for the BlueKing API Gateway dashboard. TRIGGER when: user says agent-test, 'run regression tests', 'run test cases', 'test the dashboard', 'run agent tests', 'generate test cases', 'create test cases for this page', 'browser test'. DO NOT TRIGGER for: unit tests, API tests, pytest, backend tests."
---

# Agent Test Suite

You are a browser-based regression test runner for the BlueKing API Gateway dashboard. You execute structured markdown test cases using Playwright MCP browser tools and produce detailed reports.

## Agent Compatibility

This skill is designed to work with **any AI coding agent** that has access to:

1. **Playwright MCP browser tools** — `browser_navigate`, `browser_snapshot`, `browser_click`, `browser_run_code`, `browser_type`, `browser_evaluate`, `browser_take_screenshot`, etc.
2. **File system tools** — ability to read, write, and edit files
3. **Shell/terminal access** — ability to run `python3`, `mkdir`, `ls`, `grep`, etc.

### Tool Name Mapping

Different agent platforms use different tool names. Map these generic operations to your platform:

| Operation | Claude Code | Codex | Cursor / Generic |
|-----------|-------------|-------|------------------|
| Read a file | `Read` tool | `read_file` | Read the file content |
| Write a file | `Write` tool | `write_file` | Write/create the file |
| Edit a file | `Edit` tool | `patch_file` | Apply text replacement |
| Run shell command | `Bash` tool | `shell` | Run in terminal |
| Search files | `Glob` / `Grep` tool | `shell` with find/grep | Search in workspace |
| Run Playwright code | `browser_run_code` MCP tool | Same (MCP tools are universal) | Same |

### Invocation

This skill can be invoked in different ways depending on your agent platform:

- **Claude Code**: `/agent-test run --url <URL> --user <USER> --password <PASS>`
- **Codex / Other agents**: Read this file (`SKILL.md`) and follow the instructions below with the provided arguments
- **Any agent**: Parse the arguments from the user's message and follow the step-by-step workflow

### Playwright MCP Installation (Codex-first)

Use the official install intro:
`https://raw.githubusercontent.com/microsoft/playwright-mcp/refs/heads/main/README.md`

Before any `agent-test run` or `agent-test generate`, run this preflight in shell:

```bash
# 1) Verify the Playwright MCP package is accessible
npx -y @playwright/mcp@latest --help

# 2) If Codex CLI is available, register MCP server
if command -v codex >/dev/null 2>&1; then
  codex mcp add playwright npx "@playwright/mcp@latest" || true
  codex mcp list | grep -i playwright
fi
```

If `codex` CLI is not available, configure `~/.codex/config.toml` manually:

```toml
[mcp_servers.playwright]
command = "npx"
args = ["@playwright/mcp@latest"]
```

If package access or MCP registration fails, STOP and ask the user to fix installation before running tests.

**Before starting any test run, read `test/agent-tests/AGENTS.md`** — it contains critical knowledge about URL route mappings, form selectors, and common gotchas from previous runs.

## Arguments

All connection parameters are passed as arguments. **Nothing is hardcoded or read from config files.**

```
agent-test run --url <URL> --user <USERNAME> --password <PASSWORD> [--cases <DIR>] [--excel <FILE>]
agent-test run --url <URL> --cookie <COOKIE> [--cases <DIR>] [--excel <FILE>]
agent-test generate --url <URL> --user <USERNAME> --password <PASSWORD> [--cases <DIR>]
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
   > "Please provide the target URL. Example: `agent-test run --url https://example.com --user admin --password xxx`"
2. **Check auth**: If neither `--password` nor `--cookie` provided, prompt:
   > "Please provide authentication. Either `--user <name> --password <pass>` or `--cookie <value>`"
3. **Check cases dir**: If `--cases` not provided, use default `test/agent-tests/cases/`. Verify the directory exists.
4. **Check `--excel`**: If provided, verify the file exists and ends with `.xlsx`. Run conversion before proceeding.
5. **For generate mode**: `--url` is the page to generate cases for (not just the base URL).

**NEVER read passwords from files. NEVER store passwords in config or skill files.**

### Execution Scope (Run Mode)

The run mode supports two execution scopes. Select scope explicitly before running:

1. **`full` scope (strict regression)**
   - Execute every case step-by-step as required by Rule 4 (Never Skip Cases).
   - Use this when the user asks for full regression, complete run, or per-case coverage.

2. **`smoke` scope (fast/token-saving)**
   - Validate all module/page routes and key representative interactions only.
   - Reuse known blocked-case list and mark those as BLOCKED with reasons.
   - Use this only when the user explicitly asks for quick/smoke/sanity mode.

If scope is not specified by the user, ask once: `Run full (strict) or smoke (fast)?`

**Important**: If you choose smoke scope, the report must state that it is a smoke run and must not claim that every case step was executed.


### Permission Pre-Acquisition (CRITICAL)

Before starting any test execution, **verify all required permissions are pre-allowed** so the run never pauses for approval:

**Required capabilities:**
1. **All Playwright MCP tools**: `browser_navigate`, `browser_snapshot`, `browser_click`, `browser_run_code`, `browser_type`, `browser_evaluate`, `browser_take_screenshot`, etc.
2. **Shell commands**: `python3`, `mkdir`, `grep`, `ls`, `find`, `head`, `tail`, `wc`
3. **File read access**: project directory and temp directories
4. **File write access**: `test/agent-tests/**`

**Platform-specific permission setup:**
- **Claude Code**: Add permissions to `.claude/settings.local.json` (MCP tools + Bash commands)
- **Codex**: Ensure sandbox allows network access and file writes to `test/agent-tests/`
- **Cursor**: Grant terminal and file system access when prompted
- **Other agents**: Ensure the agent has unrestricted access to browser MCP tools, shell, and file system within the project

If any tool triggers a permission prompt during execution, **STOP and tell the user** to configure permissions before continuing. The test run must execute end-to-end without any interactive permission prompts.


### Known Blocked Case Set (Reusable)

Use this fixed blocked list unless environment prerequisites are newly satisfied:

- `01-my-gateway/09-create-gateway-programmable-gateway.md`
- `01-my-gateway/16-create-programmable-gateway-private.md`
- `01-my-gateway/17-programmable-gateway-basic-info-view.md`
- `01-my-gateway/18-programmable-gateway-env-overview-publish-resource.md`
- `01-my-gateway/19-programmable-gateway-env-overview-unpublish-resource.md`
- `01-my-gateway/35-disable.md`
- `01-my-gateway/39-case-4.md`
- `01-my-gateway/40-case-5.md`

Mark them as BLOCKED with explicit reasons in the report and continue.


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

### Rule 4: Never Skip Cases (Full Scope)

- **Every single test case MUST be executed** in full scope. You are not allowed to skip cases, batch them as "page-load only", or mark them as "skipped" to save time.
- For each case, you MUST: read its steps, translate them into Playwright actions, execute them in the browser, and verify the expected outcomes.
- **If a case cannot be executed** (e.g., missing prerequisite data, UI element not found, page error, unclear steps), you MUST:
  1. Mark it as **BLOCKED** (not SKIPPED) in the report
  2. Include the **specific reason** why it cannot run (e.g., "Button '发布' not found on page", "Requires pre-existing published version which does not exist")
  3. **Tell the user immediately** during execution — do not silently skip and only mention it in the final report
- **If execution is taking too long**, tell the user the progress (e.g., "Completed 200/835 cases, currently on module 12") and ask whether to continue — do NOT decide on your own to skip remaining cases.
- **"Too many cases" is not a valid reason to skip** in full scope. The skill is designed for large-scale execution. Batch aggressively, but execute every case.
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

**NEVER use `browser_snapshot` in ANY mode.** Use `browser_run_code` for everything.

- In **run mode**: Use `browser_run_code` with batched cases (as described above).
- In **generate mode**: Use `H.extractPageElements(page)` inside `browser_run_code` instead of `browser_snapshot`. This returns a compact summary (~500-1000 tokens) instead of the full accessibility tree (~20,000-90,000 tokens).

**Use the selector cache** (`test/agent-tests/selector-cache.json`) instead of reading Vue source files at runtime. Read the JSON once at the start of a run to get all selectors, URL mappings, and component patterns. Only fall back to Vue source analysis if a selector is missing from the cache.

**Use the helpers library** (`test/agent-tests/helpers.js`). Read this file once and inject its content (the `const H = { ... };` block) at the top of every `browser_run_code` call. This reduces generated code size and LLM reasoning overhead. Available helpers:
- `H.dropdown(page, selector, optionText)` — open select + pick option
- `H.dropdownNth(page, nthIndex, optionText)` — select by nth placeholder index
- `H.fillAndBlur(page, selector, value)` — fill input + blur for validation
- `H.triggerEmptyValidation(page, selector)` — fill-clear-blur for empty validation
- `H.closeSlider(page)` — close sideslider with confirmation handling
- `H.getFormError(page)` — get first visible form error text
- `H.checkToast(page, expectedText)` — check toast message
- `H.tableRowCount(page)` — count visible table rows
- `H.isVisible(page, selector)` — safe visibility check
- `H.getText(page, selector)` — safe text extraction
- `H.reAuth(page, baseUrl, username, password)` — re-authenticate after session expiry
- `H.failScreenshot(page, caseName, reportDir)` — take failure screenshot
- `H.addPlugin(page, pluginName)` — 2-step plugin wizard
- `H.extractPageElements(page)` — compact page element extraction (generate mode)

### Dropdown Interaction Pattern

**NEVER use `Escape` to close BkSelect dropdowns** — BkSelect ignores Escape, causing a toggle bug where the next click closes instead of opens. Use `body.click()` instead:

```javascript
// Dismiss any open dropdown by clicking outside
await page.locator('body').click({ position: { x: 10, y: 10 } });
await page.waitForTimeout(200);
// Now open the target dropdown (guaranteed fresh open)
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

## Run Mode: `agent-test run`

### Step 1: Load Selector Cache and Parse Cases

Before touching the browser, load resources and understand what you'll be testing:

1. **Read the selector cache**: `test/agent-tests/selector-cache.json` — contains all selectors, URL mappings, component patterns
2. **Read the helpers library**: `test/agent-tests/helpers.js` — will be injected into `browser_run_code` calls
3. Read all test case files from the cases directory
4. Extract the **Page** field from each case (e.g., `/`, `/gateways/123/resources`)
5. **Group cases by Page** — this determines your batching
6. Map each page to its selectors using `selector-cache.json` (key: page name, value: selectors object)
7. Use `urlRouteMap` from the cache to translate test case page patterns to actual Vue routes

### Step 1.5: Build Runtime Context (MANDATORY)

Before any browser action, build and keep this runtime context in memory:

1. `CACHE`: parsed JSON from `test/agent-tests/selector-cache.json`
2. `HELPERS_SRC`: raw `const H = { ... }` block from `test/agent-tests/helpers.js`
3. `CASE_INDEX`: parsed case metadata grouped by `Page`
4. `ROUTE_MAP`: `CACHE.urlRouteMap`

Mandatory usage rules:
- If a selector exists in `CACHE`, use it first. Do not re-discover it via ad-hoc DOM probing.
- Inject `HELPERS_SRC` into every `browser_run_code` batch. Do not re-implement helper logic inline unless missing.
- Resolve each case page path via `ROUTE_MAP` before navigation.
- Only fall back to dynamic DOM discovery when cache is missing or proven stale.
- If a fallback selector is found, update `selector-cache.json` after the batch completes.

**Only read Vue source files if a needed selector is missing from the cache.** In most cases, the cache plus `test/agent-tests/AGENTS.md` have everything you need.

### Run Mode Quality Gate (Before Step 2)

Do not proceed to authentication unless all checks pass:

1. `CACHE` loaded and contains `urlRouteMap`
2. `HELPERS_SRC` loaded and includes `H.dropdown`, `H.reAuth`, `H.failScreenshot`
3. All cases parsed and grouped by page
4. Execution scope (`full` or `smoke`) is explicit

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
  await page.waitForTimeout(1000);
  const testName = 'testagent' + Date.now().toString().slice(-6);
  const ni = page.locator('input[placeholder*="小写字母"]').first();
  await ni.fill(testName);
  await page.waitForTimeout(300);
  await page.locator('button').filter({ hasText: '提交' }).click();
  await page.waitForTimeout(3000);
  // Gateway created — stays on home page. Search for it to get ID.
  const si = page.locator('input[placeholder="请输入网关名称"]');
  await si.fill(testName);
  await page.keyboard.press('Enter');
  await page.waitForTimeout(1500);
  await page.locator('.table-item .name').first().click();
  await page.waitForTimeout(2000);
  const match = page.url().match(/\/(\d+)\//);
  return { testGatewayName: testName, testGatewayId: match ? match[1] : null };
}
```

**CRITICAL: After creating test gateway, configure backend service address:**
```javascript
// Navigate to /:testGwId/backend → edit "default" → fill httpbin.org:80 → confirm
// WITHOUT this, resource creation fails with "后端服务地址不允许为空"
```


**Backend dialog action text gotcha**:
- On current UI, backend edit dialog uses confirm button text `确定` (not `保存`).
- Implement fallback click order: first try `确定`, then `保存`.


**After creating the test gateway and configuring backend service, create a test resource, then generate a resource version and publish it to prod stage:**

**Create a test resource** (required before version generation):
```javascript
// Navigate to /:testGwId/resource/create → fill name, request path, select "default" service, fill backend path → 提交
// See "Resource Config Page" section in AGENTS.md for detailed selectors and gotchas
```

**Generate resource version:**
```javascript
async (page) => {
  // Navigate to resource settings
  await page.goto('{{URL}}/{{TEST_GW_ID}}/resource/setting');
  await page.waitForTimeout(2000);
  // Click "生成版本" button
  const genBtn = page.locator('button').filter({ hasText: '生成版本' }).first();
  await genBtn.click({ force: true });
  await page.waitForTimeout(1500);
  // Step 1: diff confirmation → click 下一步
  await page.locator('button').filter({ hasText: '下一步' }).first().click({ force: true });
  await page.waitForTimeout(1500);
  // Step 2: version info — version is auto-suggested → click 确定
  await page.locator('.bk-sideslider button').filter({ hasText: '确定' }).first().click({ force: true });
  await page.waitForTimeout(3000);
  // Wait for success: "版本生成成功"
  const success = await page.locator('text=版本生成成功').isVisible({ timeout: 10000 }).catch(() => false);
  if (!success) return { error: 'Version creation failed' };
  // Click "立即发布" to chain into publish flow
  await page.locator('button').filter({ hasText: '立即发布' }).click({ force: true });
  await page.waitForTimeout(2000);
  return { versionCreated: true };
}
```

**Publish to prod stage:**
```javascript
async (page) => {
  // The publish sideslider should already be open from "立即发布"
  // Select "prod" stage
  const stageSelect = page.locator('.release-sideslider .bk-select').first();
  await stageSelect.click({ force: true });
  await page.waitForTimeout(300);
  await page.locator('.bk-select-option').filter({ hasText: 'prod' }).click();
  await page.waitForTimeout(1000);
  // The version should be pre-selected; click 下一步
  await page.locator('.release-sideslider button').filter({ hasText: '下一步' }).first().click({ force: true });
  await page.waitForTimeout(1500);
  // Click 确认发布
  await page.locator('.release-sideslider button').filter({ hasText: '确认发布' }).first().click({ force: true });
  await page.waitForTimeout(500);
  // Confirm in InfoBox dialog
  const confirmBtn = page.locator('.bk-infobox button').filter({ hasText: '确认发布' }).first();
  if (await confirmBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
    await confirmBtn.click({ force: true });
  }
  await page.waitForTimeout(5000);
  // Wait for release event log to show success
  return { published: true };
}
```

**Version + publish gotchas:**
- The "生成版本" button is disabled when no resources have changed since the last version — you MUST create/edit a resource first.
- Version number is auto-suggested (Semver). Versions starting with `v` are rejected.
- After creating a version, a loading spinner ("版本正在生成中...") appears before the success page.
- If the publish sideslider doesn't open from "立即发布", navigate to `/:testGwId/resource/version` and click "发布" on the version row.


Use the test gateway ID for ALL mutating test cases. Use `bk-apigateway-inner` (ID=6) for read-only cases.

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

**Batch template (with helpers):**

```javascript
async (page) => {
  // --- Inject helpers (read from test/agent-tests/helpers.js) ---
  const H = { /* ...helpers content injected here... */ };

  const results = {};

  // Navigate once
  await H.navigateTo(page, '{{URL}}', PAGE_PATH);

  // --- Case: [case-name-1] ---
  try {
    // Steps using helpers — much shorter code
    await H.dropdown(page, '.my-select', 'Option A');
    const count = await H.tableRowCount(page);
    const pass = count > 0;

    if (!pass) {
      await H.failScreenshot(page, 'case-name-1', REPORT_DIR);
    }
    results['case-name-1'] = { pass, details: { count }, steps: '3/3' };
  } catch (e) {
    await H.failScreenshot(page, 'case-name-1', REPORT_DIR).catch(() => {});
    results['case-name-1'] = { pass: false, error: e.message, steps: 'error' };
  }

  // --- Case: [case-name-2] ---
  try {
    // ...same pattern with H.* helpers...
  } catch (e) { /* ... */ }

  return results;
}
```

**Important batching rules:**
- Each case in the batch is wrapped in its own `try/catch` — one failure does NOT skip remaining cases
- Reset UI state between cases (clear inputs, reset dropdowns to defaults)
- Use `force: true` on clicks to avoid overlay interception issues
- Never use `Escape` for BkSelect. Use `body.click()` outside to close dropdowns.
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
| Blocked  | [N]   |
| Errors   | [N]   |

## Results

### [icon] [case-filename] — [STATUS] ([duration])

Steps completed: [completed]/[total]
[If FAILED: **Failure at step N**: Expected ... but observed ...]
[If FAILED: Screenshot: [link to failure screenshot]]
[If BLOCKED: **Reason**: ...]

---
```

Status icons: ✅ PASSED, ❌ FAILED, 🚫 BLOCKED, ⚠️ ERROR

4. Output report path and summary to user.

### Step 6: Clean Up Test Gateway

After the report is written, delete the test gateway created in Step 2:

1. Navigate to the test gateway's basic info page (`{{URL}}/{{TEST_GW_ID}}/basic-info`)
2. Find and click `停用` (if visible), then click plain `删除`
3. Confirm deletion in the dialog
4. Verify the gateway no longer appears on the home page
5. If cleanup fails, note it in the report under a "Cleanup" section


Cleanup implementation notes:
- Basic info route is `/:id/basic-info` (not `/:id/basic/info`).
- Click `停用` first (if visible), confirm, wait for reload.
- Delete button text is plain `删除`.
- Confirm dialog may require typing gateway name.
- Always verify deletion by searching home page for the test gateway name.

**NEVER skip cleanup** — leftover test gateways pollute the environment.

### Error Handling

- **Site unreachable**: Report error, do not attempt cases
- **Auth failure**: Report, suggest cookie mode fallback
- **Element not found**: Record error with selector attempted, screenshot inside batch + mark failed + continue to next case in batch
- **Timeout**: 10 second max wait per element. If exceeded, mark error, continue to next case.
- **Session expired**: If page redirects to login mid-batch, re-authenticate via `browser_run_code` using original args, retry the batch. If re-auth fails, mark remaining as errors.

---

## Generate Mode: `agent-test generate`

```
agent-test generate --url <PAGE_URL> --user <USERNAME> --password <PASSWORD> [--cases <DIR>]
```

`--url` is the specific page to explore (e.g., `https://example.com/gateways/123/resources`).

### Step 1: Map URL to Vue Component (Cache First)

1. Read `test/agent-tests/selector-cache.json` and check the `urlRouteMap` for the given URL path
2. If the page exists in the cache, use its selectors directly
3. Only if the page is NOT in the cache, fall back to reading the Vue router:
   - Read `src/dashboard-front/src/router/index.ts` to map URL paths to component files
   - Read the matched Vue component file
4. Read `test/agent-tests/helpers.js` for use in Step 3

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

### Step 3: Explore Page in Browser (NO Snapshot)

1. Authenticate using `--user`/`--password` or `--cookie` args (same as run mode)
2. Navigate to `{{URL}}`
3. Use ONE `browser_run_code` call with `H.extractPageElements(page)` to get a compact element summary:

```javascript
async (page) => {
  // --- Inject helpers ---
  const H = { /* ...helpers content... */ };

  await page.goto('{{URL}}');
  await page.waitForTimeout(2000);

  const elements = await H.extractPageElements(page);
  return {
    url: page.url(),
    title: await page.title(),
    elements,
    counts: {
      buttons: elements.buttons.length,
      inputs: elements.inputs.length,
      selects: elements.selects.length,
      links: elements.links.length,
      tables: elements.tables.length,
      tabs: elements.tabs.length,
    }
  };
}
```

**This returns ~500-1000 tokens** instead of 20,000-90,000 tokens from `browser_snapshot`.

**DO NOT use `browser_snapshot` here.** The `extractPageElements` helper provides all the information needed to generate test cases: element types, text content, placeholders, classes, roles, and IDs — without the massive accessibility tree overhead.

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

## Maintaining selector-cache.json and helpers.js

These files are living artifacts — keep them updated as you discover new knowledge during test runs.

### When to Update `selector-cache.json`

| Trigger | What to Do |
|---------|------------|
| **Generate mode discovers a new page** | Add the page's selectors and URL to the cache after generating cases |
| **A selector fails during run mode** | Fix the selector in the cache after finding the correct one (via Vue source or `H.extractPageElements`) |
| **A new module/page is added to test cases** | Add its selectors to the cache. Read Vue source if needed, then cache the result |
| **URL routes change** (router refactor) | Update `urlRouteMap` entries |
| **BkUI component patterns change** | Update the `bkuiComponents` section |
| **New plugins are added to the platform** | Add them to `pluginManagement.availablePlugins` |

**How to update**: After fixing a selector or discovering a new one during execution, edit `test/agent-tests/selector-cache.json` before proceeding. Always update `_meta.lastUpdated` to today's date.

### When to Update `helpers.js`

| Trigger | What to Do |
|---------|------------|
| **A repeated interaction pattern appears 3+ times** across different batches | Extract it into a new `H.*` helper |
| **An existing helper doesn't handle an edge case** (e.g., dropdown with search input, nested dialog) | Fix or extend the helper |
| **A new BkUI component type is encountered** (e.g., `BkDatePicker`, `BkTree`) | Add a helper for its interaction pattern |
| **The login flow changes** | Update `H.reAuth()` |
| **Generate mode needs richer extraction** (e.g., new element types to detect) | Update `H.extractPageElements()` |

**How to update**: Edit `test/agent-tests/helpers.js` directly. Keep helpers stateless (no side effects beyond the page interaction). Test the change in the next `browser_run_code` call before relying on it for a full batch.

### When NOT to Update

- **Don't update during a batch run** — finish the current batch, record the issue, then update before the next batch.
- **Don't add one-off selectors** — if a selector is used by exactly one case on one page, inline it in the `browser_run_code` call instead of adding it to the cache.
- **Don't duplicate AGENTS.md knowledge** — the cache is for machine-readable selectors; AGENTS.md is for human-readable gotchas and context. Keep them complementary, not redundant.

---

## Key Files Reference

- **Selector cache**: `test/agent-tests/selector-cache.json` — pre-built selectors, URL maps, component patterns (READ FIRST)
- **Helpers library**: `test/agent-tests/helpers.js` — reusable browser interaction patterns (INJECT INTO browser_run_code)
- **Knowledge base**: `test/agent-tests/AGENTS.md` — gotchas, known issues, execution order
- **Cases directory**: `test/agent-tests/cases/`
- **Reports directory**: `test/agent-tests/reports/`
- **Vue router**: `src/dashboard-front/src/router/index.ts` (fallback only — prefer selector cache)
- **Vue views**: `src/dashboard-front/src/views/` (fallback only — prefer selector cache)
- **Test case format contract**: `specs/001-agent-test-suite/contracts/test-case-format.md`
- **Report format contract**: `specs/001-agent-test-suite/contracts/test-report-format.md`
