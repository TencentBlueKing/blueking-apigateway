# AGENTS.md

## Scope

This file applies to `src/mcp-proxy`. It overrides the repository root guidance for this subproject.

`mcp-proxy` is the Go service that exposes BlueKing API Gateway resources as Model Context Protocol (MCP)
servers. It reads MCP server definitions, gateway release data, JWT keys, app permissions, and prompt
extensions from the API Gateway database, converts OpenAPI 3.0 operations into MCP tools, and serves both
SSE and Streamable HTTP transports through `github.com/modelcontextprotocol/go-sdk`.

For Markdown-only edits in this directory, run document checks such as `git diff --check`; do not run
`make lint` or `make test` just to change docs. For Go, config, Docker, or test changes, use the Makefile
targets below from `src/mcp-proxy`.

## Runtime And Tooling

- Work from `src/mcp-proxy`, not the monorepo root, when running Go commands.
- `go.mod`, `Dockerfile`, and `.github/workflows/mcp-proxy.yml` are the build/runtime sources of truth and
  currently use Go 1.25.x (`go.mod` and `Dockerfile` say `1.25.5`; CI uses `1.25`).
- `.envrc` and `README.md` still mention Go 1.24.4. Treat that as stale unless the user explicitly asks to
  use the `.envrc` runtime. If verification fails under Go 1.24.4, switch to the Go version required by
  `go.mod`/CI before debugging code.
- `vendor/`, `bin/`, `config.yaml`, `.coverage.cov`, and the built binary are ignored local artifacts. Do
  not edit ignored `vendor/` by hand. Run `make dep` to refresh it when a command uses `-mod=vendor`.
- Local tools are installed into `./bin` by `make init`; prefer those binaries over globally installed
  versions for this subproject.

## Common Commands

```bash
cd src/mcp-proxy

make init              # install ginkgo, golangci-lint, mockgen, gofumpt, golines, goimports-reviser, swag
make dep               # go mod tidy && go mod vendor
make build             # build ./bk-apigateway-mcp-proxy
make serve             # build and run ./bk-apigateway-mcp-proxy -c config.yaml
make fmt               # golangci-lint fmt
make lint              # golangci-lint run plus license-header check
make test              # ginkgo -r -mod=vendor --cover ./...
make mock              # go generate ./...
make integration       # Docker Compose MySQL + mock API + mcp-proxy, then integration Ginkgo suite
make integration-down  # stop and remove integration containers/volumes
make cov               # open .coverage.cov in a browser
make dev-image         # build bk-apigateway-mcp-proxy:development
```

Focused test examples:

```bash
make dep
./bin/ginkgo -r -mod=vendor ./pkg/infra/proxy/...
./bin/ginkgo -r -mod=vendor --focus "Tool Name Mapping" ./pkg/mcp/...
./bin/ginkgo -r -mod=vendor ./tests/integration/...
```

If Go reports `inconsistent vendoring`, the local ignored `vendor/` tree is stale. Run `make dep` and retry.
Use `go list -mod=mod ./...` only for package inventory or dependency investigation when you intentionally
want to bypass local vendor mode.

## CI Shape

`.github/workflows/mcp-proxy.yml` runs on changes under `src/mcp-proxy/**`.

- Build job: `make init`, `make build`, `make lint`, Trivy filesystem scan, then `make dep && make test`.
- Integration job: `make init`, `make dep`, then `make integration`.

Before claiming a code change is ready, run the smallest relevant local gate and report any skipped gate
plainly. For changes touching MCP routing, auth, tool-call behavior, metrics, request IDs, or integration
fixtures, prefer `make integration` when Docker is available.

## Package Map

- `main.go`, `cmd/`: Cobra entrypoint. Startup is config -> logger -> DB -> tracing -> BKAIDev trace ->
  Sentry -> metrics -> HTTP server. `cmd/gen.go` regenerates DAO code from the configured database.
- `pkg/config/`: Viper-backed global config (`config.G`), environment overrides, defaults, DB TLS checks,
  public SSE path-prefix derivation, metric prefix, pprof defaults, and MCP server config.
