# Contract: Test Case Markdown Format

**Version**: 1.0
**Date**: 2026-03-24

## Purpose

Defines the standard markdown format for test case files that the agent test runner reads and executes. All test cases (manual and auto-generated) MUST follow this format.

## Format Specification

```markdown
# Case: [Case Title]

**Page**: [relative URL path, e.g., / or /gateways/123/resources]
**Prerequisites**: [comma-separated list of conditions, e.g., "Logged in, Gateway 'test-gw' exists"]

## Steps

1. [Action description in natural language]
2. [Action description in natural language]
3. [Action description in natural language]

## Verify

- [Expected outcome 1]
- [Expected outcome 2]
- [Expected outcome 3]
```

## Field Definitions

| Field | Required | Description |
|-------|----------|-------------|
| Case Title | Yes | Short descriptive name for the test scenario |
| Page | Yes | The URL path to navigate to (relative to base URL) |
| Prerequisites | No | Conditions that must be true before running this case. Omit if none. |
| Steps | Yes | Ordered list of user interactions to perform. Natural language. |
| Verify | Yes | Unordered list of expected outcomes to check after steps complete. |

## Step Action Patterns

Steps should use these natural-language patterns for clarity:

| Pattern | Example |
|---------|---------|
| Navigate | "Navigate to the gateway list page" |
| Click | "Click the 'Create Gateway' button" |
| Type | "Type 'test' in the keyword search input" |
| Type + Submit | "Type 'test' in the keyword search input and press Enter" |
| Select | "Select '可编程网关' from the type filter dropdown" |
| Wait | "Wait for the gateway list to load" |
| Scroll | "Scroll down to the bottom of the page" |

## Verification Patterns

Verifications should describe observable outcomes:

| Pattern | Example |
|---------|---------|
| Content visible | "The page displays 'No gateways found'" |
| Element state | "The type filter dropdown shows '可编程网关' as selected" |
| List content | "The gateway list shows only programmable gateways" |
| Count | "The gateway list shows at least 1 result" |
| Navigation | "The browser URL changes to /gateways/123" |
| Absence | "No error message is displayed" |

## File Naming Convention

```
case[N]-[short-description].md
```

Examples:
- `case0-login.md`
- `case1-gateway-list-filters.md`
- `case2-create-gateway.md`

Cases are executed in filename alphabetical order (i.e., case0 before case1 before case2).
