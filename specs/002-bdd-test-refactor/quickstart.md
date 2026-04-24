# Quickstart: BDD Test Refactor

**Date**: 2026-03-30
**Feature**: 002-bdd-test-refactor

## Prerequisites

- Node.js 18+ installed
- Python 3.11+ installed (for Excel conversion only)
- Access to a deployed BlueKing API Gateway environment
- Valid credentials (username+password or cookie)

## 1. Install Dependencies

```bash
cd test/bdd-scripts
npm install
npx playwright install chromium
```

## 2. Run All Tests

```bash
# With username + password
make test-bdd URL=https://your-gateway.example.com USER=admin PASSWORD=your-password

# With cookie
make test-bdd URL=https://your-gateway.example.com COOKIE="session_id=your-cookie-value"
```

## 3. View Reports

After a test run:

- **Console**: Real-time pass/fail output
- **HTML Report**: `test/bdd-scripts/playwright-report/index.html`
- **JSON Report**: `test/bdd-scripts/test-results/results.json`
- **Failure Screenshots**: `test/bdd-scripts/test-results/`

## 4. Generate Scripts from BDD Cases (Agent-Assisted)

When BDD cases change or new ones are added:

```
/bdd-test-gen generate --url https://your-env.example.com --user admin --password xxx --case test/bdd-cases/01-网关管理/01-创建普通网关.md
```

Or generate all:

```
/bdd-test-gen generate --url https://your-env.example.com --user admin --password xxx --all
```

## 5. Edit BDD Cases

BDD cases are in `test/bdd-cases/` as Chinese markdown files. Edit directly, then regenerate the corresponding script using step 4.

## Directory Structure

```
test/bdd-cases/           # Human-readable BDD cases (Chinese markdown)
├── 01-网关管理/
├── 02-资源配置/
└── ...

test/bdd-scripts/         # Executable Playwright scripts (generated)
├── playwright.config.js
├── package.json
├── setup.js
├── teardown.js
├── helpers.js
├── 01-网关管理/
├── 02-资源配置/
└── ...
```