- `pkg/server/`: Gin router and graceful HTTP shutdown. Registers global middleware, health endpoints,
  pprof, metrics, MCP proxy initialization, and user/application MCP route groups.
- `pkg/mcp/`: MCP server loader/reloader. Polls database rows, prefetches release/spec data concurrently,
  applies changes serially, registers MCP middleware, tools, and prompts, and cleans stale servers/caches.
- `pkg/infra/proxy/`: MCP proxy core. Wraps the official SDK handlers, converts OpenAPI operations into
  MCP tool configs, creates SSE or Streamable HTTP MCP servers, handles tool calls, signs lazy inner JWTs,
  builds response envelopes, and manages prompts.
- `pkg/middleware/`: Gin middleware for request IDs, HTTP API logs, metrics, gateway JWT auth, app
  permission, MCP header extraction, and optional BKAIDev trace context.
- `pkg/cacheimpls/`: In-memory database caches. Gateway/stage/JWT/MCP server caches live for 12h;
  permissions and prompt extensions live for 1m. Cache retrieval is trace-wrapped.
- `pkg/biz/`: Thin query helpers over generated repo code for active MCP servers, releases, OpenAPI specs,
  gateway JWTs, and prompt extensions.
- `pkg/entity/model/`: GORM models for API Gateway tables consumed by this service. MCP-owned tables include
  `mcp_server`, `mcp_server_app_permission`, and `mcp_server_extend`.
- `pkg/repo/`: GORM Gen output. Files ending in `.gen.go` are generated; update the model and regenerate
  instead of hand-editing DAO code.
- `pkg/infra/database`, `pkg/infra/logging`, `pkg/infra/trace`, `pkg/infra/sentry`,
  `pkg/infra/bkaidevtrace`, `pkg/metric`: shared infrastructure used during startup and request handling.
- `pkg/util/`: Context helpers, JWT/private-key utilities, request mutation, response helpers, masking,
  UUIDs, placeholder replacement, and goroutine recovery.
- `tests/integration/`: Docker Compose integration environment, SQL fixtures, test config, and protocol
  suites for SSE, Streamable HTTP, application mode, metrics, permissions, prompts, and request ID/trace
  propagation.

## Request Flow

Startup path:

```text
main.main
  -> cmd.Execute
  -> cmd.Start
  -> config.Load
  -> initLogger/initDatabase/initTracing/initBkAIDevTrace/initSentry/initMetrics
  -> server.Run
  -> server.NewRouter
```

Router path:

```text
Gin global middleware:
  RequestID -> Metrics -> Sentry Recovery -> optional otelgin

Basic routes:
  GET /ping
  GET /healthz
  GET /metrics
  /debug/pprof/* with basic auth when pprof credentials are configured

MCP user routes:
  /:name/sse     GET, POST
  /:name/mcp     GET, POST

MCP application routes:
  /:name/application/sse  GET, POST
  /:name/application/mcp  GET, POST

MCP route middleware:
  APILogger -> BkGatewayJWTAuthMiddleware -> MCPServerPermissionMiddleware
  -> MCPServerHeaderMiddleware -> optional BkAIDevTraceContextMiddleware
```

The user and application route groups share one `MCPProxy` instance and the same loaded MCP server data.
SSE user/application routes derive different public path prefixes from `mcpServer.messageUrlFormat` and
`mcpServer.messageApplicationUrlFormat` so the SDK endpoint works behind a gateway that strips prefixes.
Streamable HTTP is stateless and uses the same handler for user and application routes.

## MCP Loading Flow

`pkg/mcp.LoadMCPServer()` is the central reload path.

1. Query active rows from `mcp_server` (`status = 1`).
2. If no active servers remain, call `MCPProxy.CleanupAll()`, delete MCP server cache entries, and run the
   proxy so the active set matches the empty state.
3. Prefetch each server's current `core_release` and `openapi_gateway_resource_version_spec` concurrently.
   Concurrency is controlled by `mcpServer.maxConcurrentPrefetch`, default `20`, capped at `100`.
