# Research: Agent Test Suite

**Date**: 2026-03-24
**Branch**: `001-agent-test-suite`

## Technical Decisions

### Decision 1: Test Case Format — Markdown Files

**Decision**: Test cases will be written as structured markdown files, one per test scenario, stored in a `test/agent-cases/` directory.

**Rationale**:
- Human-readable and editable without special tools
- Version-controllable alongside the codebase
- Claude Code (the AI agent) can read, interpret, and execute them naturally
- Easy for QA team to write and review without learning a programming framework

**Alternatives considered**:
- Playwright TypeScript test files — rejected because the goal is agent-driven execution, not traditional test framework execution
- JSON/YAML structured files — rejected because markdown is more readable for QA testers
- Gherkin/Cucumber — rejected as unnecessary formalism; plain markdown with clear structure achieves the same goal with less tooling

### Decision 2: Execution Engine — Claude Code with Playwright MCP

**Decision**: The test runner is a Claude Code skill that reads markdown cases and uses the Playwright MCP browser tools (already available) to execute them.

**Rationale**:
- Playwright MCP tools are already available in the environment (`browser_navigate`, `browser_click`, `browser_snapshot`, `browser_type`, etc.)
- Claude Code can interpret natural-language test steps and map them to browser actions intelligently
- No additional test framework installation needed
- The agent can adapt to minor UI changes without test case rewrites (resilience)

**Alternatives considered**:
- Standalone Playwright test suite (TypeScript) — rejected because it requires traditional test maintenance and doesn't leverage AI interpretation
- Selenium — rejected as Playwright MCP is already available and more modern
- Cypress — rejected as it's a full framework with its own runner; overengineered for agent-driven approach

### Decision 3: Report Format — Markdown Report File

**Decision**: Test reports will be generated as markdown files with embedded screenshot references, stored in a `test/agent-reports/` directory with timestamp-based filenames.

**Rationale**:
- Consistent with the markdown-based approach
- Easy to review in any text editor or git diff
- Screenshots stored alongside the report in a subdirectory

**Alternatives considered**:
- HTML reports — more complex to generate, not necessary for initial version
- JUnit XML — useful for CI integration but not needed for local agent-driven runs
- Console-only output — insufficient for regression tracking over time

### Decision 4: Skill Architecture — Single Skill with Subcommands, Built via `/skill-creator`

**Decision**: Build as a single Claude Code skill (`agent-test`) with two modes, using the `/skill-creator` skill to create and validate the skill file:
1. `run` — execute test cases from the cases directory
2. `generate` — explore a page and generate new test cases

**Rationale**:
- Simple invocation model: `/agent-test run` or `/agent-test generate <url>`
- Single skill file is easier to maintain and distribute
- Both modes share common infrastructure (browser setup, authentication)
- `/skill-creator` ensures the skill follows Claude Code conventions, has proper trigger descriptions, and can be eval-tested for reliability

**Alternatives considered**:
- Manually writing the skill file — rejected because `/skill-creator` provides structure validation, trigger accuracy testing, and best practices that reduce iteration cycles

### Decision 5: Project Location

**Decision**: Test suite lives in `test/agent-tests/` at the repository root, separate from existing test infrastructure.

**Rationale**:
- `test/cases/` already contains Bruno API test collections — avoid mixing concerns
- `src/dashboard-front/` is the frontend source; test cases about the UI don't belong in the source tree
- Repository root `test/` directory is the established location for test assets

## Frontend Analysis

### Gateway List Page (`/`)

**Component**: `src/dashboard-front/src/views/home/Index.vue`
**Framework**: Vue 3.5.18 with Composition API (`<script setup lang="ts">`)
**UI Library**: `bkui-vue` (BlueKing UI component library)

**Key Interactive Elements**:

| Element | Component | Model | Test Action |
|---------|-----------|-------|-------------|
| Type filter dropdown | BkSelect | `filterNameData.kind` | Select option by text: 全部/普通网关/可编程网关 |
| Keyword search input | BkInput | `filterNameData.keyword` | Type text + Enter |
| Sort dropdown | BkSelect | `filterKey` | Select: 更新时间/创建时间/字母 A-Z |
| New gateway button | BkButton | — | Click to open dialog |

**API Endpoint**: `GET /gateways/` with query params: `keyword`, `kind`, `ordering`

### Authentication Flow

- Dashboard URL redirects to external login page when unauthenticated
- Login form accepts username/password
- Success sets cookie on subdomain, redirects back to dashboard
- CSRF token stored in cookie: `bk_apigw_dashboard_csrftoken`
- Session validated via `GET /account/user/` endpoint
- Alternative: inject cookie directly to skip login flow

### Existing Test Infrastructure

- **No existing browser/e2e tests** in the frontend
- **No Playwright config** exists
- Bruno API tests exist in `test/cases/` (backend API testing only)
- Dashboard backend uses pytest for unit tests
