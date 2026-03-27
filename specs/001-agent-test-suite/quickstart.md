# Quickstart: Agent Test Suite

**Branch**: `001-agent-test-suite`

## What This Feature Does

An AI-agent-driven browser test suite that replaces manual regression testing of the BlueKing API Gateway dashboard. A Claude Code skill reads markdown test case files, opens a browser via Playwright MCP, logs in, executes each test scenario using `browser_run_code` (Playwright API), and produces a pass/fail report with screenshots.

## How to Use It

### Running Test Cases

```
/agent-test run
```

The skill reads defaults (URL, credentials, cases path) from `test/agent-tests/config.md`. Override with flags:

```
/agent-test run --url {{BASE_URL}} --user admin --password "xxx" --cases test/agent-tests/cases/
```

Or with a cookie (if login automation is blocked):

```
/agent-test run --cookie "session_id=abc123"
```

### Generating Test Cases for a New Page

```
/agent-test generate --url {{BASE_URL}}/some-page
```

This reads the Vue component source code, opens the page in a browser, and generates markdown test case files covering the page's interactive elements.

### Test Case Format

Each test case is a markdown file:

```markdown
# Case: Gateway List - Filter by Type

**Page**: /
**Prerequisites**: Logged in

## Steps

1. Navigate to the gateway list page
2. Click the type filter dropdown
3. Select "可编程网关" (Programmable Gateway)

## Verify

- The gateway list updates to show only programmable gateways
- The type filter dropdown displays "可编程网关" as selected
```

### Test Report

After a run, a report is generated at `test/agent-tests/reports/YYYY-MM-DDTHH-MM-SS/report.md`:
- Summary (total, passed, failed)
- Per-case results with screenshots
- Timing information

## Directory Structure

```
test/agent-tests/
├── cases/                      # Test case markdown files
│   ├── case0-login.md          # Login/authentication test
│   ├── case1-gateway-list-filter-type.md
│   ├── case1-gateway-list-search.md
│   └── case1-gateway-list-sort.md
├── reports/                    # Generated reports (gitignored)
│   └── YYYY-MM-DDTHH-MM-SS/
│       ├── report.md
│       └── screenshots/
└── config.md                   # Default configuration

.claude/skills/agent-test.md    # The skill file
```

## Token Efficiency

The skill uses `browser_run_code` (Playwright API) instead of `browser_snapshot` — this is ~25x cheaper in tokens per interaction. Vue source code is read once per page to understand selectors before opening the browser.

## Prerequisites

- Claude Code with Playwright MCP tools enabled
- Access to the target BlueKing API Gateway dashboard environment
- Valid login credentials or session cookie
