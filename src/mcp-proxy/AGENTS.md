# AGENTS.md

## Project Overview

**mcp-proxy** is a Go service in the BlueKing API Gateway ecosystem that proxies Model Context Protocol (MCP)
requests. It dynamically creates MCP servers from OpenAPI 3.0 specs stored in the database, converting API
operations into MCP tools. It supports both SSE and Streamable HTTP MCP transports via the official
`modelcontextprotocol/go-sdk`.

## Build & Development Commands

```bash
make init              # Install tooling into ./bin/
make dep               # go mod tidy && go mod vendor
make build             # Build binary: bk-apigateway-mcp-proxy
make serve             # Build and run with config.yaml
make fmt               # Format (golines 120 + gofumpt + goimports-reviser)
make lint              # golangci-lint + license header check
make test              # Ginkgo unit tests (coverage to .coverage.cov)
make mock              # Regenerate mock files (go generate ./...)
make integration       # Integration tests (requires Docker Compose)
make integration-down  # Stop integration env
make cov               # Open coverage report in browser
make dev-image         # Build Docker dev image
```

Run a single test file/package:
```bash
./bin/ginkgo -r -mod=vendor ./pkg/util/...
./bin/ginkgo -r -mod=vendor --focus="TestName" ./pkg/util/...
```

## Runtime Endpoints

- **Health/metrics**: `/ping`, `/healthz`, `/metrics`
- **pprof**: `/debug/pprof` (basic auth; defaults to `bk-mcp` / `DebugModel@bk` if not set in config/env)
- **User mode**: `/:name/sse`, `/:name/mcp` (both GET + POST)
- **Application mode**: `/:name/application/sse`, `/:name/application/mcp` (both GET + POST)

## Config Essentials

- Config file is **required** (`-c` flag); `make serve` uses `config.yaml`. Template: `config.yaml.tpl`.
- `databases` **must include** an entry with `id: "apigateway"` (used as the default DB).
- `mcpServer.interval` defaults to **60s**. `mcpServer.bkApiUrlTmpl` falls back to `BK_API_URL_TMPL` and is used
  to render OpenAPI server URLs with `{api_name}` and `{stage}` placeholders.
- `ENCRYPT_KEY` and `BK_APIGW_CRYPTO_NONCE` are used to decrypt stored gateway JWT private keys (inner JWT signing).
- `PPROF_USERNAME` / `PPROF_PASSWORD` override pprof credentials (change from defaults in production).

## Architecture

### Request Flow

```
Client -> Gin Router -> Middleware -> MCPProxy -> MCPServer -> genToolHandler -> Backend API
```

Per-MCP route middleware: RequestID -> Metrics -> Sentry Recovery -> API Logger -> JWT Auth -> Permission ->
Header extraction.

### Key Packages

- **`cmd/`**: Cobra CLI. Startup: config -> logger -> DB -> tracing -> sentry -> metrics -> server
- **`pkg/server/`**: Gin router + HTTP server lifecycle (graceful shutdown)
- **`pkg/mcp/`**: MCP loader/reloader. `LoadMCPServer()` runs on a ticker (default 60s)
- **`pkg/infra/proxy/`**: MCP proxy layer (MCPProxy, MCPServer, OpenAPI converter, tool/prompt configs)
- **`pkg/infra/database/`**, **`pkg/infra/logging/`**, **`pkg/infra/trace/`**, **`pkg/infra/sentry/`**
- **`pkg/biz/`**: Release/OpenAPI/JWT lookups, MCP server and prompt loading
- **`pkg/cacheimpls/`**: In-memory caches (gateway/stage/JWT: 12h; permissions/prompts: 1m)
- **`pkg/middleware/`**: Gin middleware: request ID, JWT auth, MCP permission, header extraction, logging, metrics
- **`pkg/mcp/middleware.go`**: MCP SDK logging middleware (audit/debug + sentry on errors)
- **`pkg/config/`**: Viper config (`config.G` global)
- **`pkg/metric/`**: Prometheus metrics setup
- **`pkg/constant/`**: Header names, protocol constants, context keys
- **`pkg/repo/`**: GORM Gen DAO code (`*.gen.go`); regenerate with `./bk-apigateway-mcp-proxy gen -c config.yaml`

### Data Flow: OpenAPI -> MCP Tools

1. `LoadMCPServer()` polls active `MCPServer` rows.
2. For each server, fetch `Release` + `OpenapiGatewayResourceVersionSpec` (OpenAPI 3.0 JSON) and set the
   OpenAPI server URL using `mcpServer.bkApiUrlTmpl`.
3. Convert OpenAPI operations to `ToolConfig` (filter by `resource_names`; support renames via
   `resource@tool` entries).
4. Create/update MCP servers and tools; remove deleted tools; load prompts from `MCPServerExtend` (`prompts`).
5. `genToolHandler()` calls backend APIs via `go-openapi/runtime` and lazy-signs inner JWTs. Tool arguments
   support `header_param`, `query_param`, `path_param`, `body_param`.

### Authentication

Incoming requests must include `X-Bkapi-Jwt`. Claims are stored in context and inner JWTs are lazily signed
per tool call using the virtual app code format `v_mcp_{server_id}_{app_code}`.

## Code Conventions

- **Go version**: 1.24.4 (from `go.mod`)
- **Module name**: `mcp_proxy`
- **Max line length**: 120 characters
- **Formatter chain**: golines -> gofumpt -> goimports-reviser (local prefix: `mcp_proxy`)
- **Test framework**: Ginkgo v2 + Gomega (BDD style, `_suite_test.go` convention)
- **Linter**: golangci-lint v2 with `.golangci.yaml` (errcheck disabled; revive + staticcheck enabled)
- **License header**: required for all `.go` files (except `vendor/` and `mock/`)
- **Vendor mode**: use `-mod=vendor`; run `make dep` after changing dependencies
