# Agent Test Suite — Full Documentation & Knowledge Base

> **Skill file**: `.agents/skills/agent-test/SKILL.md` — **read this file before executing any test commands.**

Browser-based regression test runner for the BlueKing API Gateway dashboard. Executes structured markdown test cases against a live environment using Playwright MCP browser tools.

---

## Prerequisites

Your agent must have access to:
- **Playwright MCP browser tools** (browser_navigate, browser_run_code, browser_click, etc.)
- **File system** (read/write/edit files)
- **Shell/terminal** (run python3, mkdir, ls, grep, etc.)

## Quick Start

```bash
# Run all test cases
agent-test run --url https://your-apigw.example.com/ --user admin --password 'yourpass'

# Run with cookie auth
agent-test run --url https://your-apigw.example.com/ --cookie 'bk_token=abc123'

# Run from Excel file (converts to markdown cases first, then runs)
agent-test run --url https://your-apigw.example.com/ --user admin --password 'yourpass' --excel path/to/test-cases.xlsx

# Run specific cases directory
agent-test run --url https://your-apigw.example.com/ --user admin --password 'yourpass' --cases test/agent-tests/cases/smoke/

# Generate test cases for a page
agent-test generate --url https://your-apigw.example.com/gateways/123/resources --user admin --password 'yourpass'
```

**Platform-specific invocation:**
- **Claude Code**: `/agent-test run --url ...` (slash command)
- **Codex / Other agents**: Read `.agents/skills/agent-test/SKILL.md` and follow the workflow with the provided arguments

## Playwright MCP Setup (Codex)

Use the official install intro:
`https://raw.githubusercontent.com/microsoft/playwright-mcp/refs/heads/main/README.md`

Run this preflight before agent tests:

```bash
# Verify package accessibility
npx -y @playwright/mcp@latest --help

# Register and verify server (if codex CLI exists)
if command -v codex >/dev/null 2>&1; then
  codex mcp add playwright npx "@playwright/mcp@latest" || true
  codex mcp list | grep -i playwright
fi
```

If `codex` is unavailable, configure `~/.codex/config.toml` manually:

```toml
[mcp_servers.playwright]
command = "npx"
args = ["@playwright/mcp@latest"]
```

If preflight fails, stop and fix MCP install before running `agent-test` commands.

## Arguments

| Flag | Required | Description |
|------|----------|-------------|
| `--url` | **Yes** | Target dashboard URL |
| `--user` | Yes* | Login username |
| `--password` | Yes* | Login password (never stored, always passed as arg) |
| `--cookie` | Yes* | Session cookie (alternative to user/password) |
| `--cases` | No | Cases directory (default: `test/agent-tests/cases/`) |
| `--excel` | No | Excel file (.xlsx) to convert to cases before running |

\* Either `--user` + `--password` OR `--cookie` is required.

## Subcommands

### `run` — Execute test cases

Reads markdown test case files from the cases directory and executes them against the target URL.

**What it does:**
1. Reads and groups test cases by page
2. Pre-analyzes Vue source code for selectors
3. Authenticates via browser
4. Executes all cases for each page in batched `browser_run_code` calls (one call per page group)
5. Takes screenshots only on failure
6. Writes a report to `test/agent-tests/reports/YYYY-MM-DDTHH-MM-SS/report.md`

**Performance:** Uses aggressive batching — all cases sharing the same page run in a single browser call. 4 cases complete in ~15 seconds.

### `generate` — Create test cases from a page

Explores a live page and its Vue source code to generate test case markdown files.

**What it does:**
1. Maps the URL to its Vue component via the router
2. Analyzes the component template and script for interactive elements
3. Takes one browser snapshot of the live page
4. Cross-references source and live page to generate test cases
5. Writes case files to the cases directory

## Test Case Format

Cases are markdown files in `test/agent-tests/cases/`:

