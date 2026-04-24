# Tasks: Agent Test Suite

**Input**: Design documents from `/specs/001-agent-test-suite/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested — test tasks omitted. The test suite itself IS the testing tool; validation is done by running cases against the dev environment.

**Organization**: Tasks grouped by user story. US3 (Login/Auth) is foundational since all other stories depend on authentication.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create directory structure, config file, and gitignore for the test suite

- [x] T001 Create directory structure: `test/agent-tests/cases/`, `test/agent-tests/reports/`, `.claude/skills/`
- [x] T002 [P] Create default configuration file at `test/agent-tests/config.md` with target URL, auth method options, and cases directory path per quickstart.md
- [x] T003 [P] Add `test/agent-tests/reports/` to `.gitignore` to exclude generated reports and screenshots from version control

---

## Phase 2: Foundational — Login & Session Management (US3, Priority: P1)

**Purpose**: Authentication infrastructure that MUST work before ANY test case can execute

**⚠️ CRITICAL**: No test case execution (US1) or generation (US2) can work without authentication

**Goal**: System can authenticate with the dashboard via browser login (username/password with redirect) or via pre-injected cookie

**Independent Test**: Navigate to `{{BASE_URL}}`, complete the login flow, and verify the page shows logged-in state

- [x] T004 [US3] Write login test case at `test/agent-tests/cases/case0-login.md` following the test-case-format contract: Page=/, Steps cover navigating to URL, following redirect to login page, entering username `admin` and password, submitting form, and waiting for redirect back to dashboard. Verify section checks that dashboard loads in logged-in state (user info visible, no login redirect).
- [x] T005 [US3] Manually validate `case0-login.md` by executing its steps using Playwright MCP tools against `{{BASE_URL}}` — confirm login flow works end-to-end (redirect → login form → credentials → redirect back → logged-in state). Document the exact login page URL, form field selectors, and cookie names observed. If login automation is blocked, document the fallback cookie injection approach.

**Checkpoint**: Authentication works — can log into the dashboard and maintain session. Ready for test case execution.

---

## Phase 3: User Story 1 — Run Existing Regression Test Cases (Priority: P1) 🎯 MVP

**Goal**: Execute markdown test cases against the dashboard via browser automation, producing a pass/fail report with screenshots

**Independent Test**: Run `case0-login.md` and `case1-gateway-list.md` against the dev environment and get a structured report

### Initial Test Cases

- [x] T006 [P] [US1] Write gateway list filter-by-type test case at `test/agent-tests/cases/case1-gateway-list-filter-type.md`: Page=/, Steps cover clicking the type filter dropdown and selecting each option (全部, 普通网关, 可编程网关). Verify list updates to show only gateways of the selected type.
- [x] T007 [P] [US1] Write gateway list keyword search test case at `test/agent-tests/cases/case1-gateway-list-search.md`: Page=/, Steps cover typing `test` in the keyword search input and pressing Enter. Verify list filters to show only gateways matching the keyword.
- [x] T008 [P] [US1] Write gateway list sort test case at `test/agent-tests/cases/case1-gateway-list-sort.md`: Page=/, Steps cover clicking the sort dropdown and selecting each option (更新时间, 创建时间, 字母 A-Z). Verify list reorders according to the selected sort criterion.

### Skill — Run Mode (via `/skill-creator`)

- [x] T009 [US1] Use `/skill-creator` to create the `/agent-test` skill file at `.claude/skills/agent-test.md`. The skill should define: name (`agent-test`), description (browser-based regression test runner for the BlueKing API Gateway dashboard), trigger pattern (`/agent-test`). Initial content focuses on the `run` subcommand only — `generate` subcommand added in US2 phase.
- [x] T010 [US1] Populate the `run` subcommand logic in `.claude/skills/agent-test.md` with these sections:
  1. **Input parsing**: Accept `--url`, `--user`/`--password` OR `--cookie`, `--cases` directory path. Fall back to defaults from `test/agent-tests/config.md` if not provided.
  2. **Authentication flow**: If credentials provided, use Playwright MCP to navigate to URL, follow redirect to login, fill form, submit, wait for redirect back. If cookie provided, inject cookie via `browser_evaluate` then navigate. Reference the login page details documented in T005.
  3. **Case discovery**: Read all `*.md` files from the cases directory sorted alphabetically. Parse each file to extract Title, Page, Prerequisites, Steps, and Verify sections per the test-case-format contract.
  4. **Case execution loop**: For each case: navigate to Page URL, execute each Step using appropriate Playwright MCP tools (`browser_click`, `browser_type`, `browser_select_option`, `browser_snapshot`, `browser_press_key`), take `browser_take_screenshot` after each step, check Verify items using `browser_snapshot` output, record pass/fail/skip/error result. Continue to next case on failure (no fail-fast).
  5. **Report generation**: After all cases execute, write a report markdown file to `test/agent-tests/reports/YYYY-MM-DDTHH-MM-SS/report.md` following the test-report-format contract. Save all screenshots to the `screenshots/` subdirectory.
  6. **Error handling**: Handle site unreachable, auth failure, element not found, timeout. Provide clear failure messages with expected vs. observed.
- [x] T011 [US1] Validate the `/agent-test run` skill by invoking it against the dev environment with `case0-login.md` and one `case1-*` file. Verify: browser opens, login succeeds, cases execute, screenshots are captured, report is generated at the expected path with correct pass/fail status.

**Checkpoint**: MVP complete — `/agent-test run` executes markdown test cases and produces a report. User Story 1 is independently functional.

---

## Phase 4: User Story 2 — Auto-Generate Test Cases for New/Changed Pages (Priority: P2)

**Goal**: Explore a page in the browser and read Vue source code to automatically generate markdown test case files

**Independent Test**: Point the generator at the gateway list page (`/`) and verify it produces test case files covering the type dropdown, keyword search, and sort dropdown

- [x] T012 [US2] Add the `generate` subcommand to the `/agent-test` skill in `.claude/skills/agent-test.md`. The generate flow:
  1. **Input parsing**: Accept `--url` (specific page URL to explore), `--cases` (output directory for generated cases). Authenticate first using the same flow as `run` mode.
  2. **Page exploration**: Navigate to the target URL. Use `browser_snapshot` to capture the accessibility tree of the page. Identify all interactive elements: buttons, inputs, dropdowns (select), links, tables, forms.
  3. **Source code analysis**: Map the page URL to the corresponding Vue component in `src/dashboard-front/src/views/` by reading the router config. Read the Vue component file to understand: data models, event handlers, API calls, component props. This enriches the test cases with domain-specific context (e.g., knowing a dropdown filters by gateway type).
  4. **Case generation**: For each interactive element or logical group of elements, generate a markdown test case file following the test-case-format contract. Name files using `case[N]-[page]-[interaction].md` convention. Write generated files to the cases directory.
  5. **Summary output**: Report how many cases were generated and list the file names.
- [ ] T013 [US2] Validate the generate subcommand by running `/agent-test generate --url {{BASE_URL}}` and verifying the generated case files: cover the type filter dropdown, keyword search, and sort dropdown; follow the markdown format contract; are executable by `/agent-test run`. **STATUS: Ready — invoke `/agent-test generate` to validate.**

**Checkpoint**: `/agent-test generate` produces runnable test cases from page exploration. User Story 2 is independently functional.

---

## Phase 5: User Story 4 — Skill Refinement & Packaging (Priority: P3)

**Goal**: Polish the skill for team-wide adoption — clear documentation, parameter validation, helpful prompts for missing inputs

**Independent Test**: A team member who has never used the tool invokes `/agent-test` and successfully runs test cases within 15 minutes

- [x] T014 [US4] Refine the `/agent-test` skill description and trigger in `.claude/skills/agent-test.md` using `/skill-creator` eval capabilities. Ensure the skill triggers correctly for inputs like: "run regression tests", "test the dashboard", "generate test cases for this page", `/agent-test run`, `/agent-test generate`.
- [x] T015 [US4] Add parameter validation and user prompting to `.claude/skills/agent-test.md`: when invoked without required parameters (URL, credentials), prompt the user with clear descriptions of what's needed and offer to read defaults from `test/agent-tests/config.md`.
- [x] T016 [US4] Add session re-authentication support to the `run` subcommand in `.claude/skills/agent-test.md`: detect when a page load results in a login redirect (auth expired), re-execute the authentication flow, then retry the current test step.

**Checkpoint**: Skill is polished, well-documented, and team-ready.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that benefit all user stories

- [x] T017 [P] Update `test/agent-tests/config.md` with final default values based on validated dev environment details from T005 (login page URL, cookie names, base URL)
- [x] T018 [P] Review and update `specs/001-agent-test-suite/quickstart.md` to match the final skill interface and actual invocation syntax
- [ ] T019 Run full regression suite: execute `/agent-test run` with all cases (case0 + case1-*) and verify the complete report is accurate, screenshots are captured, and no false positives occur. **STATUS: Ready — invoke `/agent-test run` in a new session to validate.**

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational/Auth (Phase 2)**: Depends on Phase 1 (directory structure must exist)
- **US1 - Run Cases (Phase 3)**: Depends on Phase 2 (auth must work). T006-T008 (test cases) can parallel with T009-T010 (skill creation)
- **US2 - Generate Cases (Phase 4)**: Depends on Phase 3 (run mode must work first, so generated cases can be validated)
- **US4 - Skill Packaging (Phase 5)**: Depends on Phase 3 + Phase 4 (both subcommands must exist before polishing)
- **Polish (Phase 6)**: Depends on all previous phases

### User Story Dependencies

- **US3 (Auth)**: Foundational — no dependencies on other stories, blocks all others
- **US1 (Run Cases)**: Depends on US3 (auth). Core MVP.
- **US2 (Generate Cases)**: Depends on US1 (needs run mode to validate generated cases)
- **US4 (Skill Packaging)**: Depends on US1 + US2 (polishes the complete skill)

### Within Each User Story

- Test case files before skill logic (need cases to test against)
- Skill logic before validation (need skill to validate)
- Validation before moving to next story

### Parallel Opportunities

- T002 + T003 can run in parallel (config and gitignore — different files)
- T006 + T007 + T008 can run in parallel (independent test case files)
- T006-T008 can run in parallel with T009-T010 (test cases and skill creation are independent files)
- T017 + T018 can run in parallel (config update and docs update)

---

## Parallel Example: Phase 3 (User Story 1)

```
# Write all gateway list test cases in parallel:
Task: "Write filter-by-type test case at test/agent-tests/cases/case1-gateway-list-filter-type.md" (T006)
Task: "Write keyword search test case at test/agent-tests/cases/case1-gateway-list-search.md" (T007)
Task: "Write sort test case at test/agent-tests/cases/case1-gateway-list-sort.md" (T008)

