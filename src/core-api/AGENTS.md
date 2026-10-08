# Core API

## Runtime and commands

Run commands from `src/core-api`. The Go module is `core`; `go.mod` and
`Dockerfile` pin Go 1.25.5, while `.github/workflows/core-api.yml` selects Go 1.25.
Use an available matching toolchain. A local `.envrc` is optional and untracked.
Start local configuration from `config.yaml.tpl`; the CLI requires `-c/--config`.

| Command | Effect |
| --- | --- |
| `make init` | Install pre-commit hooks and development tools into `bin/` |
| `make dep` | `go mod tidy` and refresh ignored `vendor/` |
| `make build` / `make serve` | Build `bk-apigateway-core-api` / run it with `config.yaml` |
| `make fmt` | Apply configured golangci formatters |
| `make lint` | golangci-lint **with fixes**, then license-header check |
| `make test` | Vendor-mode Go tests excluding mock/docs packages; `.coverage.cov` |
| `make mock` | Run `go generate ./...` |
| `make doc` | Regenerate Swagger artifacts under `docs/` |
| `make cov` / `make dev-image` | View coverage / build development image |

For code/config/build changes, run the affected package tests, then `make lint`
and `make test`; inspect formatter/linter edits. Examples:

```bash
go test -mod=vendor -gcflags=all=-l ./pkg/service -count=1
go test -mod=vendor -gcflags=all=-l ./pkg/cacheimpls -run TestCacheWithFallback -count=1
```

Run `make dep` when dependencies change or vendoring is inconsistent; review
`go.mod`/`go.sum`. Do not hand-edit or commit ignored `vendor/`, `bin/`, local
configuration, coverage, or built binaries. CI also builds and scans the service;
its precise job/tool configuration is in `.github/workflows/core-api.yml`.

## Ownership and entrypoints

- Startup: `main.go` → `cmd/root.go` → `pkg/server`; routes are registered in
  `pkg/server/router.go`.
- `pkg/api/{microgateway,open}` binds input and selects HTTP responses;
  `pkg/service` owns permission queries, keys, and event ingestion;
  `pkg/cacheimpls` owns retrieval/expiry/fallback; `pkg/database/dao` owns SQL;
  `pkg/database` owns clients, TLS, slow-query logs, and SQL metrics. Preserve
  these boundaries instead of issuing DAO queries from handlers.
- `pkg/config` loads Viper configuration; `pkg/middleware` handles request IDs,
  authentication, API logs, and metrics. Logging, tracing, and Sentry setup have
  separate packages.
- Tables are shared with Dashboard. Changes to DAO fields or query semantics
  must agree with its models/migrations. Public route changes may also require
  `src/dashboard/apigateway/apigateway/data/apigw-definitions/` updates.

## Request and cache contracts

- Micro-gateway routes under `/api/v1/micro-gateway` expose permissions, public
  keys, and publish-event reporting. Authentication checks both
  `X-Bk-Micro-Gateway-Instance-Id` and `X-Bk-Micro-Gateway-Instance-Secret` against
  configured credentials and matches the instance ID in the URL.
- Open public-key routes under `/api/v1/open` and `/api/v2/open` require
  `X-Bkapi-Jwt`, verified with the `bk-apigateway` public key and a true
  `app.verified` claim. Preserve v1 legacy `result/code/message/data` responses
  separately from v2 and micro-gateway `data`/`error` envelopes.
- Keep `sql.ErrNoRows` distinct from retrieval/system errors in HTTP mapping.
- `CacheWithFallback.Get` can use stale fallback on primary retrieval errors
  other than `sql.ErrNoRows`; typed getters delegate to the primary only.
  Expiry and jitter are defined in `pkg/cacheimpls` constructors; changes affect
  both freshness and outage tolerance.
- `AppPermissionService.Query` returns early when gateway permission outlives
  `now + ClientLRUCacheTTL` (60 seconds). Preserve its APISIX LRU compatibility.
- `PublishEventService.Report` rejects histories older than one hour and
  deduplicates on gateway, stage, publish ID, step, and status. Check its service
  and cache tests when changing event ingestion.

## Configuration and observability

- Configuration needs nonempty `auth.id`/`auth.secret` and a database list;
  startup requires the database ID `apigateway`.
- `pkg/config/kms.go` applies optional KMS credentials before validation and DB
  map construction. `ENABLE_KMS=true` or `True` requires the encrypted envelope
  at `/etc/secrets/bk-apigateway-kms` and `BK_APIGATEWAY_KMS_PRIVATE_KEY`; enabled
  KMS failures stop startup. It overrides auth secret and database credentials.
- `/ping` is liveness; `/healthz` checks configured databases; `/metrics` exposes
  Prometheus metrics; Swagger is available only with `debug: true`.
- API logging restores the request body, truncates request/query and successful
  response previews, and records full non-200 response bodies. Avoid exposing
  credentials in new fields/logs. 5xx logs can be sent to Sentry.
- `apigateway_core_api_request_duration_milliseconds` currently observes
  **microseconds** (`pkg/middleware/metrics.go`). Changing units/names requires
  checking consumers, dashboards, and alerts.
- MySQL TLS configuration supports CA and client certificates; keep
  `InsecureSkipVerify` disabled in production.

## Tests, generation, and style

Tests mix Go `testing` and Ginkgo/Gomega. DAO tests use `pkg/database/dbmock.go`;
service/DAO mocks are generated under their `mock/` directories. Update mocks
with `make mock` after interface changes and Swagger with `make doc` after
annotation or public contract changes.

Use module prefix `core`, context-aware calls, and the TencentBlueKing MIT header
on non-mock Go files. `.golangci.yaml` owns formatter/linter rules, including
120-column wrapping; do not duplicate those rules in child guides.