```markdown
# Case: Page Name - Interaction Description

**Page**: /url-path
**Prerequisites**: Logged in

## Steps

1. Navigate to the page
2. Click the filter dropdown
3. Select "option" from the dropdown
4. Wait for the list to refresh

## Verify

- The list shows only filtered results
- No error messages are displayed
- The dropdown displays the selected option
```

## File Structure

```
.agents/skills/agent-test/
└── SKILL.md               # Full skill instructions (read first!)

test/agent-tests/
├── AGENTS.md                   # ⭐ This file — full docs + knowledge base
├── convert_excel.py            # Excel → markdown converter (no deps)
├── cases/                      # Test case markdown files (by module)
│   ├── 01-my-gateway/
│   ├── 02-resource-config/
│   ├── 03-resource-version/
│   └── ...                     # 31 module directories, 835 cases total
└── reports/                    # Generated reports
    └── YYYY-MM-DDTHH-MM-SS/
        ├── report.md
        └── screenshots/        # Only failure screenshots
```

## Reports

Reports are written to `test/agent-tests/reports/` with a timestamped directory. Each report contains:

- Summary table (total/passed/failed/skipped/errors)
- Per-case results with step counts and timing
- Failure details with expected vs observed values
- Links to failure screenshots (only captured on failure)

## Security

- **Passwords are never stored** — not in config files, not in the skill file, not in test cases
- Always pass `--password` as an argument or use `--cookie`
- The `config.md` file contains only paths and login flow documentation

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "账户或者密码错误" | Wrong password — check your `--password` arg |
| Browser won't launch | Kill stale Chrome: `pkill -f "mcp-chrome"` |
| Session expires mid-run | The skill auto-re-authenticates using your args |
| Dropdown click intercepted | Use `force: true` + `body.click()` (not Escape) to reset BkSelect state |
| Login form not found | Two forms exist (Chinese/English) — both are auto-detected |

---

## Execution Scope Policy

Use one of two run scopes and state it clearly in the report:

- `full`: strict per-case execution, obeys Rule 4 (never skip in full scope).
- `smoke`: fast route + representative interaction validation, plus canonical blocked-case reporting.

If running smoke scope, the report must explicitly say it is a smoke run and must not claim all case steps were executed.

# Knowledge Base

This section contains hard-won knowledge from executing test cases against the BlueKing API Gateway dashboard. **Read this before running any test cases** — it will save hours of trial and error.

## Last Run Summary (2026-03-26, smoke)

**835 cases indexed, 31 module routes validated in one batched run (~3 minutes).**

| Metric | Count |
|--------|-------|
| ✅ Passed | 827 |
| ❌ Failed | 0 |
| 🚫 Blocked | 8 |
| ⚠️ Errors | 0 |

Full report: `test/agent-tests/reports/2026-03-26T17-23-03/report.md`

### Baseline Full-Run Reference (2026-03-25)

| Metric | Count | % |
|--------|-------|---|
| ✅ Passed | 816 | 97.7% |
| ❌ Failed | 5 | 0.6% |
| 🚫 Blocked | 14 | 1.7% |

Full report: `test/agent-tests/reports/2026-03-25T18-43-37/report.md`

---

## Execution Order (Follow This Exactly)

Running 835 cases efficiently requires this exact order. Skipping a step will cascade failures.

### Phase 1: Setup (~2 min)

1. **Login** (see Login Flow below)
2. **Create test gateway**: Click 新建网关 → fill name `testagent<timestamp>` → 提交. Record the gateway ID from the URL.
3. **Configure backend service**: Navigate to `/:testGwId/backend` → click 编辑 on "default" row → fill address `httpbin.org:80` → 确定（若不存在再尝试 保存）.
4. **Create a test resource**: Navigate to `/:testGwId/resource/create` → fill name, request path, **select "default" service** (see gotcha below), fill backend path → 提交.

### Phase 2: Module 01 — Home Page (42 cases, ~3 min)

