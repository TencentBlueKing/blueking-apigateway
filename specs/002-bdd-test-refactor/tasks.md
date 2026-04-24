# Tasks: BDD Test Refactor

**Input**: Design documents from `/specs/002-bdd-test-refactor/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in the feature specification. Tests are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create directory structure and initialize the Node.js project for Playwright scripts

- [x] T001 Create BDD cases directory structure with module subdirectories in test/bdd-cases/ (01-网关管理/ through 20-操作记录/, matching the 20 modules from research.md)
- [x] T002 Create BDD scripts directory structure in test/bdd-scripts/ with matching module subdirectories (01-网关管理/ through 20-操作记录/)
- [x] T003 Initialize Node.js project in test/bdd-scripts/package.json with @playwright/test dependency
- [x] T004 Add .gitignore entries for test/bdd-scripts/node_modules/, test/bdd-scripts/test-results/, test/bdd-scripts/playwright-report/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Parse the Excel file to understand the full module structure and case distribution before BDD conversion begins

**⚠️ CRITICAL**: US1 depends on understanding the Excel structure. US2 and US3 depend on having BDD cases and shared scripts.

- [x] T005 Read and parse the Excel file at '/Users/wklken/Library/Containers/com.tencent.WeWorkMac/Data/Documents/Profiles/44B017ECCED31FF293ECBD290E867905/Caches/Files/2026-03/7b0aa56134751f4b6bd36bd9013fde2c/蓝鲸API网关测试用例.xlsx' using the existing test/agent-tests/convert_excel.py (or Python stdlib) to extract all 835 cases with columns: 模块, 用例名称, 用例等级, 前置条件, 用例步骤, 预期结果. Output a structured JSON summary grouped by module with case counts.
- [x] T006 Analyze the extracted cases per module: identify which cases are P1/P2 core workflows vs P3 edge cases, which cases are redundant or overlapping, and produce a consolidation plan mapping ~835 cases → ~100 BDD scenarios (following the strategy in research.md R3).

**Checkpoint**: Excel parsed, module structure understood, consolidation plan ready. BDD case generation can begin.

---

## Phase 3: User Story 1 - Convert Excel Cases to Optimized BDD Cases (Priority: P1) 🎯 MVP

**Goal**: Transform 835 Excel cases into ~100 curated BDD cases in Chinese, organized by module, committed to the repository. Clean up all legacy artifacts.

**Independent Test**: Verify that test/bdd-cases/ contains ~100 BDD markdown files, all in Chinese, covering all 20 modules, following the Gherkin format defined in contracts/bdd-case-format.md.

### Implementation for User Story 1

- [x] T007 [P] [US1] Generate BDD cases for 01-网关管理 module (~5 scenarios: 创建普通网关, 创建可编程网关, 编辑网关, 停用网关, 删除网关) in test/bdd-cases/01-网关管理/. Follow format from contracts/bdd-case-format.md. All content in Chinese.
- [x] T008 [P] [US1] Generate BDD cases for 02-资源配置 module (~8 scenarios: 创建资源, 编辑资源, 删除资源, 导入资源, 查看资源列表, 资源筛选, 批量操作, 资源标签) in test/bdd-cases/02-资源配置/
- [x] T009 [P] [US1] Generate BDD cases for 03-资源版本 module (~4 scenarios: 生成版本, 查看版本列表, 版本对比, 版本详情) in test/bdd-cases/03-资源版本/
- [x] T010 [P] [US1] Generate BDD cases for 04-SDK列表 module (~2 scenarios: 查看SDK列表, SDK筛选) in test/bdd-cases/04-SDK列表/
- [x] T011 [P] [US1] Generate BDD cases for 05-环境概览 module (~6 scenarios: 查看环境概览, 发布资源, 下架资源, 环境切换, 发布历史, 环境状态) in test/bdd-cases/05-环境概览/
- [x] T012 [P] [US1] Generate BDD cases for 06-环境资源信息 module (~3 scenarios: 查看资源信息, 资源筛选, 资源详情) in test/bdd-cases/06-环境资源信息/
- [x] T013 [P] [US1] Generate BDD cases for 07-环境插件管理 module (~5 scenarios: 添加插件, 编辑插件, 删除插件, 查看插件列表, 插件类型筛选) in test/bdd-cases/07-环境插件管理/
- [x] T014 [P] [US1] Generate BDD cases for 08-环境变量管理 module (~3 scenarios: 创建变量, 编辑变量, 删除变量) in test/bdd-cases/08-环境变量管理/
- [x] T015 [P] [US1] Generate BDD cases for 09-发布记录 module (~2 scenarios: 查看发布记录, 记录筛选) in test/bdd-cases/09-发布记录/
- [x] T016 [P] [US1] Generate BDD cases for 10-后端服务 module (~4 scenarios: 创建后端服务, 编辑后端服务, 删除后端服务, 查看服务列表) in test/bdd-cases/10-后端服务/
- [x] T017 [P] [US1] Generate BDD cases for 11-权限审批 module (~4 scenarios: 查看审批列表, 审批通过, 审批驳回, 审批筛选) in test/bdd-cases/11-权限审批/
- [x] T018 [P] [US1] Generate BDD cases for 12-应用权限 module (~3 scenarios: 查看应用权限, 权限管理, 权限筛选) in test/bdd-cases/12-应用权限/
- [x] T019 [P] [US1] Generate BDD cases for 13-访问日志 module (~3 scenarios: 查看访问日志, 日志搜索, 日志筛选) in test/bdd-cases/13-访问日志/
- [x] T020 [P] [US1] Generate BDD cases for 14-统计报表 module (~2 scenarios: 查看统计图表, 时间范围切换) in test/bdd-cases/14-统计报表/
- [x] T021 [P] [US1] Generate BDD cases for 15-在线调试 module (~5 scenarios: 发送调试请求, 查看响应, 设置请求参数, 选择环境, 认证配置) in test/bdd-cases/15-在线调试/
- [x] T022 [P] [US1] Generate BDD cases for 16-调试历史 module (~2 scenarios: 查看调试历史, 历史筛选) in test/bdd-cases/16-调试历史/
- [x] T023 [P] [US1] Generate BDD cases for 17-基本信息 module (~3 scenarios: 查看基本信息, 编辑基本信息, 状态管理) in test/bdd-cases/17-基本信息/
- [x] T024 [P] [US1] Generate BDD cases for 18-MCP服务 module (~2 scenarios: MCP服务管理, MCP配置) in test/bdd-cases/18-MCP服务/
- [x] T025 [P] [US1] Generate BDD cases for 19-MCP权限审批 module (~2 scenarios: MCP权限审批, MCP审批筛选) in test/bdd-cases/19-MCP权限审批/
- [x] T026 [P] [US1] Generate BDD cases for 20-操作记录 module (~2 scenarios: 查看操作记录, 记录筛选) in test/bdd-cases/20-操作记录/
- [x] T027 [US1] Review all generated BDD cases: verify total count is ~100, all modules covered, format consistent with contracts/bdd-case-format.md, all content in Chinese, no implementation details leak into case steps
- [x] T028 [US1] Delete legacy artifacts: remove .agents/skills/agent-test/ directory entirely, remove all files in test/agent-tests/ except AGENTS.md (json, py, js, yaml, cases/ directory, reports/ directory, config.md, invalid_test.json, test_swagger.yaml)

**Checkpoint**: test/bdd-cases/ contains ~100 curated BDD cases in Chinese. Legacy artifacts cleaned up. US1 complete and independently verifiable.

---

## Phase 4: User Story 2 - Agent-Assisted Script Generation SKILL (Priority: P2)

**Goal**: Create a SKILL definition file and shared test infrastructure (helpers, setup, teardown) that enables an AI agent to convert BDD cases into executable Playwright scripts by exploring a live environment.

**Independent Test**: Invoke the SKILL on a single BDD case with a live environment and verify it produces a valid, executable .spec.js file.

### Implementation for User Story 2

- [x] T029 [P] [US2] Create shared helpers module in test/bdd-scripts/helpers.js with functions: login(page), reAuth(page), waitForPageReady(page), fillForm(page, fields), selectDropdown(page, selector, text), closeSlider(page), getToastMessage(page), getTableRowCount(page). Follow the contract in contracts/test-script-format.md. Port reusable patterns from existing test/agent-tests/helpers.js.
- [x] T030 [P] [US2] Create global setup script in test/bdd-scripts/setup.js: authenticates using TEST_URL + TEST_USER/TEST_PASSWORD or TEST_COOKIE env vars, creates a test gateway (普通网关, private, name=testagent-<timestamp>), configures backend service (httpbin.org:80), creates a test resource, generates a resource version, publishes to prod stage. Exports TEST_GATEWAY_ID to a .env file for downstream scripts. Follow the test gateway lifecycle from data-model.md.
- [x] T031 [P] [US2] Create global teardown script in test/bdd-scripts/teardown.js: navigates to test gateway basic info, deactivates (停用), deletes (删除), confirms deletion, verifies gateway removed from home page. Reads TEST_GATEWAY_ID from .env file. Cleans up .env file.
- [x] T032 [US2] Create the SKILL definition file at .agents/skills/bdd-test-gen/SKILL.md following the contract in contracts/skill-interface.md. The SKILL must define: (1) argument parsing for --url, --user, --password, --cookie, --case, --all; (2) authentication workflow using Playwright MCP; (3) BDD case parsing workflow (read markdown, extract 功能/场景/假设/当/那么); (4) live page exploration workflow (navigate to 页面, walk through each 当 step using Playwright MCP, discover selectors); (5) script generation template (test.describe/test() structure per contracts/test-script-format.md); (6) verification workflow (run generated script, check pass/fail, iterate up to 3 times); (7) file saving convention (mirror bdd-cases/ path in bdd-scripts/). Include references to test/agent-tests/AGENTS.md for business context (module classification, execution order, domain gotchas).

**Checkpoint**: SKILL file exists, helpers/setup/teardown scripts ready. An agent can invoke the SKILL to generate scripts from BDD cases.

---

## Phase 5: User Story 3 - Deterministic Script Execution via Make Command (Priority: P3)

**Goal**: Create a Makefile target and Playwright configuration that runs all test scripts sequentially without agent involvement, producing a report and CI/CD-compatible exit code.

**Independent Test**: Run `make test-bdd URL=<url> USER=<user> PASSWORD=<pass>` and verify all scripts execute, report is generated, and exit code reflects pass/fail.

### Implementation for User Story 3

- [x] T033 [P] [US3] Create Playwright configuration in test/bdd-scripts/playwright.config.js: workers=1 (sequential), globalSetup='./setup.js', globalTeardown='./teardown.js', timeout=60000, globalTimeout=1800000, retries=0, reporters=[json+html], testDir='.', testMatch='**/*.spec.js'. Read TEST_URL, TEST_USER, TEST_PASSWORD, TEST_COOKIE from environment. Follow contracts/make-command.md.
- [x] T034 [P] [US3] Create Makefile at repository root with test-bdd target: validates URL parameter is provided, validates either USER+PASSWORD or COOKIE is provided, runs `cd test/bdd-scripts && npm ci --silent && npx playwright install chromium --with-deps && TEST_URL=$(URL) TEST_USER=$(USER) TEST_PASSWORD=$(PASSWORD) TEST_COOKIE=$(COOKIE) npx playwright test`. Follow contracts/make-command.md for parameter handling and error codes.
- [x] T035 [US3] Update test/bdd-scripts/.gitignore to exclude node_modules/, test-results/, playwright-report/, .env (test gateway state file)

**Checkpoint**: `make test-bdd URL=... USER=... PASSWORD=...` runs all scripts, produces report, exits with correct code. US3 complete.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation updates, AGENTS.md rewrite, final cleanup

- [x] T036 [P] Rewrite test/agent-tests/AGENTS.md: remove all old agent-test content, replace with post-refactor content only — module classification table (20 modules with Chinese names), recommended execution order, domain-specific gotchas that cannot fit in the SKILL (e.g., BkSelect dropdown behavior, login form variants, backend service configuration requirement, version generation prerequisites)
- [x] T037 [P] Update AGENTS.md at repository root: replace the agent-test skill entry in the skills table with the new bdd-test-gen skill entry, update the Agent Test Suite section to reference the new workflow (BDD cases → agent-generated scripts → make command)
- [x] T038 [P] Update CLAUDE.md at repository root: ensure Active Technologies and Recent Changes reflect the new BDD test refactor stack (Playwright Test, Node.js, Chinese BDD markdown)
- [x] T039 Validate quickstart.md in specs/002-bdd-test-refactor/quickstart.md: walk through each step to verify paths, commands, and directory structure match the actual implementation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS US1
- **User Story 1 (Phase 3)**: Depends on Foundational (T005, T006) - BLOCKS US2 (needs BDD cases to exist)
- **User Story 2 (Phase 4)**: Depends on US1 completion (BDD cases must exist for SKILL to reference)
- **User Story 3 (Phase 5)**: Depends on US2 (needs setup.js, teardown.js, helpers.js, playwright.config.js)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2). No other dependencies. This is the MVP.
- **User Story 2 (P2)**: Can start after US1 is complete (needs BDD cases as input). helpers.js, setup.js, teardown.js are independent of each other [P].
- **User Story 3 (P3)**: Can start after US2 shared scripts exist (setup.js, teardown.js, helpers.js). playwright.config.js and Makefile are independent [P].

### Within Each User Story

- US1: All module BDD generation tasks (T007-T026) are fully parallel [P]. Review (T027) and cleanup (T028) must follow.
- US2: helpers.js, setup.js, teardown.js are parallel [P]. SKILL definition (T032) should follow to reference them.
- US3: playwright.config.js and Makefile are parallel [P]. .gitignore follows.

### Parallel Opportunities

- **Phase 1**: T001-T004 can all run in parallel
- **Phase 3 (US1)**: All 20 module generation tasks (T007-T026) can run in parallel — they write to different directories
- **Phase 4 (US2)**: T029, T030, T031 can run in parallel — they write to different files
- **Phase 5 (US3)**: T033, T034 can run in parallel — different files
- **Phase 6**: T036, T037, T038 can run in parallel — different files

---

## Parallel Example: User Story 1

```bash
# Launch all 20 module generation tasks together (all write to different directories):
Task: "Generate BDD cases for 01-网关管理 in test/bdd-cases/01-网关管理/"
Task: "Generate BDD cases for 02-资源配置 in test/bdd-cases/02-资源配置/"
Task: "Generate BDD cases for 03-资源版本 in test/bdd-cases/03-资源版本/"
# ... (all 20 modules in parallel)

