# Implementation Plan: BDD Test Refactor

**Branch**: `002-bdd-test-refactor` | **Date**: 2026-03-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-bdd-test-refactor/spec.md`

## Summary

Refactor the BlueKing API Gateway test suite from an agent-driven, token-intensive execution model (835 individual markdown cases interpreted by LLM at runtime) to a deterministic, script-based model. The pipeline has three phases: (1) one-time conversion of 835 Excel-derived cases into ~100 curated BDD cases in Chinese, (2) an AI agent SKILL that reads BDD cases and generates executable Playwright scripts by exploring the live application, (3) a `make` command that runs all scripts without any agent involvement.

## Technical Context

**Language/Version**: Python 3.11+ (Excel parsing, test runner), JavaScript/Node.js (Playwright scripts)
**Primary Dependencies**: Playwright (browser automation), Python stdlib (xlsx parsing via existing convert_excel.py)
**Storage**: File-based (markdown BDD cases, JS test scripts, JSON reports)
**Testing**: Playwright Test runner for script execution, shell-based test runner via Makefile
**Target Platform**: macOS/Linux development machines, CI/CD servers
**Project Type**: Test infrastructure / tooling
**Performance Goals**: Full test suite run <30 minutes, individual script <60 seconds
**Constraints**: Zero LLM token consumption during script execution; scripts must be deterministic
**Scale/Scope**: ~100 BDD cases → ~100 executable scripts, 20 functional modules

## Constitution Check

*GATE: Constitution is not configured (template only). No gates to enforce.*

## Project Structure

### Documentation (this feature)

```text
specs/002-bdd-test-refactor/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
test/bdd-cases/                      # BDD case files (Chinese, committed)
├── 01-网关管理/
│   ├── 01-创建普通网关.md
│   ├── 02-创建可编程网关.md
│   └── ...
├── 02-资源配置/
│   ├── 01-创建资源.md
│   └── ...
├── 03-资源版本/
├── 04-环境管理/
├── 05-后端服务/
├── 06-权限管理/
├── 07-插件管理/
├── 08-日志与统计/
├── 09-在线调试/
├── 10-基本信息/
└── ...

test/bdd-scripts/                    # Generated executable scripts (committed)
├── setup.js                         # Shared setup: create test gateway + preconditions
├── teardown.js                      # Shared teardown: delete test gateway
├── helpers.js                       # Shared utility functions (auth, selectors, waits)
├── 01-网关管理/
│   ├── 01-创建普通网关.spec.js
│   ├── 02-创建可编程网关.spec.js
│   └── ...
├── 02-资源配置/
│   └── ...
└── ...

test/bdd-scripts/playwright.config.js  # Playwright configuration
test/bdd-scripts/package.json           # Node dependencies (playwright)

.agents/skills/bdd-test-gen/SKILL.md   # New SKILL for agent-assisted script generation

test/agent-tests/AGENTS.md             # Rewritten: post-refactor business context only

Makefile                               # make test-bdd target
```

**Structure Decision**: Two parallel directory trees under `test/` — `bdd-cases/` for human-readable BDD specifications (Chinese markdown) and `bdd-scripts/` for generated Playwright test scripts. Directories are numbered and named in Chinese matching the module structure. The old `test/agent-tests/` contents (except the rewritten AGENTS.md) and `.agents/skills/agent-test/` are deleted.

## Phase 0: Research

### Research Tasks

1. **BDD case format for Chinese Playwright tests**: What markdown BDD format works best for Chinese test cases that will be parsed by an agent to generate Playwright scripts?
2. **Playwright Test runner configuration**: Best practices for running Playwright tests sequentially with shared setup/teardown, timeout handling, and report generation.
3. **Excel module mapping**: Analyze the 835 existing cases across 20 modules to determine which modules have the most redundancy and how to consolidate to ~100 core cases.

### Research Findings

#### 1. BDD Case Format

**Decision**: Use Gherkin-style markdown in Chinese with structured metadata headers.

**Format**:
```markdown
# 功能: [模块名] - [功能描述]

**模块**: [模块名]
**页面**: [URL path]
**优先级**: P1/P2/P3
**前置条件**: [prerequisites]

## 场景: [场景描述]

- **假设** [初始状态]
- **当** [用户操作]
- **那么** [预期结果]