4. Skip reload when the server exists and `resource_version_id`, `protocol_type`, selected tool list, and
   `raw_response_enabled` have not changed. Prompts are still refreshed on skipped servers.
5. Build the OpenAPI server URL from `mcpServer.bkApiUrlTmpl` plus `/{stage}` by replacing `{api_name}` and
   `{stage}` from cached gateway/stage rows.
6. Convert OpenAPI operations into MCP tools. `resource_names` filters operation IDs. Entries of the form
   `resource_name@tool_name` rename the MCP tool while still loading the original resource.
7. Create or update the MCP server:
   `protocol_type = sse` uses `mcp.NewSSEHandler`; `protocol_type = streamable_http` uses
   `mcp.NewStreamableHTTPHandler` with `Stateless: true`.
8. Register logging, metrics, session metrics, optional MCP tracing, and optional BKAIDev tracing middleware
   on the SDK server.
9. Load prompts from `mcp_server_extend` rows with `type = prompts` and register/update SDK prompts.
10. Remove stale MCP servers, shut down their active sessions, delete their cache entries, and run the proxy.

## Data Contracts

- `mcp_server.resource_names` is semicolon-separated by the custom `ArrayString` scanner. Tool rename syntax
  is `resource_name@tool_name`.
- `mcp_server.protocol_type` defaults to SSE when empty. Changing the protocol type recreates the server.
- `mcp_server.raw_response_enabled` changes tool-call output shape. When enabled, tool calls return the raw
  API response body instead of the normal envelope with request/trace metadata.
- `mcp_server_app_permission` authorizes `bk_app_code + mcp_server_id`; expired permissions are rejected by
  `MCPServerPermissionMiddleware`.
- `mcp_server_extend` currently supports `type = prompts`, whose `content` is JSON for `[]Prompt`.
- `core_jwt` stores the gateway JWT public/private keys. Encrypted private keys are decrypted with
  `ENCRYPT_KEY` and `BK_APIGW_CRYPTO_NONCE`.
- Dashboard owns the API surfaces that create/sync these rows. When changing these contracts, also inspect
  `src/dashboard/apigateway/apigateway/apps/mcp_server`,
  `src/dashboard/apigateway/apigateway/apis/v2/sync/serializers.py`, dashboard MCP documentation, and the
  gateway resource definitions under
  `src/dashboard/apigateway/apigateway/data/apigw-definitions/`.

## Authentication, Headers, And Logging

- Incoming MCP requests must include `X-Bkapi-Jwt`. The middleware validates it using the official gateway
  public key and stores app/user claims for lazy inner-JWT signing.
- Inner JWT signing happens only inside tool calls. The virtual app code format is
  `v_mcp_{mcp_server_id}_{app_code}` and expiry defaults to 5 minutes.
- `MCPServerHeaderMiddleware` reads `X-Bkapi-Timeout`, `X-Bkapi-Allowed-Headers`, and
  `X-Bkapi-ItsmFlex`; malformed `X-Bkapi-ItsmFlex` is ignored.
- Request ID behavior is documented in `docs/request_id_propagation.md`. Keep that file and this summary
  aligned when changing request ID handling.
- `X-Request-Id` is the full-chain ID and is logged as `x_request_id`.
- `X-Bkapi-Request-ID` is the per-segment gateway ID and is logged as `request_id`; if it is missing,
  mcp-proxy generates a UUID for local logging.
- MCP protocol logs and HTTP API logs intentionally use aligned field names so dashboard log search can
  combine them.
- MCP `tools/call` success logs are emitted by the tool handler, not duplicated by the MCP logging middleware.
  Pre-handler errors for `tools/call` are still logged by middleware.
- Tool-call outbound HTTP uses a shared transport initialized once from `mcpServer.transport`.
- When MCP tracing is enabled, outbound tool calls inject W3C `traceparent`/`tracestate`; BKAIDev tracing is
  independent and controlled by its own config/env vars.

## Config Notes

- A config file is required with `-c`; `make serve` expects local `config.yaml`. Start from `config.yaml.tpl`
  or `tests/integration/config.yaml`.
