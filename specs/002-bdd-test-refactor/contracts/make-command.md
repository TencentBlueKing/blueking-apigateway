# Contract: Make Command Interface

**Version**: 1.0
**Date**: 2026-03-30

## Command

```bash
# With username + password
make test-bdd URL=https://example.com USER=admin PASSWORD=secret

# With cookie
make test-bdd URL=https://example.com COOKIE="session_id=abc123"
```

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `URL` | Yes | Target environment base URL |
| `USER` | Yes* | Username for authentication |
| `PASSWORD` | Yes* | Password for authentication |
| `COOKIE` | Yes* | Cookie string (alternative to user/password) |

*Either `USER` + `PASSWORD` or `COOKIE` must be provided.

## Behavior

1. Validates required parameters (URL + auth method)
2. Installs dependencies if needed (`npm ci` in `test/bdd-scripts/`)
3. Runs `npx playwright test --config=playwright.config.js`
4. Playwright Test runner executes:
   - `globalSetup` (setup.js): creates test gateway
   - All `.spec.js` files sequentially (workers: 1)
   - `globalTeardown` (teardown.js): deletes test gateway
5. Generates report in `test/bdd-scripts/test-results/`

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All tests passed |
| 1 | One or more tests failed |
| 2 | Configuration error (missing params, browser not installed) |

## Output

- Console: real-time test progress
- `test/bdd-scripts/test-results/results.json`: machine-readable JSON report
- `test/bdd-scripts/playwright-report/index.html`: human-readable HTML report
- `test/bdd-scripts/test-results/*.png`: failure screenshots
