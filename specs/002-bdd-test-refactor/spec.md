# Feature Specification: BDD Test Refactor

**Feature Branch**: `002-bdd-test-refactor`
**Created**: 2026-03-30
**Status**: Draft
**Input**: User description: "Refactor agent test suite from agent-driven execution to deterministic script-based execution. Convert 800 Excel cases to <100 optimized BDD cases, create a SKILL for agent-assisted script generation, and add make command for autonomous script execution."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Convert Excel Cases to Optimized BDD Cases (Priority: P1)

A QA engineer wants to transform the existing 800+ Excel test cases into a curated set of approximately 100 BDD-format test cases written entirely in Chinese, organized by functional module. The engineer runs a one-time conversion process that reads the Excel file, categorizes cases by module, merges redundant cases, and produces a set of concise BDD scenarios focused on core functionality. These BDD cases are committed to the code repository as the authoritative test specification. After successful migration, all legacy artifacts (intermediate markdown in `test/agent-tests/cases/` and supporting json/scripts in `test/agent-tests/`) are cleaned up.

**Why this priority**: This is the foundation — all downstream work (script generation, automated execution) depends on having a well-structured, optimized set of BDD cases in the repository.

**Independent Test**: Can be fully tested by running the conversion process on the Excel file and verifying that the output BDD cases are fewer than 100, cover all major functional modules, and follow BDD format (Given/When/Then).

**Acceptance Scenarios**:

1. **Given** the Excel file with 800+ test cases, **When** the conversion process runs, **Then** a set of BDD case files (fewer than 100) is generated in a designated directory within the repository.
2. **Given** the generated BDD cases, **When** reviewed by module, **Then** every major functional module from the original Excel (e.g., gateway management, resource configuration, environment management, permissions, plugins, logs, online debugging) has at least one representative BDD scenario.
3. **Given** the generated BDD cases, **When** compared to the original Excel cases, **Then** the BDD cases focus on each module's core workflow correctness (核心链路) rather than exhaustive coverage, with redundant and low-value cases merged or removed.
4. **Given** a generated BDD case file, **When** read by a QA engineer, **Then** it follows standard BDD format with Feature, Scenario, Given/When/Then steps, and is understandable without referencing the original Excel.

---

### User Story 2 - Agent-Assisted Script Generation from BDD Cases (Priority: P2)

A test engineer wants to convert BDD cases into executable test scripts. The engineer invokes a SKILL and provides a deployed environment's URL and authentication credentials (username+password or cookie). The agent then reads a BDD case file, uses Playwright MCP to open the environment in a browser, and actually walks through each BDD step on the live pages — navigating, clicking, filling forms, verifying outcomes — to discover real selectors, interaction patterns, and wait conditions. Based on this live exploration, the agent generates a self-contained executable test script. When BDD case files change, the engineer runs a sync script to regenerate or update the corresponding test scripts. The generated scripts are saved to a fixed directory and committed to the repository.

**Why this priority**: Scripts are the bridge between human-readable BDD cases and deterministic automated execution. Without them, you cannot achieve agent-free test runs.

**Independent Test**: Can be tested by selecting a single BDD case, invoking the SKILL, and verifying that the output script is syntactically valid, executable, and performs the steps described in the BDD case.

**Acceptance Scenarios**:

1. **Given** a BDD case describing a user journey, **When** the script generation SKILL is invoked, **Then** an agent reads the BDD steps, navigates the live application to discover correct UI elements, and produces an executable test script.
2. **Given** the agent is generating a script, **When** it encounters a form or interactive element, **Then** it uses browser tools to inspect the page and determine the correct selectors, labels, and interaction patterns.
3. **Given** a generated script, **When** saved to the designated directory, **Then** it is self-contained (includes all necessary navigation, authentication recovery, test actions, and assertions) and can run without agent involvement.
4. **Given** a generated script that fails during verification, **When** the agent detects the failure, **Then** it iterates on the script (adjusting selectors, waits, or steps) until the script passes or reports a genuine application issue.

---

### User Story 3 - Deterministic Script Execution via Make Command (Priority: P3)

A CI/CD pipeline operator or developer wants to run the complete test suite without any AI agent involvement. They execute a single `make` command, providing the target environment URL and authentication credentials (username+password or cookie), which sequentially runs all generated test scripts, collects pass/fail results, and produces a summary report. This execution is deterministic — the same scripts produce the same results regardless of model or token usage.

