# MCP Proxy

## Runtime and commands

Run commands from `src/mcp-proxy`. The module is `mcp_proxy`, using the official
`github.com/modelcontextprotocol/go-sdk`. `go.mod` and `Dockerfile` pin Go
1.25.5; `.github/workflows/mcp-proxy.yml` selects Go 1.25. An ignored local
`.envrc` is optional, not a tracked runtime specification.

| Command | Effect |
| --- | --- |
| `make init` | Install local tools, including Ginkgo matched to `go.mod` |
| `make dep` | `go mod tidy` and refresh ignored `vendor/` |
| `make build` / `make serve` | Build `bk-apigateway-mcp-proxy` / run with `config.yaml` |
| `make fmt` / `make lint` | Apply formatters / lint plus license-header check |
| `make test` | Recursive vendor-mode Ginkgo with `.coverage.cov` |
| `make mock` | Run existing `go generate` directives |
| `make integration` | Compose MySQL + mock API + proxy, then protocol specs |
| `make integration-down` | Remove integration containers and volumes |
| `make cov` / `make dev-image` | View coverage / build development image |

For code/config/build changes, run focused specs, `make build`, `make lint`, and
`make test`; report any unavailable gate. Refresh stale/missing vendor data with
`make dep`, reviewing `go.mod`/`go.sum`; never hand-edit vendor files. Examples:

```bash
./bin/ginkgo -r -mod=vendor ./pkg/infra/proxy/...
./bin/ginkgo -r -mod=vendor --focus "Tool Name Mapping" ./pkg/mcp/...
```

Use `make integration` for routing, authentication, tool calls, metrics, request
IDs, or fixture changes when Docker is available. The suite uses host ports
3307/8080/8889; `MCP_PROXY_URL` can point focused integration specs at an existing
proxy. Update `tests/integration/init.sql` alongside changed DB/protocol contracts.
If a failed integration run leaves containers, use `make integration-down`.
The build/unit and integration CI jobs are in `.github/workflows/mcp-proxy.yml`.

## Ownership

- `cmd/` initializes configuration, logs, DB, tracing, Sentry, metrics, and the
  server. `pkg/config` owns defaults/environment overrides and validation.
- `pkg/server` registers HTTP routes; `pkg/middleware` owns HTTP authentication,
  permissions, headers, request IDs, logging, and metrics.
- `pkg/mcp` polls and reconciles server definitions. `pkg/infra/proxy` owns SDK
  handlers, OpenAPI conversion, tool execution, prompts, and response envelopes.
- `pkg/biz` queries through generated `pkg/repo` and `pkg/entity/model` mappings;
  `pkg/cacheimpls` owns cached DB retrieval. Infrastructure is under `pkg/infra`.
- Model contracts originate in Dashboard. Check its MCP models, sync API, and
  gateway definitions when changing consumed fields. `pkg/repo/*.gen.go` is
  generated: update models and run `./bk-apigateway-mcp-proxy gen -c config.yaml`
  against a suitable database instead of hand-editing DAO output.

## Startup and request flow

```text
main.main → cmd.Execute → cmd.Start
  → initConfig → initLogger → initDatabase → initTracing → initBkAIDevTrace
  → initSentry → initMetrics → server.Run → server.NewRouter

HTTP request → Gin default logger/recovery
  → RequestID → Metrics → Sentry recovery → optional OpenTelemetry
  → /:name or /:name/application group
  → APILogger → BkGatewayJWTAuthMiddleware → MCPServerPermissionMiddleware
  → MCPServerHeaderMiddleware → optional BkAIDevTraceContextMiddleware
  → GET/POST /sse or /mcp handler
```

The group middleware chain covers both user and application routes; operational
routes are registered separately in `pkg/server/router.go`.

## Loading and protocol behavior

`pkg/mcp.LoadMCPServer` reconciles definitions in this order:

1. Query active server definitions with `biz.GetAllActiveMCPServers`.
2. Concurrently prefetch each Release and evaluate `checkNeedLoad`; fetch and
   parse its version's OpenAPI spec only when loading is needed. Render the
   gateway/stage endpoint from `BK_API_URL_TMPL` plus `/{stage}`.
