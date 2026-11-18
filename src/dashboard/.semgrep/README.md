# Dashboard Semgrep rules

Run from `src/dashboard`:

```bash
make lint-semgrep
make test-semgrep
```

Make pins Semgrep in an isolated `uv tool run` environment. The first run downloads
the tool; it does not add packages to the Dashboard runtime or change `uv.lock`.
Rules are local, metrics and version checks are disabled, and no account is needed.

`lint` / `lint-check`, the `dashboard-semgrep` pre-commit hook, and Dashboard CI
run the scan. CI also runs the regression tests. Findings return exit code 1;
invalid rules and parsing errors fail the scan. Rule IDs are not rewritten.
Inline `nosemgrep` comments do not suppress these project rules.

## 001-no-legacy-response

Modern `apis/web` and `apis/v2` code must not use
`apigateway.utils.responses.V1OKJsonResponse` or `V1FailJsonResponse`.
Use `OKJsonResponse` / `FailJsonResponse`, or the surface's standard DRF response.

The scan targets `apigateway/apigateway`. Each rule's `paths` controls its own
scope, including edition source trees. Legacy `apis/open`, the response-class
definitions, tests, and historical migrations are outside this rule's scope.
No per-file ignore markers or historical baseline are needed.

The rule matches references to the fully qualified classes, including supported
import aliases, calls, callbacks, and subclass bases. It does not execute Python
or guarantee detection through dynamic imports or arbitrary cross-module wrappers.
It does not validate response payloads or HTTP 204 behavior.

The tests run real Semgrep scans on temporary source trees, covering forbidden
references, valid responses, directory boundaries, edition paths, the exact rule
ID, and failure exit codes. They require no Django/database setup.