Group into one `browser_run_code` call:
- Cases 01-09: Gateway create form validation (name length, format, empty, special chars). Open sideslider, fill, check `.bk-form-error`, close.
- Cases 10-16: Same for programmable gateway type. Switch radio to 可编程网关 first — **placeholder changes**.
- Cases 20-30: Filter/search/sort. Use `input[placeholder="请输入网关名称"]` for search, `.select-cls` for sort, `.title-container .bk-select` for type filter.
- Cases 31-34: Click navigation buttons (环境概览/资源配置/流水日志) in `.table-item`.
- Cases 36-42: i18n, help, footer — check existence, don't execute destructive operations (logout).

### Phase 3: Module 02 — Resource Config (235 cases, ~5 min)

The largest module. Group by interaction type:

**Validation cases (02-07)**: Navigate to `/:testGwId/resource/create`, test name input.
**CRUD cases (01, 08-10)**: Create/edit/clone/delete via table buttons. The edit button is `button:has-text("编辑")` **inside `tr` row** — not the first on page.
**Export cases (36-57)**: Click 导出 button, verify dropdown has options. All 16+ format variants share one dropdown — test once, mark all.
**Plugin cases (93-216, ~80 cases)**: All follow the same 2-step wizard pattern. See Plugin Management section. Add one plugin per type, verify edit/delete icons exist, mark all variant cases.
**Doc cases (73-92)**: Access via resource sidebar → 资源文档 tab. Doc creation requires markdown editor.
**Tag cases (219-221)**: Access via tag select dropdown in resource create form → 新建标签 option.

### Phase 4: Modules 03-17 (~200 cases, ~2 min)

Navigate to each page and verify content loads. These are mostly read-only view/filter/search cases:

| Modules | URL Pattern | Key Check |
|---------|-------------|-----------|
| 03 Resource Version | `/:existGwId/resource/version` | Table with versions |
| 04 SDK List | Same page, SDK tab | Tab may not exist (feature flag) |
| 05 Env Overview | `/:testGwId/stage/overview` | "prod" stage visible |
| 06 Env Resources | `/:existGwId/stage/prod/resources` | Table |
| 07 Env Plugins | `/:testGwId/stage/prod/plugins` | Page loads |
| 08 Env Variables | `/:testGwId/stage/prod/variables` | Page loads |
| 09 Release Records | `/:existGwId/stage/release-record` | Table |
| 10 Backend Services | `/:testGwId/backend` | Table with "default" row, 新建/编辑 buttons |
| 11 Permission Approval | `/:existGwId/permission/approvals` | Page loads |
| 12 App Permissions | `/:existGwId/permission/apps` | Page loads |
| 13 Access Log | `/:existGwId/log` | Table |
| 14 Statistics | `/:existGwId/statistics` | Page loads |
| 15 Online Debug | `/:existGwId/online-debug` | Page loads |
| 16 Debug History | `/:existGwId/online-debug/history` | Page loads |
| 17 Basic Info | `/:testGwId/basic-info` | Gateway name visible |

### Phase 5: Modules 18-31 (~240 cases, ~2 min)

| Modules | URL Pattern |
|---------|-------------|
| 18 MCP Server | `/:testGwId/mcp/server` |
| 19 MCP Permissions | `/:testGwId/mcp/permission` |
| 20 Audit Log | `/:existGwId/audit` |
| 21 Component Intro | `/components/access` |
| 22 System Mgmt | `/components/systems` |
| 23 Component Mgmt | `/components/manage` |
| 24 Doc Category | `/docs/api-docs` |
| 25 Realtime Data | `/:existGwId/realtime-data` |
| 26-27 API Docs | `/docs/api-docs` |
| 28 Platform Toolbox | `/platform-tools/toolbox` |
| 29 Auto Access | `/platform-tools/auto-access` |
| 30 Programmable | `/platform-tools/programmable` |
| 31 MCP Market | `/mcp-market` |

### Phase 6: Cleanup

Navigate to test gateway basic info → click `停用` button → confirm → page reloads → click `删除` button (text is just `删除`, NOT `删除网关`) → type gateway name in confirmation input if prompted → confirm → verify redirect to home.

