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

## 002/003-restrict-gateway-not-exist

Only the existing `GatewaySyncApi` classes in these two files may explicitly
enable `allow_gateway_not_exist`:

- `apigateway/apigateway/apis/open/gateway/views.py`
- `apigateway/apigateway/apis/v2/sync/views.py`

`002-restrict-gateway-not-exist-files` rejects enabling the flag elsewhere in
production code, including edition source trees. Tests and migrations are excluded.
`003-restrict-gateway-not-exist-class` checks the two approved files and rejects
enabling it outside the `GatewaySyncApi` class body. Other views in those files
are not exempt. Paths beginning with `/src/dashboard/` are anchored to the Git
repository root, including when Make runs from `src/dashboard`.

The rules share patterns for explicit `True` in declarations (including annotated
assignments), attribute writes, `setattr`, and `as_view` arguments. Setting `False`
and reading the flag are allowed. This is a syntax-level check of the listed
forms and lexical class scope; it does not prove effective permissions after
inheritance, nested definitions, or routing, nor detect arbitrary truthy expressions,
dynamic attribute names, dictionary expansion, or indirect helper calls.

## Regression tests

The tests run real Semgrep scans on temporary Git source trees, covering forbidden
references, valid responses, directory and class boundaries, edition paths, exact
rule IDs, and failure exit codes. They require Git but no Django/database setup.
