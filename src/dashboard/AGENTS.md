# Dashboard Guide

Django control plane. Commands below run from `src/dashboard`; paths are
relative to it unless marked repository-root. Runtime and dependency versions
come from `pyproject.toml` and `uv.lock`. `apigateway/` is the Django project
root; `apigateway/apigateway/` is the importable package.

## Runtime and commands

Use `uv run` for Python-backed commands. Initialize the locked environment with
`uv sync --locked --all-extras --dev`; optional `make init` also installs developer
tools and Git hooks. After dependency changes, use `make uv.lock` and
`uv lock --check`. Verify the Python version with `uv run python --version`.

`BKPAAS_ENVIRONMENT` selects `apigateway.conf.settings_<environment>` and
defaults to `dev`; `ENABLE_MULTI_TENANT_MODE` controls tenancy. Local settings
start from `apigateway/apigateway/conf/.env.tpl`.

Edition code lives in `apigateway/apigateway/editions/`. CI activates EE before
lint and tests; use other edition/reset targets only when the task requires them.

```bash
uv run make edition-ee
uv run make lint-check
```

`lint-check` runs Ruff checks, mypy, import-linter, and API consistency checks.
It does not check Ruff formatting; use `uv run ruff format --check` on affected
Python paths when formatting evidence is needed. `uv run make lint` formats and
auto-fixes files, so use it only when those changes are intended.

## Test selection

See [TESTING.md](TESTING.md) for test modes, selectors and database behavior.
For a focused ordinary test, run without parallel worker startup:

```bash
uv run make test-fast TEST_WORKERS=0 TEST_PATHS=apigateway/tests/path/to/test_file.py::TestClass::test_method
```

Code changes need tests for affected behavior and the EE lint gate. For local
changes, expand from focused tests to the affected module/callers as needed;
do not automatically run the full suite at every task or delivery phase.
`test-fast` disables migrations and excludes tests marked `migration`; it is
feedback coverage, not the full gate. For migration changes, run
`uv run make test-migrations` and the affected ordinary tests.

Broad/shared changes (including test configuration and shared fixtures) also
need the full gate below. CI uses the same entrypoint, enables migrations, and
includes migration tests. Do not substitute `test-fast` or `test-lf` for it:

```bash
uv run make edition-ee
uv run make test
```

Test-fixture contracts are in `apigateway/apigateway/tests/AGENTS.md`. Reuse
passing verification when the relevant diff, inputs, runtime, command and scope
are unchanged; committing or opening the PR does not invalidate that evidence.

## Architecture and source map

`pyproject.toml` defines import contracts and their explicit exceptions:

```text
apis -> biz -> controller -> service -> components -> apps -> core -> common -> utils
```

| Layer | Ownership |
| --- | --- |
| `apis/` | HTTP validation, DTOs, request and response shaping; independent API surfaces. |
| `biz/` | Use-case decisions, transactions, audit and side-effect sequencing. |
| `controller/` | Release input, APISIX compilation, distribution and publisher tasks. |
| `service/` | Focused reusable queries, relation operations, snapshots and cleanup. |
| `components/` | External BlueKing clients. |
| `apps/` | App models, migrations, admin, commands and Celery entrypoints. |
| `core/` | Central models, single-model managers and normalized configuration. |
| `common/`, `utils/` | Middleware, permissions, fields, tenancy and low-level utilities. |

Place API shaping in its surface, workflows in their owning business domain,
and reusable leaf operations in `service/`. Multi-model business queries do not
belong in model managers. Read the guide in the layer/module being changed.

Useful paths:

- `apigateway/apigateway/urls.py`: top-level routing.
- `apigateway/apigateway/conf/`: runtime settings and test environment.
- `apigateway/apigateway/tests/`: tests mirroring source ownership.
- `apigateway/apigateway/data/apigw-definitions/` and `data/apidocs/zh/`:
  gateway resource YAML and OpenAPI Markdown.
- `scripts/check_api_consistency.py`, `scripts/config.yaml`: API contract checks.

## Credential handling

Responses, logs, exceptions, audit events and publish history must not expose
plaintext secrets or encrypted credential payloads. Check the owning serializer,
tenant/permission boundary and downstream handler when assessing a security
report. Do not bypass model encryption or display masking in a new entrypoint.