3. Apply server additions/updates serially; skipped servers refresh prompts
   without fetching the spec or rebuilding tools.
4. Clean up stale servers and their sessions/cache entries.
5. Call `mcpProxy.Run`.

Prefetch concurrency comes from `mcpServer.maxConcurrentPrefetch` (default 20,
capped at 100).

- No active definitions: clean all servers and corresponding cache entries.
  Removed servers must also shut down active sessions.
- `checkNeedLoad` loads new servers and reloads existing servers when the version,
  protocol, or raw response mode changes, or a desired tool name is absent from
  the current tool set. With those other inputs unchanged, removing tools or
  swapping aliases within the same tool-name set skips reload and only refreshes
  prompts; deselection alone does not remove an already loaded tool.
- Protocol changes recreate the SDK server. Empty stored protocol defaults to
  SSE; Streamable HTTP uses a stateless handler. Keep cross-protocol rejection
  tests in `tests/integration/protocol_cross_test.go` aligned.
- User routes `/:name/sse` and `/:name/mcp`, and their
  `/:name/application/...` variants, share loaded server objects. SSE uses
  separate user/application message URL prefixes; preserve gateway prefix
  stripping when changing `messageUrlFormat` or `messageApplicationUrlFormat`.
- The converter selects operations by original resource name and exposes the
  configured alias. `ArrayString` scans stored names as semicolon-separated;
  prompt extension content is JSON. Keep conversion/loading tests with changes.

## Authentication, calls, and telemetry

- Expired permission is rejected. Incoming `X-Bkapi-Jwt` is verified against the
  official gateway's key; inner JWTs are signed lazily inside tool calls (default
  expiry 5 minutes).
- Header extraction handles `X-Bkapi-Timeout`, `X-Bkapi-Allowed-Headers`, and
  `X-Bkapi-ItsmFlex`; malformed ITSM metadata is ignored.
- [Request ID propagation](docs/request_id_propagation.md) owns the complete ID
  contract. Preserve HTTP-header fallbacks when SDK/session contexts lack
  request or trace values, and keep HTTP/MCP log fields aligned with Dashboard
  search. Successful `tools/call` logs come from the tool handler; middleware
  logs pre-handler failures without duplicating successes.
- Shared outbound transport initializes with `sync.Once`; configuration changes
  after initialization do not reconfigure it. Preserve TLS/timeout behavior.
- MCP tracing injects W3C trace context into outbound calls; BKAIDev tracing is
  separately controlled. Log preview limits are byte-oriented, not rune-safe.
- Metric prefixes must remain compatible with Dashboard's
  `src/dashboard/apigateway/apigateway/service/prometheus/` queries.

## Configuration and test seams

Start from `config.yaml.tpl`; `-c` is required and the database ID `apigateway`
is needed at startup. Important overrides are `BK_API_URL_TMPL`,
`PROMETHEUS_METRIC_NAME_PREFIX`, both `PPROF_USERNAME` and `PPROF_PASSWORD`, and
`BKAI_DEV_TRACE_*`. Verify exact fields/defaults in `pkg/config/config.go`.

Gateway private-key decryption uses `mcpServer.encryptKey` and
`BK_APIGW_CRYPTO_NONCE`. `ENCRYPT_KEY` can populate the config; optional KMS in
`pkg/config/kms.go` overrides that key and DB credentials afterward. With
`ENABLE_KMS=true` or `True`, the envelope `/etc/secrets/bk-apigateway-kms` and
`BK_APIGATEWAY_KMS_PRIVATE_KEY` are required; invalid enabled KMS stops startup.
Do not log secret material or enable insecure TLS for public-network calls.

Use adjacent Ginkgo/Gomega specs and existing `export_test.go` seams. Proxy,
loader, and HTTP middleware suites cover different boundaries; choose the one
owning the change. `.golangci.yaml` owns format rules and the `mcp_proxy` import
prefix. Keep TencentBlueKing license headers and generated-code exclusions.
Version output spans `cmd/version.go`, `pkg/version/version.go`, and Makefile
ldflags. Local config, `vendor/`, tools, coverage, and binaries remain untracked.
