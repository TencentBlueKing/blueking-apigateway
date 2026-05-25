# AGENTS.md

Guidance for coding agents working in `src/dashboard`. Treat this file as the
local contract for dashboard changes; the repository-root AGENTS.md still
applies.

## Scope

- Work from `src/dashboard` unless a command says otherwise.
- Do not touch sibling projects (`src/dashboard-front`, `src/core-api`,
  `src/mcp-proxy`, `src/esb`) for dashboard-only requests.
- Before changing code, read the target file, its immediate caller or URL route,
  the serializer/form it depends on, and the nearest tests.
- Keep changes surgical. Do not reformat or refactor adjacent code unless the
  requested change requires it.
- This subproject is Python-only. Frontend code lives in `src/dashboard-front`.

## Project Overview

BlueKing API Gateway Dashboard is the Django control plane for managing gateway
definitions, stages, resources, releases, permissions, plugins, SDK generation,
MCP servers, and data-plane publication. Apache APISIX is the data plane; this
service stores and validates gateway state, then turns releases into controller
configuration.

Current stack, from the checked-in files:

- Python `>=3.11,<3.12` in `pyproject.toml`; CI uses Python `3.11.13`.
- Django `4.2.30`, Django REST Framework `3.16.0`.
- Dependencies are managed by `uv` with `pyproject.toml` and `uv.lock`.
- The Django project root is `apigateway/` and contains `manage.py`.
- The importable Django package is `apigateway/apigateway/`.

## Important Paths

- `Makefile` - setup, lint, tests, edition switching, Docker image build, OpenAPI checks.
- `pyproject.toml` - dependencies, ruff, mypy, pytest, import-linter contracts.
- `uv.lock` - dependency lockfile; keep it in sync with `pyproject.toml`.
- `Dockerfile` - production image, based on a Python 3.11 BlueKing image.
- `bin/start.sh` - Gunicorn entrypoint; keeps Prometheus multiprocess metrics in `/tmp/`.
- `bin/start_celery.sh` and `bin/start_beat.sh` - Celery entrypoints.
- `apigateway/manage.py` - Django management command entrypoint.
- `apigateway/apigateway/urls.py` - top-level URL routing.
- `apigateway/apigateway/conf/default.py` - base settings.
- `apigateway/apigateway/conf/settings_dev.py` and `settings_prod.py` - environment-specific settings.
- `apigateway/apigateway/conf/unittest_env` - default test environment, SQLite databases.
- `apigateway/apigateway/data/apigw-definitions/` - gateway resource YAML definitions.
- `apigateway/apigateway/data/apidocs/zh/` - markdown API docs used by OpenAPI consistency checks.
- `apigateway/apigateway/tests/` - pytest suite, mirroring source structure.

## Architecture

`import-linter` enforces the main dependency direction:

```text
apis -> biz -> controller -> service -> components -> apps -> core -> common -> utils
```

Higher layers may import lower layers only. If you need to cross this boundary,
put shared logic in the lower appropriate layer instead of adding an import
exception.

Layer intent:

- `apis/` - HTTP API surfaces and serializers.
- `biz/` - business orchestration and handlers.
- `controller/` - release pipeline, APISIX config conversion, transformers, distributors, publisher tasks.
- `service/` - shared service integrations such as ES, Prometheus, SDK, audit, context, plugin helpers.
- `components/` - external BlueKing system clients.
- `apps/` - Django apps, models, admin, migrations, management commands, Celery tasks.
- `core/` - central gateway domain models such as `Gateway`, `Stage`, `Resource`, `ResourceVersion`, `Release`, `Backend`, `Context`.
- `common/` - reusable middleware, permissions, fields, mixins, tenant helpers, factories.
- `utils/` - low-level utility functions.

The v2 API surfaces are intentionally independent:

- `apigateway.apis.v2.sync` - sync APIs for SDK or automation clients that manage gateways.
- `apigateway.apis.v2.inner` - internal APIs, mainly for BlueKing internal callers.
- `apigateway.apis.v2.open` - public open APIs.

Do not share view/serializer code across these API surfaces by importing from one
surface into another. Move common behavior down into `biz`, `service`, `common`,
or `utils` when needed.

## Domain Notes

- The main model chain is `Gateway -> Stage -> Resource -> ResourceVersion -> Release -> ReleaseHistory`.
- `Gateway` is the current domain name. Legacy DB columns and some payloads still
  use `api`, `api_id`, or `api_name`; do not introduce new API naming unless you
  are touching an existing compatibility boundary.
- Stage/resource plugins use `PluginBinding`.
- Auth and other scoped configuration live in `Context` records.
- Backends are gateway-scoped, with stage-specific `BackendConfig` records.
- Multi-tenant behavior is controlled by `ENABLE_MULTI_TENANT_MODE`; non-tenant
  mode still mounts ESB routes and apps.
- Settings are selected by `BKPAAS_ENVIRONMENT`, loading
  `apigateway.conf.settings_<environment>`; default is `dev`.

## Runtime Setup

Use `uv` as the source of truth for the environment.

```bash
cd src/dashboard
make init
uv sync
```

For CI-equivalent dependency installation:

```bash
cd src/dashboard
uv sync --locked --all-extras --dev
```

Before running Python tools, verify the interpreter matches `pyproject.toml`:

```bash
cd src/dashboard
uv run python --version
```

If an existing `.venv` reports Python 3.10 or old tool versions, refresh it with
`uv sync` before trusting lint or test results. Do not assume a pre-existing
`.venv` is current.

After dependency changes:

```bash
cd src/dashboard
make uv.lock
uv lock --check
```

