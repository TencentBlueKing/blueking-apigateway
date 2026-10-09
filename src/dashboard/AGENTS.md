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

For focused Django tests, replace the final target in this wrapper:

```bash
uv run bash -lc 'cd apigateway && set -a && . apigateway/conf/unittest_env && set +a && python -m pytest --nomigrations --ds apigateway.settings -q --tb=short apigateway/tests/path/to/test_file.py::TestClass::test_method'
```

The test environment and Django settings are required. `--nomigrations` avoids
migration setup for focused tests. Test-fixture contracts are in
`apigateway/apigateway/tests/AGENTS.md`.

Code changes need affected tests and the EE lint gate. Broad/shared changes also
need the full gate, which uses migrations and parallel workers:

```bash
uv run make edition-ee
uv run make test
```

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