- `databases` must include an entry with `id: "apigateway"`; startup panics without it.
- `BK_API_URL_TMPL` overrides `mcpServer.bkApiUrlTmpl`.
- `PROMETHEUS_METRIC_NAME_PREFIX` overrides `metric.namePrefix`, default `bk_apigateway_`. Keep metric names
  compatible with dashboard PromQL in `src/dashboard/apigateway/apigateway/service/prometheus/`.
- `PPROF_USERNAME` and `PPROF_PASSWORD` override pprof credentials. Defaults exist in code, but production
  config should set real credentials.
- `BKAI_DEV_TRACE_ENABLE`, `BKAI_DEV_TRACE_ENDPOINT`, `BKAI_DEV_TRACE_SERVICE_NAME`, and
  `BKAI_DEV_TRACE_TOKEN` override the `bkAIDevTrace` config section.
- `mcpServer.logTruncate` sizes are string lengths, not byte counts.
- `mcpServer.transport.insecureSkipVerify` defaults from config. It is acceptable for internal test networks
  but should be false for public network paths.

## Tests

- Unit tests use Ginkgo v2 + Gomega. Each package has a `_suite_test.go`; prefer adding focused specs near
  the code under test.
- Use test-only exports in `export_test.go` when present instead of widening production APIs for tests.
- `pkg/infra/proxy` covers OpenAPI-to-tool conversion, response envelopes, raw response mode, prompt
  registration, protocol-specific handlers, shared transport, tracing, and concurrency.
- `pkg/mcp` covers load/reload decisions, protocol switches, stale cleanup, tool-name mapping, prompt refresh,
  raw-response reloads, and middleware behavior.
- `pkg/middleware` covers gateway JWT, permissions, request IDs, header extraction, metrics, logging, and
  BKAIDev trace context.
- `tests/integration` starts MySQL 8, `mccutchen/go-httpbin`, and mcp-proxy. It binds host ports `3307`,
  `8080`, and `8889`; use `MCP_PROXY_URL` if running tests against another already-started proxy.
- Integration fixture data lives in `tests/integration/init.sql`; update it with the tests when changing DB
  contracts, tool names, prompts, protocol types, or permissions.

## Style And Generated Code

- Keep line length at or below 120 characters.
- Use the configured formatter chain through `make fmt`; local import prefix is `mcp_proxy`.
- All non-generated `.go` files need the TencentBlueKing MIT license header. `make lint` checks this and
  excludes `vendor/` and `/mock/`.
- Generated DAO files are in `pkg/repo/*.gen.go`; do not hand-edit them. Update models and run
  `./bk-apigateway-mcp-proxy gen -c config.yaml` against a suitable database when DAO regeneration is needed.
- `make mock` currently delegates to `go generate ./...`; check for actual `//go:generate` directives before
  assuming it will change files.
- Avoid broad rewrites. This service has load-bearing contracts with dashboard, gateway routes, metrics, and
  log search. Change the smallest package that owns the behavior and add tests at that boundary.

## Common Sharp Edges

- Do not trust the nearest ignored `vendor/` directory. It is local state and may not match `go.mod`.
- Do not silently use Go 1.24.4 from `.envrc` for code verification when `go.mod`/CI require Go 1.25.x.
- `MCPProxy.InitSharedTransport` uses `sync.Once`; config changes after the first initialization will not
  affect the shared transport in the same process.
- SSE and Streamable HTTP are protocol-specific. Cross-protocol access should fail; keep
  `tests/integration/protocol_cross_test.go` aligned when changing routing.
- Application mode routes are not separate server definitions; they share the same loaded MCP server objects.
- Request ID and trace context may be absent from the MCP SDK context after session initialization. Existing
  code falls back to request headers where possible; preserve that behavior when changing MCP middleware or
  tool handlers.
- The version command still contains old core-api wording and the Makefile ldflags target `core/pkg/version`.
  If you work on version/build metadata, inspect `cmd/version.go`, `pkg/version/version.go`, and the Makefile
  together instead of copying the current strings.
