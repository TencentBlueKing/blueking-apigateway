# AGENTS.md

Guidance for coding agents working in `src/core-api`.

## Scope

- This file applies only to the BlueKing API Gateway core-api service.
- Work from `src/core-api` for Go commands. The repository root `.envrc` is for other
  subprojects and should not be used to activate this service.
- Touch only the files required by the task. Ignored local artifacts such as
  `.envrc`, `vendor/`, `bin/`, `config.yaml`, `.coverage.cov`, logs, certs, and the
  built binary are developer-local unless the user explicitly asks otherwise.

## Service Overview

- Go module: `core`
- Required Go version: `1.25.5` (`go.mod`, Dockerfile, and CI all target Go 1.25).
- Main stack: Gin HTTP server, Cobra CLI, Viper config, sqlx/MySQL, zap logging,
  Prometheus metrics, Sentry, and OpenTelemetry.
- Entry path: `main.go` -> `cmd.Execute()` -> `cmd/root.go` -> `Start()` ->
  `server.Run()`.
- Runtime config is required through `-c/--config`; use `config.yaml.tpl` as the
  tracked template and keep local `config.yaml` uncommitted.

## Runtime Setup

Use the local service directory:

```bash
cd src/core-api
```

Activate Go 1.25.5 before any Go or Make command. In this checkout, the ignored
local `.envrc` uses GVM:

```bash
source .envrc
go version
```

Expected version:

```text
go version go1.25.5 linux/amd64
```

If `.envrc` is absent, use the local Go version manager available on the machine
or set `GOTOOLCHAIN=auto` only when that is enough for the task. Do not source the
repository root `.envrc` for core-api.

## Make Targets

- `make init`: install pre-commit plus local tools into `./bin`
  (`golangci-lint`, `ginkgo`, `mockgen`, `gofumpt`, `golines`,
  `goimports-reviser`, `swag`).
- `make dep`: run `go mod tidy` and `go mod vendor`. This writes the ignored
  local `vendor/` tree.
- `make build`: build `bk-apigateway-core-api` with version ldflags.
- `make serve`: build, then run `./bk-apigateway-core-api -c config.yaml`.
- `make dev-image`: build the Docker image `bk-apigateway-core-api:development`.
- `make fmt`: run golangci formatters from `./bin/golangci-lint fmt`.
- `make lint`: run `./bin/golangci-lint run --fix`, then check license headers.
  This command can modify files; always check `git status --short` after it.
- `make test`: run `go test -mod=vendor -gcflags=all=-l` for non-mock,
  non-doc packages and write `.coverage.cov`.
- `make cov`: open coverage from `.coverage.cov`.
- `make mock`: run `go generate ./...` for `mockgen` directives.
- `make doc`: run `swag init` and refresh `docs/docs.go`, `docs/swagger.json`,
  and `docs/swagger.yaml`.

If Go reports inconsistent vendoring, run `make dep` from `src/core-api` first.
Do not hand-edit `vendor/modules.txt`.

## Architecture

Keep the service layering strict:

```text
pkg/api/{microgateway,open}
  -> pkg/service
  -> pkg/cacheimpls
  -> pkg/database/dao
  -> pkg/database
```

- API handlers validate/bind Gin input, translate service errors to HTTP
  responses, and should not query DAOs directly.
- Services own business decisions such as permission resolution, public-key
  lookup, publish-event deduplication, and cache composition.
- `pkg/cacheimpls` owns cache keys, TTLs, fallback behavior, and DB retrieve
  functions.
- `pkg/database/dao` owns SQL for existing dashboard tables:
  `core_api`, `core_stage`, `core_release`, `core_release_history`,
  `core_resource_version`, `core_jwt`, `permission_app_api`,
  `permission_app_resource`, and `core_publish_event`.
- `pkg/database` owns the default sqlx client, MySQL DSN/TLS setup, slow SQL
  logging, and sqlstats Prometheus registration.

Support packages:

- `pkg/server`: HTTP server, routes, graceful shutdown.
- `pkg/middleware`: request ID, metrics, API logging, micro-gateway auth,
  BK Gateway JWT auth.