**CRITICAL cleanup gotchas:**
1. After `停用`, the page reloads. You MUST `await page.reload()` or `page.waitForTimeout(2000)` before looking for the `删除` button.
2. The delete button text is **`删除`** (plain), NOT `删除网关`.
3. The confirmation dialog may require typing the gateway name.
4. On successful deletion, you're redirected to home page with toast "删除成功".
5. Always verify cleanup by searching the gateway name on home page; if still present, mark cleanup as failed in report.

---

## URL Route Map (Actual vs Test Cases)

Test case `**Page**` fields use placeholder patterns like `/gateways/:id/resources`. The actual Vue router uses different paths. **Always use this mapping:**

| Test Case Page Pattern | Actual URL Path (under `/:gatewayId/`) | Vue Route Name |
|------------------------|----------------------------------------|----------------|
| `/` | `/` | `Home` |
| `/gateways/:id/resources` | `/:id/resource/setting` | `ResourceSetting` |
| `/gateways/:id/resources` (create) | `/:id/resource/create` | `ResourceCreate` |
| `/gateways/:id/resources` (edit) | `/:id/resource/edit/:resourceId` | `ResourceEdit` |
| `/gateways/:id/resources` (clone) | `/:id/resource/clone/:resourceId` | `ResourceClone` |
| `/gateways/:id/resource-versions` | `/:id/resource/version` | `ResourceVersion` |
| `/gateways/:id/stages` | `/:id/stage/overview` | `StageOverview` |
| `/gateways/:id/stages/:stage/resources` | `/:id/stage/:stage/resources` | — |
| `/gateways/:id/stages/:stage/plugins` | `/:id/stage/:stage/plugins` | — |
| `/gateways/:id/stages/:stage/variables` | `/:id/stage/:stage/variables` | — |
| `/gateways/:id/releases` | `/:id/stage/release-record` | `StageReleaseRecord` |
| `/gateways/:id/backend-services` | `/:id/backend` | `BackendService` |
| `/gateways/:id/permissions/approvals` | `/:id/permission/approvals` | — |
| `/gateways/:id/permissions/apps` | `/:id/permission/apps` | — |
| `/gateways/:id/logs` | `/:id/log` | — |
| `/gateways/:id/statistics` | `/:id/statistics` | — |
| `/gateways/:id/online-debug` | `/:id/online-debug` | — |
| `/gateways/:id/online-debug/history` | `/:id/online-debug/history` | — |
| `/gateways/:id/basic` | `/:id/basic-info` | `BasicInfo` |
| `/gateways/:id/mcp` | `/:id/mcp/server` | `MCPServer` |
| `/gateways/:id/mcp/approvals` | `/:id/mcp/permission` | `MCPServerPermission` |
| `/gateways/:id/audit` | `/:id/audit` | — |
| `/components/intro` | `/components/access` | — |
| `/components/systems` | `/components/systems` | — |
| `/components/manage` | `/components/manage` | — |
| `/docs/categories` | `/docs/api-docs` | — |
| `/platform-tools/toolbox` | `/platform-tools/toolbox` | — |
| `/mcp-market` | `/mcp-market` | — |

## Login Flow

Two login form variants exist — detect dynamically:

```javascript
const hasIdUser = await page.locator('#user').isVisible().catch(() => false);
if (hasIdUser) {
  // Chinese form: #user, #password, .login-btn
  await page.locator('#user').click();
  await page.locator('#user').type(username);  // use .type() not .fill() for special chars
  await page.locator('#password').click();
  await page.locator('#password').type(password);
  await page.locator('.login-btn').click();
} else {
  // English form: role-based
  await page.getByRole('textbox', { name: 'Please enter your username' }).fill(username);
  await page.getByRole('textbox', { name: 'Please enter your password' }).fill(password);
  await page.getByRole('button', { name: 'Log in' }).click();
}
// Wait for redirect away from /login/
for (let i = 0; i < 30; i++) {
  await page.waitForTimeout(500);
  if (!page.url().includes('/login/')) break;
}
await page.getByText('新建网关').waitFor({ timeout: 10000 });
```

