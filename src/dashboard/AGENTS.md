# AGENTS.md

Guidance for coding agents working in `src/dashboard`. Treat this file as the
local contract for dashboard changes; the repository-root AGENTS.md still
applies.

## Scope

- Read this file through **Post-Implementation Requirements** before running
  commands; the runtime and final gates are documented after the architecture.
- Work from `src/dashboard` unless a command says otherwise.
- Do not touch sibling projects (`src/dashboard-front`, `src/core-api`,
  `src/mcp-proxy`, `src/esb`) for dashboard-only requests.
- Start from the exact path, endpoint, traceback, SQL, commit, PR, or report named
  by the user and verify it against the active checkout.
- Before changing code, read the target file and, as applicable, its immediate
  caller or URL route, serializer/form, and nearest tests.
- Keep changes surgical. Do not reformat or refactor adjacent code unless the
  requested change requires it.
- During refactors, preserve useful comments and keep unchanged control flow in
  contiguous blocks when that makes the diff easier to review.
- This subproject is Python-only. Frontend code lives in `src/dashboard-front`.

## Command Roots And Runtime

Follow the repository-root checkout/worktree rules before selecting a branch or
PR. Do not hard-code workspace prefixes such as `/root/workspace` or
`/data/workspace`; derive the dashboard root from the active checkout:

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
DASHBOARD_ROOT="$REPO_ROOT/src/dashboard"
cd "$DASHBOARD_ROOT"
```

Run repository-level `git`, `gh`, and worktree commands from `REPO_ROOT`. Run
dashboard `make`, `uv`, lint, test, and management commands from
`DASHBOARD_ROOT`. Use `uv run` for Python-backed Make targets so a global pyenv,
stale `.venv`, or missing shell executable is not mistaken for a code failure.

For direct Django pytest, use the wrapper in **Testing**; plain pytest does not
load `apigateway/conf/unittest_env` or the required Django settings. If a command
reports a missing executable, wrong Python version, unconfigured Django settings,
or an unrelated PR, stop and re-check the worktree, command root, and runtime
before interpreting the result as a product failure.

## Project Overview

BlueKing API Gateway Dashboard is the Django control plane for managing gateway
definitions, stages, resources, releases, permissions, plugins, SDK generation,
MCP servers, and data-plane publication. Apache APISIX is the data plane; this
service stores and validates gateway state, then turns releases into controller
configuration that is published through `controller -> etcd -> operator -> APISIX`.

Current stack, from the checked-in files:

- Python `>=3.14,<3.15` in `pyproject.toml`; CI uses Python `3.14.6`.
- Django `5.2.15`, Django REST Framework `3.17.1`.
- Dependencies are managed by `uv` with `pyproject.toml` and `uv.lock`.
- The Django project root is `apigateway/` and contains `manage.py`.
- The importable Django package is `apigateway/apigateway/`.

## Important Paths

- `Makefile` - setup, lint, tests, edition switching, Docker image build, OpenAPI consistency lint.
- `pyproject.toml` - dependencies, ruff, mypy, pytest, import-linter contracts.
- `uv.lock` - dependency lockfile; keep it in sync with `pyproject.toml`.
- `Dockerfile` - production image, currently based on `hub.bktencent.com/blueking/python:3.14-tencentos4`.
- `bin/start.sh` - Gunicorn entrypoint; keeps Prometheus multiprocess metrics in `/tmp/`.
- `bin/start_celery.sh` and `bin/start_beat.sh` - Celery entrypoints; worker concurrency defaults to `12` and can be overridden with `BK_APIGW_CELERY_WORKER_CONCURRENCY`.
- `scripts/check_api_consistency.py` - deterministic OpenAPI consistency lint for API code, YAML definitions, and docs.
- `scripts/config.yaml` - OpenAPI consistency lint allowlists and special-case config.
- `apigateway/manage.py` - Django management command entrypoint.
- `apigateway/apigateway/urls.py` - top-level URL routing.
- `apigateway/apigateway/conf/default.py` - base settings.
- `apigateway/apigateway/conf/settings_dev.py` and `settings_prod.py` - environment-specific settings.
- `apigateway/apigateway/conf/unittest_env` - default test environment, SQLite databases.
- `apigateway/apigateway/data/apigw-definitions/` - gateway resource YAML definitions.
- `apigateway/apigateway/data/apidocs/zh/` - markdown API docs used by OpenAPI consistency checks.
- `apigateway/apigateway/fixtures/plugins.yaml` - plugin type, schema, and form fixtures.
- `apigateway/apigateway/apis/web/plugin/AGENTS.md` - local plugin subsystem guide; read it before changing plugins.
- `apigateway/apigateway/tests/` - pytest suite, mirroring source structure.
- Repository root `docs/ai-gateway-models.md` - AI Gateway domain contract.
- Repository root
  `docs/superpowers/specs/2026-07-21-ai-backend-web-protocol-decoupling-design.md`
  describes the current AI Backend Web/storage/publish protocol design.

## Architecture

`import-linter` enforces the main dependency direction:

```text
apis -> biz -> controller -> service -> components -> apps -> core -> common -> utils
```

Higher layers may import lower layers only. If you need to cross this boundary,
put shared logic in the lower appropriate layer instead of adding an import
exception.

Important call rules:

- `apis/` view and serializer code may call `biz/` and `service/` directly.
- `biz/` may call `service/`. Package-local `biz` imports are allowed inside
  one domain or subpackage, but do not add peer-domain imports covered by the
  `biz-domain-independence` contract. That contract currently covers
  `biz.gateway`, `biz.resource`, `biz.permission`, and `biz.mcp_server`.
- `service/` modules may call each other and may contain cross-model operations
  when the operation is focused and reusable.
- `service/` is not a dumping ground for code moved only to avoid `biz`-to-`biz`
  imports. Cross-domain workflow orchestration belongs in a neutral use-case
  `biz` module or in `controller/`, not in `service/`. Keep `service/` to leaf
  capabilities with stable inputs and outputs, clear reuse, direct tests, and no
  permission, audit, lifecycle, or workflow decisions.
- Historical exception: `apigateway.service.release.PublishValidator` currently
  lives under `service/` because it was moved there during the 2026-05
  `biz-domain-independence` refactor to break an import-boundary issue. Treat
  that location as compatibility debt, not as placement precedent. Release
  gating, lifecycle, and publish workflow decisions should prefer
  `biz/release/`; keep only the smallest reusable leaf checks in `service/`.
- Direct model or queryset use from views and serializers is limited to simple
  local reads or writes that are already idiomatic in Django.

Function placement guide:

Use this order when deciding where a new function belongs:

1. Keep it where it is if it is only used inside one module or one `biz`
   domain, especially when moving it would only create a proxy wrapper.
2. Keep view-specific parameter shaping, response assembly, or API-surface
   branching in the owning view or serializer.
3. Put it in `biz/` when it owns use-case flow: what should happen,
   permission-aware decisions, lifecycle branching, audit or side-effect
   orchestration, transactions, or sequencing multiple lower-level operations.
4. Put it in `service/` only when it is a focused reusable leaf operation over
   model relationships or domain data: snapshots, schema lookup, cleanup,
   reusable cross-model queries, relation normalization, or data shaping.
5. When both `biz` and `service` seem possible, keep orchestration in `biz` and
   extract only the smallest reusable relation or data operation to `service`.

Service organization guide:

- Name `service` modules by domain plus capability, not by vague technical
  buckets. Prefer names like `resource_snapshot.py`, `resource_cleanup.py`,
  `resource_version_schema.py`, or `openapi_export.py`; avoid adding new
  behavior to generic modules such as `utils.py` unless the code is truly
  domain-neutral.
- Keep a small capability as a top-level module. Convert a domain into a package
  only after several related service modules exist or a file starts mixing
  unrelated capabilities, for example `service/resource/snapshot.py`,
  `service/resource/cleanup.py`, and `service/resource/labels.py`.
- For `service/<domain>/` packages, external callers must import public symbols from
  `apigateway.service.<domain>`, not from leaf modules such as
  `apigateway.service.<domain>.<capability>`. The package `__init__.py` owns the
  public API and `__all__`; leaf modules must not define `__all__`.
- For `biz/<domain>/` packages covered by the public API contract, callers from
  `apis/` and `apps/` must import public symbols from
  `apigateway.biz.<domain>`, not from leaf modules that import-linter forbids.
- Service package internals may use single-dot relative imports for local
  leaf modules, but should not use parent relative imports such as `..` inside
  `service/`. When reaching outside the current package, use absolute imports
  rooted at `apigateway.service`.
- Function names should describe the action, domain, and output shape or side
  effect. Use `get_*` for reads, `delete_*` or `clear_*` for destructive writes,
  `build_*` for construction, `format_*` or `normalize_*` for shape changes,
  `snapshot_*` for snapshot creation, and `ensure_*` for idempotent creation or
  backfill.
- Prefer free functions for stateless leaf operations. Use classes only when
  the service needs state, strategy selection, validation objects, factories, or
  polymorphic behavior.
- Each non-trivial service module should expose a small public surface: add a
  module docstring that states what the module owns, keep public helpers
  discoverable, and prefix module-private helpers with `_`.

Package `__init__.py` export guide:

- For `biz/` and `service/` package `__init__.py` files that define `__all__`,
  keep exports grouped in this fixed order: `# constant`, `# Enum`, `# class`,
  `# functions`, `# others`.