## 场景: [另一个场景]

- **假设** ...
- **当** ...
- **那么** ...
```

**Rationale**: Chinese Gherkin keywords (功能/场景/假设/当/那么) are standard and widely understood by Chinese QA teams. Markdown format allows easy editing and git diff tracking. Metadata headers enable automated script mapping.

**Alternatives considered**: YAML-based cases (rejected — less readable), English Gherkin (rejected — user requires Chinese), custom JSON (rejected — harder to maintain).

#### 2. Playwright Test Runner

**Decision**: Use Playwright Test (`@playwright/test`) with sequential execution, shared global setup/teardown, and HTML + JSON reporters.

**Configuration approach**:
- `playwright.config.js` with `workers: 1` (sequential)
- `globalSetup` pointing to `setup.js` (creates test gateway)
- `globalTeardown` pointing to `teardown.js` (deletes test gateway)
- Environment variables for URL, credentials, cookie
- `timeout: 60000` per test, `globalTimeout: 1800000` (30 min)
- JSON reporter for machine-readable results, HTML reporter for human review

**Rationale**: Playwright Test is the standard runner, supports global setup/teardown natively, produces exit codes for CI/CD, and handles timeouts out of the box.

#### 3. Excel Module Consolidation Strategy

**Decision**: Consolidate 835 cases → ~100 cases by selecting 3-8 core workflow scenarios per module.

**Module analysis** (20 modules, 835 cases):
- Focus on CRUD core paths per module (create → read → update → delete)
- Merge validation edge cases into the create/edit scenario (e.g., name validation folded into create gateway scenario)
- Keep only P1/P2 priority cases; P3 edge cases only if they test unique functionality
- Each BDD file can contain multiple scenarios for the same feature area

**Target distribution**: ~5 scenarios per module × 20 modules = ~100 scenarios.

## Phase 1: Design & Contracts

### Data Model

*See [data-model.md](./data-model.md) for full details.*

Key entities:
- **BDD Case File**: Markdown file with structured Gherkin-style scenarios in Chinese
- **Test Script**: Playwright `.spec.js` file generated from a BDD case
- **Test Gateway**: Ephemeral gateway created during setup, shared across all tests, deleted during teardown
- **Test Report**: JSON + HTML output from Playwright Test runner

### Contracts

#### BDD Case File Contract

```markdown
# 功能: [模块名] - [功能描述]

**模块**: [模块名]
**页面**: [URL path pattern, e.g., /:gatewayId/resource]
**优先级**: P1|P2|P3
**前置条件**: [comma-separated prerequisites]

## 场景: [场景名称]

- **假设** [precondition state]
- **当** [user action 1]
- **并且** [user action 2] (optional, for multi-step)
- **那么** [expected outcome]
- **并且** [additional verification] (optional)
```

#### Test Script Contract

Each `.spec.js` file:
- Imports from shared `helpers.js` (auth, selectors, navigation)
- Reads `TEST_URL`, `TEST_USER`, `TEST_PASSWORD`, `TEST_COOKIE`, `TEST_GATEWAY_ID` from environment
- Contains one `test.describe` block per BDD `# 功能`
- Contains one `test()` block per `## 场景`
- Each test: navigate → interact → assert
- On auth failure: calls `helpers.reAuth()`
- On failure: captures screenshot to `test-results/`

#### Make Command Contract

```makefile
test-bdd:  # Run all BDD test scripts
	@echo "Usage: make test-bdd URL=<url> USER=<user> PASSWORD=<pass>"
	@echo "   or: make test-bdd URL=<url> COOKIE=<cookie>"
	cd test/bdd-scripts && \
	TEST_URL=$(URL) TEST_USER=$(USER) TEST_PASSWORD=$(PASSWORD) TEST_COOKIE=$(COOKIE) \
	npx playwright test --config=playwright.config.js
```

#### SKILL Invocation Contract

```
bdd-test-gen generate --url <URL> --user <USER> --password <PASSWORD> [--case <BDD_FILE>] [--all]
bdd-test-gen generate --url <URL> --cookie <COOKIE> [--case <BDD_FILE>] [--all]
```

### Quickstart

*See [quickstart.md](./quickstart.md) for setup instructions.*
