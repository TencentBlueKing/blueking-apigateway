# AGENTS.md

## Skills

Agent skills are located in `.agents/skills/`. Before executing any agent task described below, **read the full skill file first** to get detailed instructions, templates, and patterns.

| Skill | File | Description |
|-------|------|-------------|
| agent-test | `.agents/skills/agent-test/SKILL.md` | Browser-based regression test runner for the BlueKing API Gateway dashboard |

---

## Agent Test Suite (`/agent-test`)

> **Skill file**: `.agents/skills/agent-test/SKILL.md` — **read this file before executing any test commands.**

Browser-based regression test runner for the BlueKing API Gateway dashboard. Executes structured markdown test cases against a live environment using Playwright MCP browser tools.

### Quick Start

```bash
# Run all test cases
/agent-test run --url https://your-apigw.example.com/ --user admin --password 'yourpass'

# Run with cookie auth
/agent-test run --url https://your-apigw.example.com/ --cookie 'bk_token=abc123'

# Run from Excel file (converts to markdown cases first, then runs)
/agent-test run --url https://your-apigw.example.com/ --user admin --password 'yourpass' --excel path/to/test-cases.xlsx

# Run specific cases directory
/agent-test run --url https://your-apigw.example.com/ --user admin --password 'yourpass' --cases test/agent-tests/cases/smoke/

# Generate test cases for a page
/agent-test generate --url https://your-apigw.example.com/gateways/123/resources --user admin --password 'yourpass'
```

### Arguments

| Flag | Required | Description |
|------|----------|-------------|
| `--url` | **Yes** | Target dashboard URL |
| `--user` | Yes* | Login username |
| `--password` | Yes* | Login password (never stored, always passed as arg) |
| `--cookie` | Yes* | Session cookie (alternative to user/password) |
| `--cases` | No | Cases directory (default: `test/agent-tests/cases/`) |
| `--excel` | No | Excel file (.xlsx) to convert to cases before running |

\* Either `--user` + `--password` OR `--cookie` is required.

### Subcommands

#### `run` — Execute test cases

Reads markdown test case files from the cases directory and executes them against the target URL.

**What it does:**
1. Reads and groups test cases by page
2. Pre-analyzes Vue source code for selectors
3. Authenticates via browser
4. Executes all cases for each page in batched `browser_run_code` calls (one call per page group)
5. Takes screenshots only on failure
6. Writes a report to `test/agent-tests/reports/YYYY-MM-DDTHH-MM-SS/report.md`

**Performance:** Uses aggressive batching — all cases sharing the same page run in a single browser call. 4 cases complete in ~15 seconds.

#### `generate` — Create test cases from a page

Explores a live page and its Vue source code to generate test case markdown files.

**What it does:**
1. Maps the URL to its Vue component via the router
2. Analyzes the component template and script for interactive elements
3. Takes one browser snapshot of the live page
4. Cross-references source and live page to generate test cases
5. Writes case files to the cases directory

### Test Case Format

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

### File Structure

```
.agents/skills/agent-test/
└── SKILL.md               # Full skill instructions (read first!)

test/agent-tests/
├── AGENTS.md                   # ⭐ Knowledge base — URL mappings, selectors, gotchas (READ THIS)
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

> **Important**: Before running test cases, read `test/agent-tests/AGENTS.md` for critical knowledge about URL route mappings, form selectors, and common gotchas discovered during previous test runs.

### Reports

Reports are written to `test/agent-tests/reports/` with a timestamped directory. Each report contains:

- Summary table (total/passed/failed/skipped/errors)
- Per-case results with step counts and timing
- Failure details with expected vs observed values
- Links to failure screenshots (only captured on failure)

### Security

- **Passwords are never stored** — not in config files, not in the skill file, not in test cases
- Always pass `--password` as an argument or use `--cookie`
- The `config.md` file contains only paths and login flow documentation

### Troubleshooting

| Problem | Solution |
|---------|----------|
| "账户或者密码错误" | Wrong password — check your `--password` arg |
| Browser won't launch | Kill stale Chrome: `pkill -f "mcp-chrome"` |
| Session expires mid-run | The skill auto-re-authenticates using your args |
| Dropdown click intercepted | The skill uses `force: true` + `Escape` pattern |
| Login form not found | Two forms exist (Chinese/English) — both are auto-detected |