- Keep every section comment in place even when that section is empty, so later
  additions have an obvious slot.
- Keep names grouped under the matching section. Put module re-exports or other
  uncategorized names under `# others`.

Layer intent:

- `apis/` - HTTP API surfaces and serializers. Serializers own input
  validation and output definitions, and must not introduce N+1 queries for
  computed fields. Views stay thin: simple control flow, parameter building,
  lower-layer calls, and response assembly. Call `biz/` for workflows,
  decisions, permission-aware orchestration, and multi-model operations. Call
  `service/` for focused reusable domain operations, snapshots, cleanup
  helpers, schema lookup, and pure or query helpers. Keep view-level logic
  inside its own API module even when another API surface has the same or
  similar logic.
- `biz/` - workflow and decision logic, including permission-aware
  orchestration and multi-model operations. Keep peer model domains such as
  gateway, resource, resource version, permission, and MCP server independent;
  move shared coordination or reusable domain operations into `service/` when
  needed. Internal helpers within the same `biz` domain may stay inside that
  domain.
- `controller/` - release pipeline, APISIX config conversion, transformers, distributors, publisher tasks.
- `service/` - focused reusable domain operations, snapshots, cleanup helpers,
  schema lookup, and pure or query helpers. `service` modules may import each
  other and may perform cross-model work when the operation is reusable outside
  one view or `biz` workflow.