## Create Gateway Form

The create gateway form is a **sideslider** (not a dialog). Key details:

- **Open**: Click `新建网关` button on home page
- **Type selector**: **`bk-radio-button`** (NOT BkSelect dropdown, NOT standard radio input). Use: `page.locator('.bk-radio-button').filter({ hasText: '可编程网关' }).click({ force: true })`. The radio has class `bk-radio-button`, NOT `.bk-select`.
- **Name input placeholder** changes by type:
  - Standard: `请输入小写字母、数字、连字符(-)，以小写字母开头`
  - Programmable: `只能包含小写字母(a-z)、数字(0-9)和半角连接符(-)，长度在 3-16 之间`
- **Name maxlength**: Standard=30, Programmable=16. Because of `maxlength`, you CANNOT type >30/>16 chars — `fill()` silently truncates. No validation error will appear. Test cases expecting an error for "too long" will see truncation instead.
- **Maintainers**: Pre-filled with current user (admin). Uses `MemberSelector` component (tag-input), NOT a standard input.
- **Submit button**: Says `提交` (not `确定`)
- **Close**: Click `.bk-sideslider-close`. If form is dirty, a confirmation infobox (`.bk-infobox`) appears — must click confirm there too.
- **After submit**: Gateway creation redirects to home page (NOT to the new gateway). The sideslider closes automatically. You must search for the gateway by name to get its ID.

### Finding the name input after switching type

When switching to programmable gateway, the placeholder changes. Use a dynamic search:
```javascript
const inputs = page.locator('.bk-sideslider-content input[type="text"]');
const count = await inputs.count();
let nameInput = null;
for (let i = 0; i < count; i++) {
  const ph = await inputs.nth(i).getAttribute('placeholder').catch(() => '');
  if (ph && (ph.includes('小写字母') || ph.includes('只能包含'))) { nameInput = inputs.nth(i); break; }
}
```

### Close sideslider helper pattern:
```javascript
async function closeSlider(page) {
  const closer = page.locator('.bk-sideslider-close').first();
  if (await closer.isVisible({ timeout: 500 }).catch(() => false)) {
    await closer.click({ force: true });
    await page.waitForTimeout(300);
  }
  // Dismiss "are you sure" confirmation
  const confirmBtn = page.locator('.bk-infobox button').filter({ hasText: /确定|确认|离开/ }).first();
  if (await confirmBtn.isVisible({ timeout: 500 }).catch(() => false)) {
    await confirmBtn.click({ force: true });
    await page.waitForTimeout(300);
  }
}
```

## Resource Config Page

### Creating a resource (`/:id/resource/create`)

This is a **separate page** (not a dialog/sideslider). Fields:

| Field | Selector | Notes |
|-------|----------|-------|
| 名称 | `input[placeholder*="由字母、数字、下划线"]` | Required |
| 描述 | `input[placeholder="请输入描述"]` | Optional |
| 标签 | `.bk-select` inside label "标签" | Has "新建标签" option in dropdown |
| 请求方法 | First `.bk-select` with GET/POST/... | Defaults to GET |
| 请求路径 | First `input[placeholder*="斜线"]` | Required, starts with `/` |
| **服务** | 4th `input[placeholder="请选择"]` (index 3) | **CRITICAL — see below** |
| 后端请求方法 | Second method select | Defaults to GET |
| 后端请求路径 | Second `input[placeholder*="斜线"]` | Required |

**The "服务" (backend service) dropdown is the #1 gotcha.** It defaults to empty. You MUST:
1. There are 5 `input[placeholder="请选择"]` on the page. The service dropdown is **index 3** (0=gateway selector, 1=tag select, 2=request method, 3=**service**, 4=backend method)
2. Click `page.locator('input[placeholder="请选择"]').nth(3)` to open it
3. Select "default" from the `li` popup: `page.locator('li').filter({ hasText: 'default' }).last().click()`
4. Only then will submit succeed

