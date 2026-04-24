# Implementation Plan: Agent Test Suite

**Branch**: `001-agent-test-suite` | **Date**: 2026-03-24 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-agent-test-suite/spec.md`

## Summary

Build an AI-agent-driven browser regression test suite for the BlueKing API Gateway dashboard. The system uses Claude Code with Playwright MCP tools to read markdown test case files, open a browser, authenticate, execute each test scenario, and produce a pass/fail report with screenshots. This replaces a 2-week manual regression cycle. The deliverable is a Claude Code skill (`/agent-test`) plus initial test cases for login and gateway list page.

## Technical Context

**Language/Version**: Markdown (test cases), Claude Code skill (orchestration)
**Primary Dependencies**: Playwright MCP browser tools (already available in Claude Code environment)
**Storage**: Local filesystem — markdown files for cases and reports, PNG screenshots
**Testing**: Self-testing — the test suite IS the testing tool; validated by running against the dev environment
**Target Platform**: macOS/Linux with Claude Code and Playwright MCP enabled
**Project Type**: CLI tool (Claude Code skill)
**Performance Goals**: Each test case completes in <60 seconds; full regression suite in <4 hours
**Constraints**: Must work with the existing Playwright MCP tools; no additional framework installation required
**Scale/Scope**: Initial 2 test cases (login + gateway list), expandable to cover all dashboard pages (~50 pages)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution is not customized for this project (template defaults). No gates to enforce.
**Status**: PASS (no violations)

## Project Structure

### Documentation (this feature)

```text
specs/001-agent-test-suite/
├── plan.md              # This file
├── research.md          # Technical decisions and frontend analysis
├── data-model.md        # Entity definitions
├── quickstart.md        # Usage guide
├── contracts/
│   ├── test-case-format.md    # Markdown format for test cases
│   └── test-report-format.md  # Markdown format for reports
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
test/agent-tests/
├── cases/                      # Test case markdown files
│   ├── case0-login.md          # Login/authentication test
│   └── case1-gateway-list.md   # Gateway list page filters & sorting
├── reports/                    # Generated reports (gitignored)
│   └── YYYY-MM-DDTHH-MM-SS/
│       ├── report.md
│       └── screenshots/
└── config.md                   # Default config (URL, auth hints)

.claude/skills/agent-test.md    # The Claude Code skill file
```

**Structure Decision**: Standalone test directory at `test/agent-tests/` — separate from existing `test/cases/` (Bruno API tests) to avoid mixing browser-based agent tests with API tests. The skill file lives in `.claude/skills/` following Claude Code conventions.

## Key Design Decisions

### 1. Agent-Driven vs. Traditional Test Framework

The test runner is Claude Code itself, not a Playwright test framework. Test cases are natural-language markdown that the agent interprets and executes using Playwright MCP tools. This provides:
- **Resilience**: Agent can adapt to minor UI changes (button text changes, layout shifts)
- **No code maintenance**: Test cases are human-readable markdown, not TypeScript
- **Lower barrier**: QA team writes markdown, not code

### 2. Test Case Execution Flow

```
1. Read config.md for defaults
2. Authenticate (credentials → browser login, or cookie injection)
3. Discover case files in cases/ directory (sorted alphabetically)
4. For each case:
   a. Read markdown, parse page URL + steps + verifications
   b. Navigate to page
   c. Execute each step using Playwright MCP tools
   d. Take screenshots at each step
   e. Check verifications using browser_snapshot
   f. Record result (pass/fail/skip/error)
5. Generate report.md with all results
```

### 3. Authentication Strategy

Two modes supported:
- **Credentials mode**: Navigate to URL → follow redirect to login → fill username/password → submit → wait for redirect back
- **Cookie mode**: Inject provided cookie into browser context → navigate directly to dashboard

Cookie mode is the fallback when automated login is blocked by captchas or other anti-automation measures.

### 4. Skill Creation via `/skill-creator`

The Claude Code skill (`/agent-test`) MUST be created using the `/skill-creator` skill, which provides:
- Proper skill file structure and metadata conventions
- Best practices for skill description (trigger accuracy)
- Eval-driven validation to ensure the skill triggers correctly
- Performance benchmarking and variance analysis

**Workflow**: Use `/skill-creator` to scaffold the skill, then populate it with the agent-test logic (authentication, case parsing, execution loop, report generation). This ensures the skill follows Claude Code conventions and triggers reliably when users invoke `/agent-test`.

**Skill file**: `.claude/skills/agent-test.md` — created and refined via `/skill-creator`

### 5. Skill Subcommands

The skill supports two modes passed as arguments:

- **`/agent-test run`** — Execute all test cases from the cases directory against the target URL
- **`/agent-test generate <page-url>`** — Explore a page in the browser + read Vue source code → generate new markdown test case files

Both modes share the authentication flow (credentials or cookie injection).

## Implementation Tooling

| Tool | Purpose | When |
|------|---------|------|
| `/skill-creator` | Create and validate the `/agent-test` skill file | Task: Skill creation |
| Playwright MCP | Browser automation (navigate, click, type, snapshot, screenshot) | Runtime: Test execution |
| `src/dashboard-front/` | Read Vue components to understand page structure | Runtime: Test case generation |
| Markdown files | Test cases, reports, config | All phases |

## Complexity Tracking

No constitution violations — no complexity justification needed.
