# Research: BDD Test Refactor

**Date**: 2026-03-30
**Feature**: 002-bdd-test-refactor

## R1: BDD Case Format for Chinese Playwright Tests

**Decision**: Gherkin-style markdown in Chinese with structured metadata headers.

**Rationale**:
- Chinese Gherkin keywords (功能/场景/假设/当/那么) are standard BDD terminology
- Markdown format supports git diff tracking and easy editing
- Structured metadata headers (模块, 页面, 优先级) enable automated script mapping
- One file per functional area allows multiple scenarios per file

**Alternatives considered**:
- YAML-based cases: Rejected — less human-readable, harder for QA to maintain
- English Gherkin with Chinese comments: Rejected — user explicitly requires Chinese content
- Custom JSON format: Rejected — not easily editable by non-developers
- Cucumber `.feature` files: Rejected — adds Cucumber dependency, markdown is simpler

## R2: Playwright Test Runner Configuration

**Decision**: Use `@playwright/test` with sequential execution and native global setup/teardown.

**Rationale**:
- `workers: 1` ensures sequential execution (required for shared test gateway state)
- `globalSetup`/`globalTeardown` natively handle test gateway lifecycle
- Built-in timeout handling (`timeout` per test, `globalTimeout` for suite)
- JSON + HTML reporters provide both machine-readable and human-readable output
- Exit code behavior is built-in (non-zero on failure)
- `npx playwright test` works in CI/CD without additional tooling

**Configuration details**:
- `timeout: 60000` (60s per test)
- `globalTimeout: 1800000` (30 min for entire suite)
- `retries: 0` (deterministic — no flaky retries)
- `reporter: [['json', { outputFile: 'results.json' }], ['html']]`
- Environment variables: `TEST_URL`, `TEST_USER`, `TEST_PASSWORD`, `TEST_COOKIE`, `TEST_GATEWAY_ID`

**Alternatives considered**:
- Custom shell runner: Rejected — reinvents reporter, timeout, and exit code handling
- Jest + Playwright: Rejected — Playwright Test is the official runner, better integration
- Mocha: Rejected — less Playwright-native

## R3: Excel Module Consolidation Strategy

**Decision**: Consolidate 835 cases → ~100 by selecting core workflow scenarios per module.

**Analysis of 20 existing modules** (835 cases total):

| Module | Cases | Core Scenarios | Strategy |
|--------|-------|----------------|----------|
| 01-my-gateway | 40 | 5 | CRUD gateway + basic validation |
| 02-resource-config | ~80 | 8 | Create/edit/delete resource + import |
| 03-resource-version | ~40 | 4 | Generate/view/compare versions |
| 04-sdk-list | ~15 | 2 | View/filter SDKs |
| 05-env-overview | ~60 | 6 | Publish/unpublish + env view |
| 06-env-resource-info | ~30 | 3 | View/filter env resources |
| 07-env-plugin-mgmt | ~50 | 5 | CRUD plugins |
| 08-env-variable-mgmt | ~30 | 3 | CRUD env variables |
| 09-release-records | ~20 | 2 | View/filter releases |
| 10-backend-service | ~40 | 4 | CRUD backend services |
| 11-permission-approval | ~40 | 4 | Approve/reject permissions |
| 12-app-permissions | ~30 | 3 | View/manage app permissions |
| 13-access-log | ~30 | 3 | View/filter/search logs |
| 14-statistics | ~20 | 2 | View statistics charts |
| 15-online-debug | ~40 | 5 | Debug request lifecycle |
| 16-debug-request-history | ~15 | 2 | View debug history |
| 17-basic-info | ~20 | 3 | View/edit gateway info |
| 18-mcp-server | ~15 | 2 | MCP server management |
| 19-mcp-permission-approval | ~15 | 2 | MCP permission flows |
| 20-operation-records | ~15 | 2 | View operation logs |

**Estimated total**: ~70-100 core scenarios

**Consolidation principles**:
1. One BDD scenario per CRUD operation per module (Create, Read, Update, Delete)
2. Validation edge cases folded into create/edit scenarios (not separate cases)
3. Only P1/P2 cases retained; P3 only if testing unique functionality
4. Filter/search/sort operations grouped into one "列表操作" scenario per module
5. Each BDD file: one `# 功能` with 3-8 `## 场景` blocks
