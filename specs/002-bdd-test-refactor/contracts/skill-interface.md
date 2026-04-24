# Contract: SKILL Definition Interface

**Version**: 1.0
**Date**: 2026-03-30

## SKILL Location

```
.agents/skills/bdd-test-gen/SKILL.md
```

## Invocation

```
bdd-test-gen generate --url <URL> --user <USER> --password <PASSWORD> [--case <BDD_FILE>] [--all]
bdd-test-gen generate --url <URL> --cookie <COOKIE> [--case <BDD_FILE>] [--all]
```

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--url` | Yes | Deployed environment URL |
| `--user` | Yes* | Username for authentication |
| `--password` | Yes* | Password for authentication |
| `--cookie` | Yes* | Cookie (alternative to user/password) |
| `--case` | No | Path to a specific BDD case file to convert |
| `--all` | No | Convert all BDD cases in `test/bdd-cases/` |

*Either `--user` + `--password` or `--cookie` required.

## Agent Workflow

1. **Authenticate**: Log into the environment using provided credentials
2. **Read BDD case**: Parse the target markdown file for 功能, 场景, steps
3. **Navigate**: Open the page specified in `**页面**` field
4. **Explore & Execute**: For each `## 场景`:
   - Walk through each 当/并且 step on the live page via Playwright MCP
   - Discover real selectors, button labels, form fields
   - Record wait conditions and navigation patterns
   - Verify 那么 assertions match live behavior
5. **Generate script**: Create `.spec.js` file following the test-script-format contract
6. **Verify**: Run the generated script to confirm it passes
7. **Iterate**: If script fails, adjust selectors/waits and re-verify (max 3 attempts)
8. **Save**: Write to `test/bdd-scripts/<matching-path>.spec.js`

## Output

- Generated `.spec.js` file(s) in `test/bdd-scripts/`
- Console log of generation progress and verification results