**Why this priority**: This delivers the core value proposition — stable, token-free, repeatable test execution that can integrate into CI/CD pipelines.

**Independent Test**: Can be tested by running the make command and verifying that all scripts execute in order, assertions are evaluated, and a summary report is generated.

**Acceptance Scenarios**:

1. **Given** all generated test scripts in the designated directory, **When** the make command is executed, **Then** every script runs sequentially in a defined order.
2. **Given** a script execution completes, **When** results are collected, **Then** each script's pass/fail status and any failure details are recorded.
3. **Given** all scripts have finished, **When** the make command completes, **Then** a summary report shows total/passed/failed counts, identifies which cases failed, and exits with a non-zero code if any test failed.
4. **Given** the test suite runs in a CI/CD environment, **When** executed, **Then** no AI agent, LLM API calls, or token consumption is required — execution is purely script-based.

---

### Edge Cases

- What happens when the Excel file contains cases with empty or malformed steps?
- How does the system handle cases that require test data setup? A shared setup script creates one test gateway before all tests; individual scripts reference it. A teardown script deletes it after all tests complete.
- What happens when a generated script's selectors become stale due to UI changes?
- How does the make command handle a script that hangs or times out?
- What happens when the live application is unavailable during script generation?
- How does the system handle authentication session expiry during script execution?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST read the specified Excel file (.xlsx format) and extract all test cases with their module, name, priority, preconditions, steps, and expected results.
- **FR-002**: System MUST categorize extracted cases by functional module (e.g., gateway management, resource configuration, environment management, permissions, plugins, logs).
- **FR-003**: System MUST merge redundant cases, combine related scenarios, and produce approximately 100 BDD cases focused on each module's core workflow correctness (核心链路), not exhaustive coverage of all original cases.
- **FR-004**: System MUST output BDD cases entirely in Chinese, in a standard format (Feature/Scenario/Given-When-Then) as markdown files organized by module in a designated repository directory. File naming and structure MUST support easy lookup, modification, and maintenance.
- **FR-005**: System MUST provide a SKILL definition file at `.agents/skills/<name>/SKILL.md` that guides an AI agent through the process of converting a BDD case into an executable test script.
- **FR-006**: The script generation SKILL MUST instruct the agent to: (1) request environment URL and authentication credentials (username+password or cookie) from the user, (2) read the target BDD case file, (3) use Playwright MCP to open the provided environment in a browser, (4) follow the BDD steps by actually navigating pages, clicking buttons, filling forms, and verifying results on the live application, and (5) based on the real interaction results (discovered selectors, navigation paths, wait conditions), generate the target executable test script.
- **FR-007**: Generated test scripts MUST be self-contained — each script handles its own navigation, authentication recovery, test actions, and assertions without requiring agent involvement at runtime.
- **FR-008**: Generated test scripts MUST be saved to a fixed, well-known directory within the repository.
- **FR-009**: System MUST provide a make command (or equivalent build target) that requires the user to provide environment URL, username+password or cookie as input parameters, then executes all test scripts sequentially in a defined order, preceded by a shared setup script (creates a test gateway and required preconditions) and followed by a shared teardown script (deletes the test gateway and cleans up test data).
- **FR-010**: The make command MUST collect results from each script and produce a summary report with total, passed, failed, and error counts.
- **FR-011**: The make command MUST exit with a non-zero status code if any test fails, enabling CI/CD integration.
- **FR-012**: Test scripts MUST handle session expiry by re-authenticating automatically during execution.
- **FR-013**: Test scripts MUST include configurable timeout handling — scripts that exceed a maximum execution time are terminated and marked as timed out.
- **FR-014**: The BDD-to-script conversion process MUST support incremental updates — when BDD case files change, the user runs a script to generate or update the corresponding test scripts without regenerating all scripts.
- **FR-015**: Upon successful migration to BDD cases, the system MUST clean up all legacy artifacts: the entire old `agent-test` SKILL (`.agents/skills/agent-test/`), `test/agent-tests/` directory contents (json, scripts, helpers, selector-cache, module-classification, convert_excel.py, classify_modules.py, etc.), and `test/agent-tests/cases/` intermediate markdown files. The `test/agent-tests/AGENTS.md` MUST be rewritten to contain only post-refactor content (business context that cannot fit in the new SKILL, such as module classification, execution order, and domain-specific notes).

### Key Entities