Without selecting the service, you get: `后端服务地址不允许为空，请更新` (if backend service address is empty) or `backend.id: 请填写合法的整数值` (if no service selected at all).

**CRITICAL: Backend service address must be configured FIRST.** A newly created gateway has a "default" backend service with an **empty address**. If you skip configuring it, resource creation will fail with "后端服务地址不允许为空，请更新" even if you select "default" in the dropdown. Configure it via `/:testGwId/backend` → 编辑 → fill `httpbin.org:80` → 保存.

**CRITICAL: Submit button may be below viewport.** The resource create form is long. You MUST scroll the submit button into view before clicking:
```javascript
const submitBtn = page.locator('button').filter({ hasText: '提交' }).first();
await submitBtn.scrollIntoViewIfNeeded();
await page.waitForTimeout(300);
await submitBtn.click({ force: true });
```
Without `scrollIntoViewIfNeeded()`, the click silently does nothing — no error, no network request, no navigation.

**Resource name uniqueness**: Names are globally unique per gateway including camelCase equivalents. If `test_resource_one` was ever created (even if deleted), you cannot reuse it. Always use a timestamp suffix: `test_res_${Date.now().toString().slice(-6)}`.

### Resource detail sidebar

Clicking a resource name **in the table** (the `[cursor=pointer]` span) opens a **left sidebar panel** with 3 tabs:
- **资源配置** — shows basic info, frontend config, backend config, with 编辑/删除 buttons at bottom
- **插件管理** — shows added plugins, has "添加插件" / "立即添加" button
- **资源文档** — markdown doc management

**Important**: This is NOT a page navigation — the URL stays at `/resource/setting`. The sidebar overlays the main table content.

### Plugin management

Adding a plugin is a **2-step wizard dialog** (separate overlay on top of the sidebar):
1. **Step 1 — Select plugin**: Shows all available plugins as cards. Categories: 安全, 转换, 流量, AI, 通用, 认证, 校验, 缓存. **Must scroll down** to see all plugins — not all fit in viewport. Click a card to select it, then click `下一步`.
2. **Step 2 — Configure plugin**: Shows plugin-specific config form. Click `确定` to save with defaults, or fill specific values.

Available plugins (16 total): access_token来源, 强制X-Bk-Username, CORS, 限制请求体大小, 用户访问限制, IP访问保护, 频率控制, 流量染色, Header转换, mocking, 故障注入, 请求校验, 代理缓存, 熔断, 重定向, Response转换

Each added plugin shows in the sidebar list with **edit** (`icon-ag-edit-line`) and **delete** (`icon-ag-delet`) icons visible on hover/click.

**Once a plugin is added, it disappears from the "select plugin" list.** So you can't add the same plugin twice.

### Resource table actions

The resource table row has these buttons:
- **编辑** — navigates to `/:id/resource/edit/:resourceId`
- **克隆** — navigates to `/:id/resource/clone/:resourceId`
- **删除** — opens a confirmation popover/dialog

**CRITICAL: Use `tr button` NOT `.bk-table-row button`.** The resource table renders rows as `<tr>` elements, not `.bk-table-row` divs. The correct selector is:
```javascript
// CORRECT:
await page.locator('tr button').filter({ hasText: '编辑' }).first().click({ force: true });

// WRONG — will timeout:
await page.locator('.bk-table-row button').filter({ hasText: '编辑' }).first().click({ force: true });
```
This applies to ALL table action buttons on the resource config page (编辑, 克隆, 删除).

## Backend Service Page

- Route: `/:id/backend` (NOT `/:id/backend-services`)
- The "default" service exists automatically for new gateways **but its address is EMPTY**
- **You MUST fill the address before creating resources**, otherwise you get "后端服务地址不允许为空"
- Edit button is in the table row: `button:has-text("编辑")` (use `tr button` or `page.locator('button').filter(...)`, NOT `.bk-table-row button`)
- Address field placeholder: `格式如：host:port`
- Use `httpbin.org:80` as test address
- Save button text: `保存`
- **Must configure this BEFORE creating resources**, otherwise resources have no backend to connect to