- `components/` - external BlueKing system clients.
- `apps/` - Django app model layer plus admin, migrations, management commands,
  and Celery tasks. Keep `models.py` rich for single-model properties and
  methods. Keep `managers.py` to reusable single-model queryset logic. Do not
  put multiple-model business queries in managers.
- `core/` - central gateway domain model layer such as `Gateway`, `Stage`,
  `Resource`, `ResourceVersion`, `Release`, `Backend`, `Context`. Follow the
  same model-layer rule as `apps/`: rich single-model methods in `models.py`,
  reusable single-model queryset logic in `managers.py`, and no multiple-model
  business queries in managers.
- `common/` - reusable middleware, permissions, fields, mixins, tenant helpers, factories.
- `utils/` - low-level utility functions.
- Top-level packages such as `account/`, `healthz/`, `schema/`, and `tracing/`
  are outside the main `global-layers` stack. Follow the nearest caller,
  settings, or middleware pattern instead of forcing them into a layer.

The API surfaces are intentionally independent:

- `apigateway.apis.web` - dashboard backend APIs consumed by `dashboard-front`.
- `apigateway.apis.open` - legacy open APIs with compatibility response formats.
- `apigateway.apis.v2.open` - public open APIs.
- `apigateway.apis.v2.inner` - internal APIs, mainly for BlueKing internal callers.
- `apigateway.apis.v2.sync` - sync APIs for SDK or automation clients that manage gateways.