# Meanwhile, scaffold the skill:
Task: "Use /skill-creator to create /agent-test skill at .claude/skills/agent-test.md" (T009)
```

---

## Implementation Strategy

### MVP First (Phase 1 + 2 + 3 = User Stories 3 + 1)

1. Complete Phase 1: Setup (directory structure, config, gitignore)
2. Complete Phase 2: Login/Auth (write case0, validate login flow manually)
3. Complete Phase 3: Run mode (write case1-*, create skill, validate end-to-end)
4. **STOP and VALIDATE**: Run `/agent-test run` with all cases, verify report
5. ✅ MVP delivered — team can write markdown cases and run automated regression

### Incremental Delivery

1. Setup + Auth + Run Mode → **MVP!** Team can run regression tests
2. Add Generate Mode → Team can auto-generate cases for new pages
3. Add Skill Polish → Frictionless team-wide adoption
4. Each increment adds value without breaking previous functionality

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- The `/skill-creator` skill is used for T009 and T014 to ensure proper Claude Code skill conventions
- Validation tasks (T005, T011, T013) require access to the dev environment (URL configured in `test/agent-tests/config.md`)
- If automated login is blocked (captcha, etc.), T005 documents the cookie fallback approach and all subsequent tasks use cookie mode
- Commit after each completed task or logical group
