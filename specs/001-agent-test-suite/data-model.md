# Data Model: Agent Test Suite

**Date**: 2026-03-24
**Branch**: `001-agent-test-suite`

## Entities

### Test Case (Markdown File)

A single test scenario stored as a `.md` file in the cases directory.

**Attributes**:
- **File name**: Identifies the case (e.g., `case0-login.md`, `case1-gateway-list.md`)
- **Title**: Human-readable name of the test scenario
- **Page URL**: The target page to test (relative or absolute)
- **Prerequisites**: Any conditions that must be met before this case runs (e.g., "must be logged in", "gateway X must exist")
- **Steps**: Ordered list of interactions to perform
- **Verifications**: Expected outcomes to check after each step or at the end

**Relationships**:
- Belongs to a **Cases Directory**
- Produces **Test Step Results** during a run
- References a **Page Under Test**

### Test Step

An individual action + verification within a test case.

**Attributes**:
- **Action type**: navigate, click, type, select, wait, screenshot
- **Target**: Description of the UI element to interact with (natural language, e.g., "the type filter dropdown")
- **Value**: Input value if applicable (e.g., text to type, option to select)
- **Expected outcome**: What should be true after the action (e.g., "list filters to show only programmable gateways")

### Test Run

A single execution session encompassing one or more test cases.

**Attributes**:
- **Run ID**: Timestamp-based identifier (e.g., `2026-03-24T14-30-00`)
- **Target URL**: The base URL of the environment being tested
- **Auth method**: "credentials" or "cookie"
- **Start time**: When the run began
- **End time**: When the run completed
- **Status**: running, completed, aborted

**Relationships**:
- Contains multiple **Test Case Results**
- Produces one **Test Report**

### Test Case Result

The outcome of executing a single test case within a run.

**Attributes**:
- **Case reference**: Which test case file was executed
- **Status**: passed, failed, skipped, error
- **Duration**: How long the case took to execute
- **Steps completed**: Number of steps executed before completion or failure
- **Failure reason**: Description of what went wrong (if failed)
- **Screenshots**: List of screenshot file paths captured during execution

### Test Report

The final output of a test run.

**Attributes**:
- **Run ID**: Links to the test run
- **Summary**: Total cases, passed, failed, skipped, error counts
- **Overall duration**: Total execution time
- **Case results**: Ordered list of test case results
- **Generated at**: Timestamp of report generation

## State Transitions

### Test Case Execution

```
pending → running → passed
                  → failed
                  → error (unexpected exception)
                  → skipped (prerequisites not met)
```

### Test Run

```
initializing → authenticating → running → completed
                              → aborted (auth failure, site unreachable)
```