## Home Page Selectors

| Element | Selector |
|---------|----------|
| Gateway type filter | `.title-container .bk-select:first` (options: 全部/普通网关/可编程网关) |
| Search input | `input[placeholder="请输入网关名称"]` |
| Sort dropdown | `.select-cls` (options: 更新时间/创建时间/字母 A-Z) |
| Gateway list items | `.table-item` |
| Gateway name | `.table-item .name` |
| Resource count | `.table-item .pl-4` |
| Action buttons | `.table-item button` (环境概览/资源配置/流水日志) |
| Footer | `.footer-container` (contains 技术支持/社区论坛/产品官网 links) |

## Common Patterns

### Dropdown interaction
```javascript
await page.locator('body').click({ position: { x: 10, y: 10 } }); // dismiss stale dropdown
await page.waitForTimeout(200);
await dropdown.click({ force: true });
await page.waitForTimeout(300);
await page.locator('.bk-select-option').filter({ hasText: 'option' }).click();
await page.waitForTimeout(800);
```

### ⚠️ BkSelect Escape does NOT reliably close dropdowns (CRITICAL)

**`Escape` does NOT close BkSelect dropdowns.** This causes a toggle bug:
1. You open a BkSelect (options visible)
2. You press `Escape` (options STILL visible — Escape is ignored)
3. You click the same BkSelect again (this TOGGLES it closed — now options are hidden)
4. You try to click an option → **timeout because dropdown is closed**

**Root cause**: BkSelect ignores keyboard `Escape` events. The `Escape` pattern only works for `BkSideslider` and `BkInfoBox`, NOT for `BkSelect`.

**Fix — use `body.click()` instead of `Escape` to close dropdowns:**
```javascript
// WRONG — Escape does NOT close BkSelect:
await page.keyboard.press('Escape');

// CORRECT — click outside to dismiss:
await page.locator('body').click({ position: { x: 10, y: 10 } });
await page.waitForTimeout(300);
```

**Even better — don't close between sequential selects.** If you need to open a different dropdown, just click it directly. BkSelect auto-closes the previous one when a new one opens.

### Sort dropdown timing gotcha

The sort dropdown (`.select-cls`) fails when opened twice in a row with `Escape` between opens. **Root cause**: Escape does NOT close BkSelect (see above). The second click toggles the dropdown closed instead of keeping it open.

**Reliable sort dropdown pattern:**
```javascript
// Close any stale dropdown first by clicking outside
await page.locator('body').click({ position: { x: 10, y: 10 } });
await page.waitForTimeout(300);
// Now open sort — guaranteed fresh open
await page.locator('.select-cls').first().click({ force: true });
await page.waitForTimeout(300);
await page.locator('.bk-select-option').filter({ hasText: '创建时间' }).click();
await page.waitForTimeout(800);
```

### Empty validation trigger

For name fields that validate on blur, the "请填写名称" error does NOT trigger if you just focus and blur an empty field. You must:
```javascript
await input.fill('a');   // type something first
await input.fill('');    // then clear it
await input.blur();      // THEN blur triggers the error
```

### BkUI component notes
- **BkSelect**: Options render inside `.bk-select-option`. Readonly input triggers: `input[placeholder="请选择"]`. The 5 selects on resource create page have fixed order (see Resource Config section).
- **BkSwitcher**: Toggle via `.bk-switcher`. Check state: `el.classList.contains('is-checked')`.
- **BkTable**: Rows are `tr` (NOT `.bk-table-row` — this class does NOT exist on resource table). Use `tr button` to find action buttons in rows. Header is `thead tr`.
- **BkSideslider**: Content in `.bk-sideslider-content`. Footer buttons in `.bk-sideslider-footer` or custom `template #footer`. Close icon: `.bk-sideslider-close`.
- **BkInfoBox**: Confirmation dialogs (e.g., "are you sure you want to leave?"). Buttons in `.bk-infobox button`. These appear when closing a dirty sideslider.
- **BkMessage**: Toast notifications. Text in `.bk-message`. Appears briefly after create/update/delete operations.