# After all complete:
Task: "Review all generated BDD cases"
Task: "Delete legacy artifacts"
```

## Parallel Example: User Story 2

```bash
# Launch shared infrastructure scripts together:
Task: "Create helpers.js in test/bdd-scripts/helpers.js"
Task: "Create setup.js in test/bdd-scripts/setup.js"
Task: "Create teardown.js in test/bdd-scripts/teardown.js"

# After all complete:
Task: "Create SKILL definition at .agents/skills/bdd-test-gen/SKILL.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (create directories, init node project)
2. Complete Phase 2: Foundational (parse Excel, produce consolidation plan)
3. Complete Phase 3: User Story 1 (generate ~100 BDD cases, clean up legacy)
4. **STOP and VALIDATE**: Review BDD cases — all modules covered, Chinese, correct format
5. Commit BDD cases to repository

### Incremental Delivery

1. Setup + Foundational → Directories and Excel analysis ready
2. User Story 1 → ~100 BDD cases committed, legacy cleaned → **MVP!**
3. User Story 2 → SKILL + shared scripts ready → agents can generate test scripts
4. User Story 3 → Makefile + config → `make test-bdd` works end-to-end
5. Polish → Documentation updated, AGENTS.md rewritten

### Parallel Team Strategy

With multiple developers/agents:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Agent A-T: Each handles 1-2 modules for BDD case generation (20 modules total)
3. After US1 complete:
   - Agent A: helpers.js + setup.js + teardown.js (US2 shared infra)
   - Agent B: SKILL definition (US2, after shared infra)
   - Agent C: Makefile + playwright.config.js (US3, after US2 shared infra)
4. All agents: Polish phase tasks in parallel

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All BDD cases MUST be written in Chinese following contracts/bdd-case-format.md
- The Excel file path is absolute — it references a local WeWork cache file
- Legacy cleanup (T028) should only happen after BDD cases are committed and verified
