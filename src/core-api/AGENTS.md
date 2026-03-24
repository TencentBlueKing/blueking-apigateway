# AGENTS.md

Guidance for coding agents working on the core-api service (BlueKing API Gateway).

## Overview
- Go service (module `core`, Go 1.25.5) using Gin + Cobra.
- Entry: `main.go` -> `cmd/root.go` (`core-api` CLI).
- Config required via `-c/--config` (see `config.yaml.tpl`).

## Architecture (strict flow)
`pkg/api/{microgateway,open}` -> `pkg/service` -> `pkg/cacheimpls` -> `pkg/database/dao` -> `pkg/database`

Support packages: `pkg/server`, `pkg/middleware`, `pkg/config`, `pkg/logging`, `pkg/metric`, `pkg/trace`, `pkg/sentry`, `pkg/util`, `pkg/version`.

## HTTP surface
- Ops: `/ping`, `/healthz` (checks all configured DBs), `/metrics` (Prometheus).
- Swagger: `/swagger/*any` only when `config.debug` is true.
- MicroGateway (`/api/v1/micro-gateway`):
  - `GET /:micro_gateway_instance_id/permissions/`
  - `GET /:micro_gateway_instance_id/public_keys/`
  - `POST /:micro_gateway_instance_id/release/:publish_id/events/`
  - Middleware: `APILogger`, `MicroGatewayInstanceMiddleware` (instance ID/secret).
- Open API:
  - `/api/v1/open` and `/api/v2/open`
  - `GET /gateways/:gateway_name/public_key/`
  - Middleware: `BkGatewayJWTAuthMiddlewareV1/V2`.
- Global middleware: `RequestID`, `Metrics`, Sentry recovery; optional OTel gin instrumentation when tracing enabled.

## Caching (cache-first)
- `CacheWithFallback` (`pkg/cacheimpls/cache_with_fallback.go`) wraps `gopkg/cache/memory` with gocache fallback.
- Fallback is used only on non-`sql.ErrNoRows` errors; fallback TTL > primary TTL.
- Primary + fallback TTLs:
  - `gateway` 2h + 24h
  - `stage` 5m + 12h
  - `release` 1m + 12h
  - `release_history` 1m + 12h
  - `app_gateway_permission` 1m + 12h
  - `app_resource_permission` 1m + 12h
- Non-fallback caches: `jwt_public_key` 12h, `resource_version_mapping` 12h.
- `publishEventCache`: in-memory gocache 10m TTL.
- Random extra expiration is added to reduce thundering herd.

## Configuration
- `config.yaml` is required (`-c`); template: `config.yaml.tpl`.
- Required fields: `auth.id`, `auth.secret`, and a `databases` entry with id `apigateway`.
- Key sections: `server`, `auth`, `databases` (supports TLS), `logger`, `tracing`, `sentry`, `debug`.

## Go Version (IMPORTANT — read before running any Go command)

This project requires **Go 1.25.5** (see `go.mod`). The system default `go` is often older.

Before running any `go` command or `make` target, check the repo root for dotfiles that activate the correct Go version (e.g. `.envrc`, `.env`, `.tool-versions`, or similar). Source or apply whichever one is present to get the right `go` on your `PATH`.

Without the correct version, commands will fail with:
`go: go.mod requires go >= 1.25.5 (running go 1.22.x; GOTOOLCHAIN=local)`

## Dev commands (Makefile)
- Setup: `make init`, `make dep`
- Build/run: `make build`, `make serve`, `make dev-image`
- Tests: `make test`, `make cov`
- Quality: `make fmt`, `make lint`, `make check-license`
- Codegen: `make mock`, `make doc`

## Tests & Codegen
- Tests use vendor mode (`-mod=vendor`) and Ginkgo/Gomega.
- `make mock` runs `go generate ./...` for `mockgen` directives.
- `make doc` runs `swag init`.

## After Code Changes

Always run `make lint` and `make test` after making code changes and fix any issues before considering the work done.

When asked to "make a PR", create the pull request targeting `upstream/master`.

## License
- All non-vendor, non-mock Go files must include the TencentBlueKing license header (checked by `make lint`/`make check-license`).