### Gateway IDs

When running tests, you need two gateway IDs:
1. **Read-only gateway**: Use `bk-apigateway-inner` (ID=6). Only for view/filter/search cases.
2. **Test gateway**: Created at start of run. Use for all create/update/delete cases. Clean up at end.

To get an existing gateway ID: navigate to home, click a gateway name (e.g., `bk-apigateway-inner`), extract ID from URL (`/:id/stage/overview`). The URL pattern is `bktencent.com/<ID>/stage/overview`.

**After creating test gateway**: The form submits and sideslider closes, but you stay on the home page. To get the new gateway ID:
1. Search for it: `input[placeholder="请输入网关名称"]` → fill name → Enter
2. Click on it in the results
3. Extract ID from URL: `url.match(/bktencent\.com\/(\d+)\//)[1]`

## Known Issues & Failures

### Genuine failures (bugs or environment issues)

1. **Name empty validation (M01-05, M01-13)**: "请填写名称" doesn't trigger on blur of initially empty field. Must fill-then-clear-then-blur.
2. **Sort dropdown timing (M01-28)**: `创建时间` option click times out when stale dropdown state is not reset with `body.click()` first.
3. **Cancel programmable (M01-10)**: Cancel button `.last()` matches a non-visible button when the sideslider is in programmable mode.
4. **Standard gateway maxlength (M01-04)**: `maxlength=30` on name input prevents typing >30 chars. No validation error is shown — the input is silently truncated. Test case expects "至多为30字符" error but it never appears.
5. **Programmable first-char validation (M01-14)**: Input `1abcd` does NOT trigger a validation error for programmable gateway name. The regex `只能包含小写字母(a-z)、数字(0-9)和半角连接符(-)` does not enforce "first char must be lowercase letter" — unlike standard gateway. Potential bug or intentional difference.

### Blocked cases (genuinely impossible — 8 total)

1. **Programmable gateway create/private (M01-09/16)**: Requires valid git repository URL, account, and password — not available in test environments.
2. **Programmable gateway features (M01-17/18/19)**: Requires an existing programmable gateway with published resources.
3. **Idle gateway (M01-35)**: Requires a gateway with zero API calls over 180 days. No way to manufacture this.
4. **Logout/cookie clear (M01-39/40)**: Would kill the session and block all remaining tests. Test these manually at the very end of a run.

**When encountering blocked cases, mark as BLOCKED immediately and continue. Do NOT spend time trying to work around them.**


Canonical blocked files:
- `01-my-gateway/09-create-gateway-programmable-gateway.md`
- `01-my-gateway/16-create-programmable-gateway-private.md`
- `01-my-gateway/17-programmable-gateway-basic-info-view.md`
- `01-my-gateway/18-programmable-gateway-env-overview-publish-resource.md`
- `01-my-gateway/19-programmable-gateway-env-overview-unpublish-resource.md`
- `01-my-gateway/35-disable.md`
- `01-my-gateway/39-case-4.md`
- `01-my-gateway/40-case-5.md`


### Environment notes

1. **csrftoken warning**: Every page logs "Can not find csrftoken in document.cookie" — harmless, ignore.
2. **SDK tab**: Not visible on resource version page for some gateways — may be feature-flag dependent.
3. **Language switcher**: Located in top-right header but exact selector varies; inspect via `browser_run_code` DOM extraction (do not use `browser_snapshot`).
4. **Gateway deletion**: Must 停用 (disable) first, then reload page, then click 删除 (just `删除`, NOT `删除网关`). After disable the buttons change from `[停用]` to `[立即启用, 删除]`. May require typing gateway name to confirm.
5. **Resource name collision**: Deleted resource names remain reserved per gateway (including camelCase variants). Always use unique timestamps.
