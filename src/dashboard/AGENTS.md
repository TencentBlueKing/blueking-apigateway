# AGENTS.md

Guidance for coding agents working in `src/dashboard`. The repository-root
`AGENTS.md` also applies. Read the nearest nested `AGENTS.md` before changing a
directory that has one.

## Scope

- Work from `src/dashboard` unless a command says otherwise.
- Do not touch sibling projects for dashboard-only requests.
- Start from the exact path, endpoint, traceback, SQL, commit, PR, or report
  named by the user and verify it against the active checkout.
- Before changing code, read the target file, its relevant caller or route, its
  serializer or form, and the nearest tests.
- Keep changes surgical. Do not reformat or refactor adjacent code unless the
  requested change requires it.
- During refactors, preserve useful comments and keep unchanged control flow in
  contiguous blocks when that makes the diff easier to review.
- This subproject is Python-only. Frontend code lives in
  `src/dashboard-front`.

## Command Roots And Runtime

Follow the repository-root checkout and worktree rules before selecting a
branch or PR. Derive paths from the active checkout:

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
DASHBOARD_ROOT="$REPO_ROOT/src/dashboard"
cd "$DASHBOARD_ROOT"
```

Run repository-level `git`, `gh`, and worktree commands from `REPO_ROOT`. Run
dashboard `make`, `uv`, lint, test, and management commands from
`DASHBOARD_ROOT`. Use `uv run` for Python-backed Make targets so a global pyenv
or stale `.venv` is not mistaken for a code failure.

For direct Django pytest, use the wrapper in **Testing**. If a command reports a
missing executable, wrong Python version, unconfigured Django settings, or an
unrelated PR, re-check the worktree, command root, and runtime before treating
it as a product failure.

## Project Overview

BlueKing API Gateway Dashboard is the Django control plane for gateway
definitions, stages, resources, releases, permissions, plugins, SDK generation,
MCP servers, and data-plane publication. It stores and validates gateway state,
then publishes controller configuration through
`controller -> etcd -> operator -> APISIX`.

The current Python, Django, tooling, and dependency versions are defined by
`pyproject.toml` and `uv.lock`. The Django project root is `apigateway/`; the
importable package is `apigateway/apigateway/`.

## Important Paths

- `Makefile` - supported setup, lint, test, edition, fixture, and image targets.
- `pyproject.toml` and `uv.lock` - dependencies, tool configuration, and lockfile.
- `apigateway/apigateway/urls.py` - top-level URL routing.
- `apigateway/apigateway/conf/` - settings and test environment.
- `apigateway/apigateway/data/apigw-definitions/` - gateway resource YAML.
- `apigateway/apigateway/data/apidocs/zh/` - OpenAPI markdown documentation.
- `scripts/check_api_consistency.py` and `scripts/config.yaml` - deterministic
  API/YAML/documentation consistency checks.
- `apigateway/apigateway/tests/` - pytest suite, mirroring source structure.
- `apigateway/apigateway/` layer guides: `apis/AGENTS.md`, `biz/AGENTS.md`,
  `controller/AGENTS.md`, `service/AGENTS.md`, and `core/AGENTS.md`; read the
  guide under the directory being changed.
- `apigateway/apigateway/apis/web/plugin/AGENTS.md` - plugin fixtures,
  conversion, compatibility, and focused verification.
- Repository-root `docs/ai-gateway-models.md` - AI Gateway domain contract.
- Repository-root
  `docs/superpowers/specs/2026-07-21-ai-backend-web-protocol-decoupling-design.md`
  - AI Backend Web/storage/publish protocol design.

## Architecture

`import-linter` enforces the main dependency direction:

```text
apis -> biz -> controller -> service -> components -> apps -> core -> common -> utils
```

Higher layers may import lower layers only. Put shared logic in the lowest
appropriate layer instead of adding an import exception.

Layer ownership:

- `apis/` owns HTTP surfaces, serializers, boundary validation, parameter
  shaping, and response assembly. Read `apigateway/apigateway/apis/AGENTS.md`.
- `biz/` owns use-case workflows, permission-aware decisions, lifecycle
  branching, audit or side-effect orchestration, transactions, and sequencing.
  Read `apigateway/apigateway/biz/AGENTS.md`.
- `controller/` owns release compilation, APISIX conversion, distribution, and
  publisher tasks. Read `apigateway/apigateway/controller/AGENTS.md`.
- `service/` owns focused reusable leaf capabilities over domain data. It must
  not absorb workflow decisions merely to bypass a `biz` import boundary. Read
  `apigateway/apigateway/service/AGENTS.md` before changing it.
- `components/` owns clients for external BlueKing systems.
- `apps/` owns Django app models, admin, migrations, commands, and Celery tasks.
- `core/` owns the central gateway domain models and normalized configuration.
  Read `apigateway/apigateway/core/AGENTS.md` before changing it.
- `common/` owns reusable middleware, permissions, fields, mixins, tenant
  helpers, and factories. `utils/` owns low-level utilities.

When placing a function:

1. Keep module-local or single-domain behavior where it is.
2. Keep API-surface shaping in the owning view or serializer.
3. Put workflows and decisions in `biz/` or release compilation in
   `controller/`.
4. Put only the smallest focused, reusable relation, query, or data operation
   in `service/`.
5. Keep reusable single-model queryset logic in managers; do not put
   multi-model business queries there.

## Domain Notes

- The main model chain is
  `Gateway -> Stage -> Resource -> ResourceVersion -> Release -> ReleaseHistory`.
- `Gateway` is the current domain name. Legacy DB columns and payloads may still
  use `api`, `api_id`, or `api_name`; do not expand legacy naming.
- Stage and resource plugins use `PluginBinding`.
- Scoped authentication and configuration live in `Context` records.
- Backends are gateway-scoped, with stage-specific `BackendConfig` records.
- `ENABLE_MULTI_TENANT_MODE` controls tenancy; `BKPAAS_ENVIRONMENT` selects the
  settings module and defaults to `dev`.

## AI Gateway And Backend Configuration

Read both AI Gateway documents in **Important Paths** before changing AI
models, APIs, connectivity checks, plugin compatibility, or publishing. Current
code and tests take precedence over older plans or review reports.

Keep these representations separate:

1. The flat Web DTO and `AIBackendWebConfigAdapter`, owned by `apis/`.
2. The normalized stored `AIBackendConfig` owned by `core/`.
3. The APISIX plugin configuration compiled by `controller/`.

Follow the owning API, core, controller, and plugin guides when changing a
representation or its transition. Do not repair one representation by leaking
its surface-specific rules into another layer.

## Runtime Setup

Use `uv`, `pyproject.toml`, and `uv.lock` as the environment source of truth:

```bash
cd src/dashboard
make init
uv sync --locked --all-extras --dev
uv run python --version
```

Refresh a stale `.venv` with `uv sync` before trusting lint or test results.
After dependency changes, run:

```bash
cd src/dashboard
make uv.lock
uv lock --check
```

## Edition System

Edition-specific code lives under `apigateway/apigateway/editions/`. CI uses
the enterprise edition before lint and tests:

```bash
cd src/dashboard
uv run make edition-ee
```

Use the other edition targets in the Makefile only when the task explicitly
requires another edition or an edition reset.

## Linting

`ruff`, `mypy`, `lint-imports`, and the API consistency checker are configured
in `pyproject.toml` and the Makefile.

```bash
cd src/dashboard
uv run make lint-check
uv run make lint
```

Use `uv run make lint-check` as the default non-mutating agent gate. Run the
mutating `uv run make lint` only when formatting or fixes are intended, then
inspect its diff. `lint-check` does not run `ruff format --check`; use an
explicit non-mutating Ruff format check when formatting evidence is required.

## Testing

The full test gate is:

```bash
cd src/dashboard
uv run make edition-ee
uv run make test
```

For a focused Django pytest target:

```bash
cd src/dashboard
uv run bash -lc 'cd apigateway && set -a && . apigateway/conf/unittest_env && set +a && python -m pytest --nomigrations --ds apigateway.settings -q --tb=short apigateway/tests/path/to/test_file.py::TestClass::test_method'
```

- Tests mirror source paths under `apigateway/apigateway/tests/`.
- Direct pytest must load `apigateway/conf/unittest_env` and pass
  `--ds apigateway.settings`.
- Use `--nomigrations` for focused tests when branch migration conflicts block
  database setup.
- Reuse fixtures from `tests/conftest.py`; model setup commonly uses `G()` from
  `django_dynamic_fixture`.

## Security And Secrets

- Do not commit `.env` values, app secrets, database credentials, tokens, or
  generated certificates.
- Copy local configuration from `apigateway/apigateway/conf/.env.tpl`.
- Verify routes, serializers, permissions, tenant checks, and downstream
  handlers before accepting or rejecting a security report.
- API responses, logs, exceptions, audit events, and publish history must not
  expose plaintext or encrypted credential payloads.

## Post-Implementation Requirements

For markdown-only documentation changes, do not run `make lint` or `make test`;
verify the diff and referenced paths instead.

For code changes:

1. Add or update focused tests under `apigateway/apigateway/tests/`.
2. Update API docs and gateway YAML when an API contract changes.
3. Run the narrow relevant pytest target first.
4. Run `uv run make edition-ee && uv run make lint-check` for the CI-style lint
   gate. Use `uv run make lint` only when auto-fix changes are intended.
5. Run `uv run make edition-ee && uv run make test` for broad or shared changes.

If a required verification command is skipped, say exactly why.