## Local Development

Prepare MySQL databases for a real local server:

```sql
CREATE DATABASE IF NOT EXISTS `bk_apigateway` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
CREATE DATABASE IF NOT EXISTS `bk_esb` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
```

Then configure and run Django:

```bash
cd src/dashboard
uv sync
cp apigateway/apigateway/conf/.env.tpl apigateway/apigateway/conf/.env
uv run python apigateway/manage.py migrate
uv run python apigateway/manage.py migrate --database bkcore
uv run python apigateway/manage.py runserver
```

The frontend is developed separately in `src/dashboard-front`. A local nginx
reverse proxy usually sends `/backend/` to the dashboard server and other paths
to the frontend dev server.

## Edition System

Edition-specific code lives under `apigateway/apigateway/editions/` and is
activated through `editionctl`.

```bash
cd src/dashboard
make edition
make edition-ee
make edition-te
make edition-develop
make edition-reset
make edition-modules
```

CI runs lint and tests after `make edition-ee`. If imports or tests fail because
edition links are missing, run `make edition-ee` before debugging application
logic.

## Linting

Configured in `pyproject.toml`:

- `ruff` handles formatting and linting.
- `mypy` runs with strict optional checks and ignores migrations/conf/editions as configured.
- `lint-imports` enforces the layer and API-surface contracts from `pyproject.toml`.

Commands:

```bash
cd src/dashboard
make lint
make lint-check
```

Use `make lint` for local code edits because it auto-formats and fixes what it
can. Use `make lint-check` when you need the CI-style non-mutating check.

## Testing

The normal full test gate is:

```bash
cd src/dashboard
make test
```

Useful variants:

```bash
cd src/dashboard
make test-lf
make test-cov
make test-pdb
```

Focused pytest pattern for agents:

```bash
cd src/dashboard
uv run bash -lc 'cd apigateway && set -a && . apigateway/conf/unittest_env && set +a && python3 -m pytest --nomigrations --ds apigateway.settings -q --tb=short apigateway/tests/path/to/test_file.py::TestClass::test_method'
```

Notes:

- Tests live under `apigateway/apigateway/tests/` and mirror source paths.
- `apigateway/conf/unittest_env` uses SQLite for both `default` and `bkcore`.
- Always pass `--ds apigateway.settings` for direct pytest runs.
- Add `--nomigrations` for focused runs when branch migration conflicts block DB setup.
- Use `request_view`, `request_to_view`, `fake_gateway`, `fake_stage`, `fake_backend`,
  `fake_resource`, and related fixtures from `tests/conftest.py`.
- Model setup commonly uses `ddf` / `django_dynamic_fixture` `G()`.
- API tests usually call the URL by `view_name` and assert through `resp.json()`.

## OpenAPI And API Docs

When changing an open API, keep these three surfaces aligned:

- API implementation: views and serializers under `apigateway/apigateway/apis/`.
- Gateway YAML definitions: `apigateway/apigateway/data/apigw-definitions/`.
- Markdown docs: `apigateway/apigateway/data/apidocs/zh/`.

Run the consistency checker:

```bash
cd src/dashboard
make check-openapi
make check-openapi SCOPE=v2_sync
make check-openapi API=v2_sync_gateway
make check-openapi JSON=1
make check-openapi FIX=1
```

For changed or new endpoints, update the matching markdown doc with method,
path, parameters or request body, response fields, status codes, and error
examples. The frontend team uses these docs for integration.

## Response And Validation Patterns

- Prefer serializer validation at the API boundary; do not duplicate it in views
  unless the rule depends on already-loaded domain state.
- Web and v2 APIs commonly return `OKJsonResponse` / `FailJsonResponse` from
  `apigateway.utils.responses`.
- Legacy open APIs may use `V1OKJsonResponse` / `V1FailJsonResponse`; do not
  switch formats unless the compatibility contract changes.
- For health or security-sensitive errors, keep client messages sanitized and
  log original exceptions with `logger.exception(...)`.
- For drf-yasg docs, serializers commonly define unique `Meta.ref_name` values;
  preserve that pattern when adding serializers.

## Build And Runtime Entrypoints

Image build targets copy a clean build tree and remove tests, edition metadata,
and local artifacts before building.

```bash
cd src/dashboard
make image-ee
make image-te
make dev-ee-image
```

Runtime scripts source `${BK_HOME}/etc/bk_apigateway/bk_apigateway.env` when it
exists. `bin/start.sh` runs Gunicorn with gevent workers and Prometheus
multiprocess mode. Keep `/metrics` compatibility in mind when changing URL
routing, middleware, or process startup.

## Security And Secrets

- Do not commit real `.env` values, app secrets, database credentials, tokens, or
  generated certificates.
- `apigateway/apigateway/conf/.env` is local-only; copy from `.env.tpl`.
- Check permission classes, middleware, serializer validation, and tenant checks
  before accepting or rejecting a security report.
- When a report points at a sink, trace the route, serializer, permission class,
  and downstream handler before deciding whether the issue is real.

## Post-Implementation Requirements

For markdown-only documentation changes, do not run `make lint` or `make test`;
verify the diff instead.

For code changes:

1. Add or update focused tests under `apigateway/apigateway/tests/`.
2. Update API docs and gateway YAML definitions when an API contract changes.
3. Run the narrow relevant pytest target first.
4. Run `make lint`.
5. Run `make check-openapi` if any open API, YAML definition, serializer, or API
   markdown doc changed.
6. Run `make test` for broad code changes or when shared behavior is touched.

If a verification command is skipped, say exactly why.
