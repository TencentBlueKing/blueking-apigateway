# Feature Specification: Agent Test Suite for Browser-Based Regression Testing

**Feature Branch**: `001-agent-test-suite`
**Created**: 2026-03-24
**Status**: Draft
**Input**: User description: "Build an agent-driven automated test suite that uses a browser to run regression tests against the BlueKing API Gateway dashboard, replacing the current 2-week manual regression cycle."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run Existing Regression Test Cases (Priority: P1)

A QA tester or developer wants to run all existing test cases against the dashboard to verify nothing is broken. They provide the site URL, login credentials, and a directory of test case files (written in markdown). The system opens a browser, logs in, executes each test case sequentially, and produces a pass/fail report.

**Why this priority**: This is the core value proposition — replacing a 2-week manual regression cycle with an automated run that completes in hours. Without this, the feature has no purpose.

**Independent Test**: Can be fully tested by creating a small set of markdown test cases (e.g., login + gateway list page filters) and running them against the dev environment. Delivers immediate value by automating repetitive testing.

**Acceptance Scenarios**:

1. **Given** a directory containing markdown test case files and valid login credentials, **When** the tester triggers a test run, **Then** the system opens a browser, authenticates, and executes each test case in order.
2. **Given** a test run is in progress, **When** a test case passes all its verification steps, **Then** it is marked as "passed" in the report with evidence (e.g., screenshots).
3. **Given** a test run is in progress, **When** a test case fails a verification step, **Then** it is marked as "failed" in the report with a description of what went wrong and a screenshot of the failure state.
4. **Given** all test cases have been executed, **When** the run completes, **Then** a summary report is generated showing total cases, passed, failed, and execution time.

---

### User Story 2 - Auto-Generate Test Cases for New or Changed Pages (Priority: P2)

A developer has added a new page or modified an existing page in the dashboard. They want the system to explore the new/changed page, understand its UI elements and interactions by reading the frontend source code, and automatically generate markdown test case files into the cases directory.

**Why this priority**: This extends the core automation by keeping test coverage up to date as the product evolves. Without auto-generation, maintaining the test suite becomes a manual burden that defeats the purpose of automation.

**Independent Test**: Can be tested by pointing the system at a known page (e.g., the gateway list page at the root URL) and verifying it produces reasonable test case markdown files that cover the page's interactive elements.

**Acceptance Scenarios**:

1. **Given** a URL for a new/changed page and access to the frontend source code (`src/dashboard-front`), **When** the developer triggers case generation, **Then** the system explores the page in a browser and reads the relevant source code to understand the UI.
2. **Given** the system has explored a page, **When** it identifies interactive elements (dropdowns, inputs, buttons, tables), **Then** it generates markdown test case files covering those interactions.
3. **Given** generated test case files, **When** a developer reviews them, **Then** each file follows the standard test case markdown format and is immediately runnable by the test execution system (User Story 1).

---

### User Story 3 - Login and Session Management (Priority: P1)

The system needs to authenticate with the dashboard before running any test cases. It must handle the login flow (redirect to login page, enter credentials, cookie-based session) or accept a pre-existing cookie for environments where automated login is restricted.

**Why this priority**: Authentication is a prerequisite for every other test case. If the system cannot log in, nothing else works.

**Independent Test**: Can be tested by attempting to log in to the dev environment and verifying the session is established (page shows logged-in state after redirect back to dashboard).

**Acceptance Scenarios**:

1. **Given** valid credentials (username/password), **When** the system navigates to the dashboard URL, **Then** it follows the redirect to the login page, enters credentials, and is redirected back to the dashboard in a logged-in state.
2. **Given** a pre-provided session cookie, **When** the system starts a browser session, **Then** it injects the cookie and navigates directly to the dashboard without going through the login flow.
3. **Given** invalid credentials, **When** the system attempts to log in, **Then** it reports an authentication failure clearly and does not proceed with test execution.
4. **Given** a session expires mid-run, **When** the system detects an authentication error during test execution, **Then** it attempts to re-authenticate and resume the test run.

---

### User Story 4 - Build as a Reusable Skill (Priority: P3)

The test suite should be packaged as a reusable skill (or equivalent reusable command) so that any team member can invoke it with a simple command, passing the URL, credentials, and cases directory as inputs. This makes it easy to integrate into CI pipelines or ad-hoc testing workflows.

**Why this priority**: Packaging as a skill improves usability and adoption, but the core functionality (Stories 1-3) must work first. This is an enhancement that makes the tool easier to distribute and invoke.

**Independent Test**: Can be tested by invoking the skill command with parameters and verifying it triggers the full test execution workflow.

**Acceptance Scenarios**:

1. **Given** the skill is installed, **When** a user invokes it with URL, credentials, and cases directory, **Then** the full test execution pipeline runs and produces a report.
2. **Given** the skill is invoked without required parameters, **When** the system detects missing inputs, **Then** it prompts the user for the missing information with clear descriptions of what is needed.