- `pkg/config`: Viper-backed config structs and validation.
- `pkg/logging`, `pkg/metric`, `pkg/trace`, `pkg/sentry`: observability setup.
- `pkg/util`: response shapes, validation messages, request helpers.
- `pkg/version`: ldflag-populated build metadata.

## HTTP Surface

Global middleware in `pkg/server/router.go`:

- `middleware.RequestID()`
- `middleware.Metrics()`
- Sentry recovery
- optional `otelgin.Middleware(...)` when tracing Gin instrumentation is enabled

Ops routes:

- `GET /ping`
- `GET /healthz`: checks every configured DB with tiny connection-pool limits.
- `GET /metrics`: Prometheus handler.
- `GET /swagger/*any`: only when `debug: true`.

Micro-gateway routes under `/api/v1/micro-gateway`:

- `GET /:micro_gateway_instance_id/permissions/`
- `GET /:micro_gateway_instance_id/public_keys/`
- `POST /:micro_gateway_instance_id/release/:publish_id/events/`

Micro-gateway auth uses `X-Bk-Micro-Gateway-Instance-Id` and
`X-Bk-Micro-Gateway-Instance-Secret`; the header instance ID must match the path
instance ID and the configured `auth.id`/`auth.secret`.

Open API routes:

- `GET /api/v1/open/gateways/:gateway_name/public_key/`
- `GET /api/v2/open/gateways/:gateway_name/public_key/`

Open API auth uses `X-Bkapi-Jwt`. The JWT is verified with the public key of the
official gateway name `bk-apigateway`, and the `app.verified` claim must be true.
Keep v1 and v2 response formats separate.

## Response Compatibility

- Micro-gateway APIs and open API v2 use `util.SuccessJSONResponse` and
  `util.ErrorResponse`: `{ "data": ... }` or
  `{ "error": { "code": "...", "message": "...", "system": "bk-apigateway" } }`.
- Open API v1 is legacy-compatible and uses `LegacySuccessResponse` /
  `LegacyErrorResponse`: `result`, `code`, `message`, and `data`.
- `sql.ErrNoRows` normally maps to 404; other DAO/cache/service errors normally
  map to system errors. Preserve this distinction unless the task explicitly
  changes the API contract.

## Cache And Data Contracts

- `CacheWithFallback` wraps the primary `gopkg/cache/memory` cache with a longer
  in-memory fallback cache.
- Fallback is used only by `Get`, only when the primary retrieval error is not
  `sql.ErrNoRows`. Typed helpers such as `GetString` delegate to the primary
  cache and do not use fallback.
- Random extra expiration is used to reduce thundering herd behavior.
- Primary + fallback TTLs:
  - `gateway`: 2h + 24h
  - `stage`: 5m + 12h
  - `release`: 1m + 12h
  - `release_history`: 1m + 12h
  - `app_gateway_permission`: 1m + 12h
  - `app_resource_permission`: 1m + 12h
- Non-fallback caches:
  - `jwt_public_key`: 12h
  - `resource_version_mapping`: 12h
  - `publishEventCache`: 10m TTL, 15m cleanup interval
- `AppPermissionService.Query` returns gateway permission early when gateway
  permission expires later than `now + ClientLRUCacheTTL` (60 seconds). Be careful
  when changing this; APISIX plugin LRU behavior depends on it.
- `PublishEventService.Report` rejects release histories older than 1 hour and
  deduplicates by gateway ID, stage ID, publish ID, step, and status.

## Configuration

Tracked template: `config.yaml.tpl`.

Required config:

- `auth.id`
- `auth.secret`
- at least one `databases` entry
- a database entry with `id: "apigateway"`

Important sections:

- `server`: host, port, timeouts.
- `databases`: MySQL connection pool, timeout, optional TLS.
- `logger`: default and API loggers.
- `tracing`: OTLP `http` or `grpc`, sampler, token, service name, Gin/DB
  instrumentation switches.
- `sentry`: DSN and zap report level.
- `debug`: enables Swagger route when true.

Do not commit local `config.yaml`, certificates, passwords, DSNs, or tokens.

