# BDD Test Suite

## Workflow and command roots

`cases/` contains Chinese acceptance cases; `scripts/` contains executable
Playwright specs; `runtime/` owns environment preparation, login, setup,
teardown, helpers, and runner configuration. Case/module counts change: inspect
the actual files instead of relying on a fixed inventory.

Generate scripts through the skill named in the repository-root guide, exploring
the target environment before choosing locators. Running existing scripts does
not require generation.

From the **repository root**:

```bash
make test-bdd-init
make test-bdd
```

Before execution, configure ignored `test-bdd/runtime/.test-env.json` with
`url` plus either `user`/`password` or `cookie`. The root Make target also accepts
`URL`, `USER`, `PASSWORD`, and `COOKIE` overrides; `runtime/prepare-env.js` accepts
`TEST_BDD_URL`, `TEST_BDD_USER`, `TEST_BDD_PASSWORD`, and `TEST_BDD_COOKIE` from the
environment. Reuse available test credentials without committing them.

For a focused spec, run from **`test-bdd/runtime`** after configuration and init:

```bash
npx playwright test --config=playwright.config.js ../scripts/<module>/<case>.spec.js
```

Use a real path from `scripts/`. The runner selects `*.spec.js`, uses one worker
with no retries, and invokes global setup/teardown even for focused selections.
It writes timestamped reports under `runtime/reports/`. A package-level bare
`npm test` does not explicitly select this runtime config; use the commands above.

## State and test boundaries

- `runtime/setup.js` creates a test gateway, backend/resource/version state and
  authenticated storage; teardown attempts to deactivate/delete that gateway.
  Confirm cleanup from the result, since teardown catches errors. Do not point
  destructive cases at an unrelated existing gateway.
- Reuse `runtime/helpers.js` for login, state, API-assisted fixtures and cleanup.
  Specs using `runtime/bdd-test.js` also enforce the shared hard-failure guard.
- Cases sharing the gateway run sequentially. Keep setup prerequisites explicit:
  configure a suitable backend, create resources, create a version, then publish
  when the case needs released state. Put gateway deactivation/deletion last.
- Classify the **actions** in a case: permission grant/revoke, marketplace
  applications, online debugging and publish operations can mutate state even
  on pages that also provide read-only views.

## Navigation and UI checks

Routes are defined in `src/dashboard-front/src/router/index.ts` and each view's
route module (paths below are relative to the site base, with `:id` a gateway ID):

| Area | Current route |
| --- | --- |
| Resource editing / versions | `/:id/resource/setting`, `/:id/resource/version` |
| Environment overview / release history | `/:id/stage/overview`, `/:id/stage/release-record` |
| Backends | `/:id/backend` |
| Permission applications / grants | `/:id/permission/apply`, `/:id/permission/app` |
| Access logs / statistics | `/:id/log`, `/:id/dashboard`, `/:id/report` |
| Debug / basic information / audit | `/:id/online-debugging`, `/:id/basic-info`, `/:id/audit` |
| MCP servers / approvals | `/:id/mcp/server`, `/:id/mcp/permission` |
| Component categories / runtime data | `/components/category`, `/components/runtime-data` |
| API docs / platform tools / MCP market | `/docs/api-docs`, `/platform-tools`, `/mcp-market` |

Environment resources/plugins/variables and debugging history may be tabs or
panels; do not invent standalone URLs from case names. UI controls depend on
edition, feature flags, role, and deployed version. Confirm login selectors,
name constraints, dropdown dismissal and publish steps in the live page/helpers
instead of treating old observations as universal rules.
