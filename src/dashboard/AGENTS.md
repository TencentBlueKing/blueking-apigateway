# AGENTS.md

This file provides guidance for coding agents and automation tools when working with code in this repository.

## Project Overview

BlueKing API Gateway Dashboard — the Django-based control plane for managing API gateways. The data plane uses Apache APISIX. This is the `dashboard` component in a monorepo (siblings: `dashboard-front`, `core-api`, `mcp-proxy`, `esb`).

- Python >=3.11,<3.12, Django 4.2, DRF 3.16
- Dependency management: `uv` (lockfile: `uv.lock`, config: `pyproject.toml`)
- The Django project root is `apigateway/` (contains `manage.py`); the Python package is `apigateway/apigateway/`

## Architecture (import-linter enforced layers)

```
apis → biz → controller → service → components → apps → core → common → utils
```

Upper layers may import lower layers only. Violations break `make lint-check`.

### Layer responsibilities

| Layer | Purpose |
|---|---|
| `apis/` | DRF views — three independent API surfaces: `web` (UI), `open` (v1 OpenAPI), `v2` (inner/sync/open) |
| `biz/` | Business logic orchestration (handlers, not models) |
| `controller/` | Release pipeline — converts domain objects into APISIX config via convertor/transformer/distributor |
| `service/` | Shared services (ES, Prometheus, SDK generation, alert flows) |
| `components/` | HTTP clients to external BlueKing systems (bkauth, bkpaas, bkmonitor, etc.) |
| `apps/` | Django apps with models, admin, management commands (gateway, plugin, permission, esb, mcp_server, etc.) |
| `core/` | Central domain models: Gateway, Stage, Resource, ResourceVersion, Release, Backend, Context |
| `common/` | Shared utilities, mixins, permissions, error codes, middleware, encryption |
| `utils/` | Pure utility functions |

The three API modules (`apis.open`, `apis.web`, `apis.v2.*`) are enforced as independent — they cannot import from each other.

### Domain model chain

```
Gateway → Stage → Resource → ResourceVersion → Release → ReleaseHistory
```

Plugins bind at stage/resource scope via `PluginBinding`. Auth settings live in `Context` records. Backends (upstream configs) are per-gateway with stage-specific `BackendConfig`.


## Command Execution Guide

This section contains critical command execution instructions that apply across all development.


### Python Command Execution Requirements

CRITICAL: When running Python commands (pytest, mypy, pre-commit, etc.), you MUST use the virtual environment.

```
# Activate the virtualenv (required before running make targets / dev tools)
source .venv/bin/activate
```

### Setup

```
# Bootstrap local dev env (installs uv, pre-commit, mypy types)
make init

# Install dependencies
uv sync

# Regenerate uv.lock after changing pyproject.toml
make uv.lock
```

### Linting

All configured in `pyproject.toml`:
- **ruff** — formatter + linter (line-length 119)
- **mypy** — strict optional, excludes `editions/` and migrations
- **import-linter** (via `lint-imports`) — enforces layered architecture contracts (run from `apigateway/` dir)

`make lint` runs: ruff format → ruff check → mypy → lint-imports.

```
# Lint (auto-fix + type check + import layer check)
make lint

# Lint (check only, no auto-fix — used in CI)
make lint-check
```

### Testing

```bash
# Run all tests (uses SQLite, parallel via pytest-xdist)
make test

# Run a single test file or test
cd apigateway && export PYTHONDONTWRITEBYTECODE=1 && . apigateway/conf/unittest_env && \
  pytest --ds apigateway.settings --reuse-db -n auto --dist loadscope \
  apigateway/apigateway/tests/path/to/test_file.py::TestClass::test_method -v

# Re-run only last-failed tests
make test-lf

# Debug with pdb (single-process, stops on first failure)
make test-pdb

# Run tests with coverage
make test-cov
```

## Settings

Settings are loaded dynamically: `apigateway.conf.settings_{BKPAAS_ENVIRONMENT}` (defaults to `dev`). Base config is in `apigateway/conf/default.py`. Local dev config goes in `apigateway/apigateway/conf/.env` (copy from `.env.tpl`).

Tests source `apigateway/conf/unittest_env` which uses SQLite. Alternate env files exist for MySQL and multi-tenant testing.

## Testing Patterns

- Tests mirror source structure under `apigateway/apigateway/tests/`
- Use `ddf` (django-dynamic-fixture) `G()` to create model instances
- Key fixtures in `apigateway/apigateway/tests/conftest.py`: `fake_gateway`, `fake_stage`, `fake_backend`, `fake_resource`, `fake_admin_user`, `request_factory`
- Test settings: `--ds apigateway.settings`, `--reuse-db` for speed, `-n auto --dist loadscope` for parallel
- Tests use two databases: `default` (apigateway) and `bkcore` (ESB)

## Edition System (EE/TE)

The project supports multiple editions (Enterprise/Tencent) via `editionctl`. Edition-specific code lives under `apigateway/apigateway/editions/{ee,te}/` and is symlinked into the main package tree.

```bash
make edition          # show current
make edition-te       # switch to TE
make edition-ee       # switch to EE
make edition-develop  # develop mode
make edition-reset    # clear edition symlinks
make edition-modules  # create __init__.pyi files for mypy compatibility
```

## Naming Convention: Gateway vs API

Legacy code uses `API`/`api`/`api_id` to refer to gateways. All new code must use `Gateway`. The `api` naming persists in:
- DB columns and ORM foreign keys (`api=`, `api_id=`)
- Some frontend request/response payloads