## Observability Notes

- API logging reads and restores the request body, truncates request body/query
  and successful response body to 1024 bytes, and includes full response body for
  non-200 responses.
- 5xx responses from API logging are sent to Sentry when Sentry is enabled.
- Metrics:
  - `apigateway_core_api_requests_total`
  - `apigateway_core_api_request_duration_milliseconds`
- The duration metric name says milliseconds, but the middleware currently
  observes microseconds. Do not rename or rescale it without checking dashboards
  and alerting rules.
- SQL stats are registered through `github.com/dlmiddlecote/sqlstats` after DB
  initialization.

## Tests

Tests live next to packages as `*_test.go`. The suite mixes standard `testing`
with Ginkgo/Gomega. Useful focused commands:

```bash
go test -mod=vendor ./pkg/service -count=1
go test -mod=vendor ./pkg/cacheimpls -run TestCacheWithFallback -count=1
go test -mod=vendor ./pkg/middleware -run TestBkGatewayJWTAuthMiddleware -count=1
```

DAO tests use `sqlmock` helpers from `pkg/database/dbmock.go`. Service tests use
generated mocks under `pkg/service/mock` and `pkg/database/dao/mock`.

For code changes:

1. Run the smallest focused package test that covers the touched behavior.
2. Run `make lint`.
3. Run `make test`.
4. Re-check `git status --short` because `make lint` can rewrite files.

For dependency changes, run `make dep` before tests and review `go.mod` /
`go.sum`. The ignored `vendor/` tree is for local vendor-mode testing and should
not be committed unless the repository policy changes.

## Codegen

- Interfaces with `//go:generate mockgen ...` are in service and DAO packages.
  Run `make mock` after changing those interfaces.
- Swagger annotations for open APIs live beside handlers, especially
  `pkg/api/open/public_key.go`. Run `make doc` after changing annotations,
  route contracts, response structs, or public API docs.
- If a route or response contract is externally exposed through the dashboard
  gateway definitions, check the tracked definitions under
  `src/dashboard/apigateway/apigateway/data/apigw-definitions/` before calling
  the API change complete.

## Style

- Local imports use module prefix `core`.
- Follow existing package boundaries instead of adding cross-layer shortcuts.
- Use context-aware DB/cache/service calls.
- Keep `sql.ErrNoRows` handling explicit.
- Add or update focused tests for behavior changes.
- Keep all non-vendor, non-mock Go files with the TencentBlueKing MIT license
  header. `make lint` and `make check-license` enforce this.
- `.golangci.yaml` is golangci-lint v2 config. It enables gofmt, goimports,
  gofumpt, and golines formatters with 120-column wrapping.

## Security

- Treat micro-gateway instance credentials, JWTs, DSNs, database passwords, and
  TLS material as secrets.
- New logs and errors should not expose credentials or token bodies. Existing API
  logging already captures request bodies, so be extra careful before adding new
  sensitive request fields.
- MySQL TLS supports CA-only or client cert/key config. `InsecureSkipVerify` is
  for testing only and must not be enabled in production config.

## Build And CI

- Docker build uses `golang:1.25.5` as the builder and copies the binary plus
  `dlv` into `tencentos/tencentos4-minimal`.
- GitHub Actions workflow: `.github/workflows/core-api.yml`.
- CI triggers on `src/core-api/**` for `master`, `pre_*`, `ft_*`, and
  `release/*` branches.
- CI runs build, golangci-lint v2.11, Trivy filesystem scan, then
  `make dep && make test`.

## Pull Requests

- Use the repository PR template.
- When the user asks to make a PR, target `upstream/master` unless they specify a
  different base branch.
- Include local verification evidence in the PR body or final handoff.

## Post-Implementation Requirements

- For Markdown-only documentation edits, do not run `make lint` or `make test`.
  Verify with `git diff --check -- <changed-md-file>` and re-read the edited
  section for stale claims.
- For Go, config template, Dockerfile, Makefile, generated docs, or dependency
  changes, run the focused checks relevant to the touched files, then the service
  gate from `src/core-api`: `make lint` and `make test`.