---

### Edge Cases

- What happens when a test case references a UI element that no longer exists on the page (e.g., after a UI redesign)?
- How does the system handle pages that require data setup (e.g., a gateway must exist before testing the gateway detail page)?
- What happens when the target site is unreachable or returns errors (500, 503)?
- How does the system handle slow-loading pages or elements that appear asynchronously?
- What happens when two test cases conflict (e.g., one creates data that another expects not to exist)?
- How does the system handle browser pop-ups, confirmation dialogs, or toast notifications?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a site URL, login credentials (username/password or cookie), and a test cases directory as inputs to begin a test run.
- **FR-002**: System MUST authenticate with the target site via browser-based login (form submission with redirect) or via pre-injected session cookie.
- **FR-003**: System MUST discover and load all markdown test case files from the specified cases directory.
- **FR-004**: System MUST execute each test case by controlling a real browser — navigating to pages, interacting with UI elements (click, type, select from dropdowns), and verifying expected outcomes.
- **FR-005**: System MUST capture a screenshot at each verification step (both pass and fail) as evidence.
- **FR-006**: System MUST generate a structured test report after each run, including: total cases, passed count, failed count, execution duration per case, overall duration, and links to screenshots.
- **FR-007**: System MUST handle common UI interaction patterns: dropdown selection, text input with form submission (Enter key), link clicking, table content verification, page navigation, and waiting for asynchronous content to load.
- **FR-008**: System MUST support test case generation by exploring a given page URL and reading the corresponding frontend source code (Vue components in `src/dashboard-front`) to identify testable interactions.
- **FR-009**: Generated test cases MUST follow the same markdown format as manually written cases so they are immediately executable.
- **FR-010**: System MUST continue executing remaining test cases when one case fails (no fail-fast by default), collecting all results for the final report.
- **FR-011**: System MUST support re-authentication if the session expires during a test run.
- **FR-012**: System MUST provide clear, actionable error messages when a test case fails, including what was expected vs. what was observed.

### Key Entities

- **Test Case**: A markdown file describing a single test scenario — includes the target page URL, steps to perform (interactions), and expected outcomes (verifications). Organized in a directory structure.
- **Test Run**: A single execution of all (or selected) test cases against a target environment. Produces a test report.
- **Test Report**: The output of a test run — structured summary with pass/fail status per case, screenshots, timing, and an overall summary.
- **Test Step**: An individual action within a test case (e.g., "select 'All' from the type dropdown") paired with an expected outcome (e.g., "gateway list shows all types").
- **Page Under Test**: A specific URL/page in the dashboard that is the target of one or more test cases.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Regression testing cycle time reduces from 2 weeks of manual testing to under 4 hours of automated execution for the same scope of test cases.
- **SC-002**: 100% of manually written test cases in the cases directory execute without requiring human intervention (excluding initial credential input).
- **SC-003**: Test reports accurately reflect the state of the application — zero false positives (reporting pass when the feature is actually broken) in 95% of runs.
- **SC-004**: Auto-generated test cases for a new page cover at least 80% of the interactive elements visible on that page.
- **SC-005**: A new team member can set up and run the test suite within 15 minutes using only the provided documentation and skill command.
- **SC-006**: Each individual test case completes execution in under 60 seconds (excluding page load time for slow environments).

## Assumptions

- The target dashboard is a standard web application accessible via a modern browser (Chromium-based).
- The login flow uses a redirect-based pattern with cookie-based session management (as described for the dev environment).
- The frontend source code in `src/dashboard-front` uses Vue.js and follows standard component patterns that can be parsed to understand page structure.
- The backend source code in `src/dashboard` (Django) can be referenced for understanding data models and API endpoints when generating test cases.
- Test cases are written in markdown following a consistent format that describes steps and expected outcomes in a structured way.
- The dev environment (`{{BASE_URL}}` configured in `test/agent-tests/config.md`) is available for initial development and testing of the suite.
- Screenshots and reports are stored locally on the machine running the tests.
- The test suite runs locally (not in CI) for the initial version, with CI integration as a future enhancement.

## Scope Boundaries

### In Scope
- Browser-based UI testing of the BlueKing API Gateway dashboard
- Login/authentication handling (credentials or cookie-based)
- Executing test cases defined in markdown files
- Generating test reports with pass/fail results and screenshots
- Auto-generating test cases for new/changed pages by exploring UI and reading source code
- Starting with simple cases: login (case0) and gateway list page filters/sorting (case1)

### Out of Scope
- API-level testing (already covered by existing Bruno test collections in `/test/cases/`)
- Load testing or performance testing
- Testing of non-dashboard components (core-api, ESB, operator)
- Mobile browser testing
- Cross-browser testing (initial version targets Chromium only)
- CI/CD pipeline integration (future enhancement)
- Database setup or test data management (tests run against existing environment data)