- **Excel Test Case**: A row in the source Excel file representing one test scenario with module, name, steps, and expected results.
- **BDD Case**: A curated, human-readable test scenario in Given/When/Then format, organized by functional module. Serves as the specification for script generation.
- **Test Script**: An executable file generated from a BDD case that performs browser-based functional testing without agent involvement. Contains navigation, interactions, and assertions.
- **Test Report**: A summary document produced after running all test scripts, showing pass/fail status and failure details.
- **SKILL Definition**: A configuration file that instructs an AI agent on how to convert BDD cases into executable test scripts using browser exploration.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Approximately 100 BDD cases cover all major functional modules present in the original 800+ Excel test suite (target ~100, flexibility allowed).
- **SC-002**: A full test suite run via the make command completes without any AI agent or LLM API involvement — zero token consumption during execution.
- **SC-003**: The same test suite run produces identical pass/fail results when executed multiple times against the same application state (deterministic execution).
- **SC-004**: A complete test suite run finishes within 30 minutes (compared to hours of agent-driven execution with 800 cases).
- **SC-005**: New BDD cases can be converted to executable scripts by an agent within 5 minutes per case using the provided SKILL.
- **SC-006**: The test suite integrates into a CI/CD pipeline — the make command's exit code correctly signals success (0) or failure (non-zero).
- **SC-007**: At least 90% of generated scripts pass on first execution against a healthy application instance without manual adjustment.

## Clarifications

### Session 2026-03-30

- Q: BDD case 文件语言? → A: 全部使用中文，文件易于查找、变更、维护。
- Q: BDD case 数量目标? → A: 大约 100 个左右 BDD case 覆盖原先核心 case，不是严格 "小于100"。
- Q: BDD case 变更后如何同步脚本? → A: 用户运行一个脚本即可生成或更新对应的 BDD test 脚本文件。
- Q: 脚本生成时 AGENT 如何获取环境信息? → A: AGENT 启动后主动要求用户提供环境信息（URL、认证等），然后自行探索页面生成脚本。
- Q: 旧 test/agent-tests/ 下的产物如何处理? → A: 原先 agent-test SKILL 生成的 json/脚本等确认不再需要后全部清理；原先 convert 后的 markdown（test/agent-tests/cases/）在 BDD case 入库后也全部清理。
- Q: 测试数据（test gateway）如何管理? → A: 共享 setup/teardown——运行前由 setup 脚本创建一个测试网关，所有脚本共用，运行结束后由 teardown 脚本删除。
- Q: make 命令如何获取环境信息? → A: 要求用户提供环境 URL / 用户名+密码 / 或 cookie，与现有 agent-test skill 的输入参数类似。
- Q: 原先 agent-test 相关信息如何处理? → A: 彻底清理，不再需要（包括旧 SKILL、旧脚本、旧配置）。
- Q: 新 SKILL 文件放在哪里? → A: `.agents/skills/xxxx/SKILL.md`，用于从 BDD case 调用 AGENT 生成对应的测试可执行脚本。
- Q: 800 转 BDD 的筛选重点? → A: 关注网关各个模块的核心链路的正确性，而不是覆盖所有 case。
- Q: test/agent-tests/AGENTS.md 如何处理? → A: 只保留重构后的相关内容（SKILL 中无法放入的业务说明，如模块划分、执行顺序等）。
- Q: 脚本生成的具体工作流? → A: 用户提供已部署环境的 URL + 用户名密码/cookie；AGENT 读取 BDD case 文件，通过 Playwright MCP 打开该环境页面，按照 BDD 步骤逻辑实际走完功能流程，基于真实交互结果生成目标可执行脚本。

## Assumptions

- The existing Excel file format matches the documented column structure (模块 | 用例名称 | 用例等级 | 前置条件 | 用例步骤 | 预期结果 | 实际结果 | 备注 | 用例版本).
- The existing `convert_excel.py` script and helpers library from the 001-agent-test-suite can be reused or adapted for the initial conversion.
- The live application (BlueKing API Gateway dashboard) is available during the script generation phase for agent-assisted exploration.
- Test scripts will use the same browser automation approach established in the current test suite.
- Authentication credentials will be provided at runtime via environment variables or command-line arguments — never hardcoded.
- The BDD case consolidation from 800 to <100 is a one-time operation; subsequent updates will be incremental.
- Timeout for individual test scripts defaults to 60 seconds unless otherwise specified.
- The make command execution environment has access to a browser runtime (e.g., headless browser with automation support installed).