Do not share view or serializer code across API surfaces by importing from one
surface into another. Keep view-level logic in the owning API module
(`apis.open`, `apis.web`, `apis.v2.open`, and other `apis.v2.*` modules), even
when the logic is the same or nearly the same. Duplicate small view logic when
that keeps the surfaces independent, especially because `apis.web` behavior
changes frequently. Move common behavior down into `biz`, `service`, `common`,
or `utils` only when it is true lower-layer business, service, or utility logic
instead of surface-specific view flow.

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

## AI Gateway And Backend Configuration

Read both AI Gateway documents listed in **Important Paths** before changing AI
models, APIs, connectivity checks, plugin compatibility, or publishing. Current
code and tests take precedence when an older plan or review report disagrees.

- `Gateway.kind` is stored as the numeric `GatewayKindEnum`; API names use
  `GatewayKindNameEnum` conversion. `Backend.kind` and `Resource.kind` use the
  string values `standard` and `ai`. Do not repurpose transport `type` fields as
  kind discriminators.
- Keep three representations separate: the flat Web DTO and
  `AIBackendWebConfigAdapter`, the normalized stored `AIBackendConfig`, and the
  APISIX plugin config compiled by `ServiceConvertor`. Open/v2 automation APIs
  intentionally accept the stored protocol rather than the Web DTO.
- `core/ai_backend.py` is the runtime-critical built-in provider registry used
  by Web conversion, connectivity tests, and publishing. A provider change must
  update choices, registry entries, adapter rules, tests, and API documentation.
- Store built-in providers as their product identity. Convert compatible built-ins
  to APISIX `openai-compatible`, add `override.endpoint`, strip
  `model_endpoint`, and convert timeout seconds to milliseconds only at the
  publish boundary.
- Web and automation inputs are single-instance in the first phase, while the
  core config and converter support multiple instances. Keep that external
  restriction out of the core model.
- `BackendConfig.config` transparently encrypts AI config at the ORM persistence
  boundary. Web and audit outputs must mask credentials; API responses, logs,
  exceptions, and publish history must not expose plaintext or encrypted
  payloads. Generated APISIX/etcd runtime config is a credential trust boundary.
- Resource plugin compatibility is enforced across list, bind/update, and
  import paths. Stage configuration stays permissive; AI Service publishing
  filters incompatible Stage plugins. `ai-proxy` and `ai-proxy-multi` are
  controller-managed and must not be user-bound.
- In controller convertor changes, preserve the standard Service/Route blocks
  and their comments; isolate AI-specific behavior in narrow branches unless a
  behavior change requires a broader refactor.

## Runtime Setup

Use `uv` as the source of truth for the environment.

```bash
cd src/dashboard
make init
```

`make init` installs `uv==0.11.26`, runs `uv sync`, installs pre-commit, and
installs mypy stub packages. The Docker image copies `uv==0.11.26`; use the
checked-in lockfile rather than relying on either version detail.

For a local install with CI's locked dependency set:

```bash
cd src/dashboard
uv sync --locked --all-extras --dev
```

In GitHub Actions, the workflow also sets `UV_PROJECT_ENVIRONMENT` to the
action-provided Python location before running the same `uv sync` flags.

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

## Plugin Fixtures

Before changing plugin behavior, read
`apigateway/apigateway/apis/web/plugin/AGENTS.md`.

For plugin type/schema/form maintenance:

```bash
cd src/dashboard
uv run make load_fixtures
# edit through Django admin or update fixtures intentionally
uv run make dump_fixtures
```

New APISIX plugins should normally store APISIX-native YAML and should not add
API-layer or service-layer convertors unless the plugin guide says the legacy
compatibility path applies.

## Edition System

Edition-specific code lives under `apigateway/apigateway/editions/` and is
activated through `editionctl`.

```bash
cd src/dashboard
uv run make edition
uv run make edition-ee
uv run make edition-te
uv run make edition-develop
uv run make edition-reset
uv run make edition-modules
```

CI runs lint and tests after the `edition-ee` target. Run
`uv run make edition-ee` before local lint or test gates unless you are
intentionally checking a different edition.

## Linting

Configured in `pyproject.toml`:

- `ruff` handles formatting and linting.
- `mypy` runs with strict optional checks; migrations, conf, and editions are
  excluded or error-suppressed as configured.
- `lint-imports` enforces the layer and API-surface contracts from `pyproject.toml`.

Commands:

```bash
cd src/dashboard
uv run make lint-check
uv run make lint
```

Use `uv run make lint-check` as the default agent gate because it is
non-mutating. `uv run make lint` formats and fixes files; run it only when those
edits are intended, then inspect the resulting diff. `lint-check` does not run
`ruff format --check`, so use pre-commit or an explicit non-mutating Ruff format
check when formatting evidence is required.

## Testing

The normal full test gate is:

```bash
cd src/dashboard
uv run make edition-ee
uv run make test
```

`make test` runs pytest with `--reuse-db`, `-n auto`, and `--dist loadscope`.

Useful variants:

```bash
cd src/dashboard
uv run make test-lf
uv run make test-cov
uv run make test-pdb
```

Focused pytest pattern for agents:

```bash
cd src/dashboard
uv run bash -lc 'cd apigateway && set -a && . apigateway/conf/unittest_env && set +a && python -m pytest --nomigrations --ds apigateway.settings -q --tb=short apigateway/tests/path/to/test_file.py::TestClass::test_method'
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
- When adding `service/<domain>/` packages or package exports, keep
  `tests/service/test_public_api_contract.py` passing.

## OpenAPI And API Docs

When changing an open API, keep these three surfaces aligned:

- API implementation: views and serializers under `apigateway/apigateway/apis/`.
- Gateway YAML definitions: `apigateway/apigateway/data/apigw-definitions/`.
- Markdown docs: `apigateway/apigateway/data/apidocs/zh/`.

The consistency checker is a deterministic dashboard lint script at
`scripts/check_api_consistency.py`. Both `make lint` and `make lint-check` run
it by default. Use the dedicated target below when you want to rerun only this
gate.

Available commands:

```bash
cd src/dashboard
uv run make lint-openapi
uv run make lint-openapi-help
uv run make lint-openapi SCOPE=v2_open
uv run make lint-openapi SCOPE=v2_inner
uv run make lint-openapi SCOPE=v2_sync
uv run make lint-openapi API=v2_sync_gateway
uv run make lint-openapi JSON=1
uv run make lint-openapi FIX=1
```

For changed or new endpoints, update the matching markdown doc with method,
path, parameters or request body, response fields, status codes, and error
examples. The frontend team uses these docs for integration. CI runs
the same check through `make lint-check`, so keep API, YAML, serializer, and
docs aligned before push.

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
uv run make image-ee
uv run make image-te
uv run make dev-ee-image
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
4. Run `uv run make edition-ee && uv run make lint-check` for the CI-style lint
   gate. Use `uv run make lint` only when auto-format/fix changes are intended.
   This lint gate includes the OpenAPI consistency check; use
   `uv run make lint-openapi` only when you need a focused rerun of that checker.
5. Run `uv run make edition-ee && uv run make test` for broad code changes or
   when shared behavior is touched.

If a required verification command is skipped, say exactly why.
