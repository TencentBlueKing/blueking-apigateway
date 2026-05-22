# AGENTS.md

## Project Overview

BlueKing API Gateway Operator is a Kubernetes operator that bridges the Control Plane (BlueKing API Gateway dashboard) and Data Plane (APISIX). It watches for configuration changes in the Control Plane (stored in etcd), transforms them into APISIX-compatible formats, and synchronizes them to the Data Plane.

**Key Design**: This is NOT a traditional Kubernetes CRD-based operator. It primarily uses etcd for both watching Control Plane changes and writing Data Plane configurations.

**Tech Stack**: Go 1.25, Cobra CLI, Gin HTTP framework, etcd v3, Ginkgo/Gomega testing, Zap logging, OpenTelemetry tracing, Prometheus metrics.

## Environment Activation

Activate the Go runtime from the repository root before running Go, lint, or test commands:

```bash
source .envrc
```

The expected runtime is `go1.25.5`, matching the `go.mod` directive. Verify activation with:

```bash
which go
go version
go env GOROOT GOVERSION
```

`which go` and `GOROOT` should both point at the same GVM `go1.25.5` installation. If `.envrc` is missing or activation still leaves a mixed toolchain, stop and ask for the correct runtime setup before running `make lint` or `make test`.

## Common Commands

### Setup and Dependencies
```bash
# Install all development tools (golangci-lint, mockgen, ginkgo, envtest)
make init

# Build the operator binary (output: build/micro-gateway-operator)
make build
```

### Testing
```bash
# Run all unit tests with coverage
make test

# Run integration tests (requires Docker Compose)
make integration

# Run specific test file
bin/ginkgo pkg/core/agent/

# Run tests with verbose output
bin/ginkgo -v pkg/core/committer/
```

### Code Quality
```bash
# Format code
make fmt

# Run linter
make lint
```

### Docker
```bash
# Build Docker image
make docker-build
```

### CLI Commands
```bash
# Run the operator (requires --config flag)
./build/micro-gateway-operator --config config.yaml

# Print version info
./build/micro-gateway-operator version

# List Control Plane resources
./build/micro-gateway-operator list-apigw \
  --config config.yaml \
  --gateway_name <gateway> \
  --stage_name <stage> \
  --write-out json

# List Data Plane (APISIX) resources
./build/micro-gateway-operator list-apisix \
  --config config.yaml \
  --gateway_name <gateway> \
  --stage_name <stage> \
  --write-out yaml

# Get resource count only
./build/micro-gateway-operator list-apigw \
  --config config.yaml \
  --gateway_name <gateway> \
  --stage_name <stage> \
  --count

# Get current release version
./build/micro-gateway-operator list-apigw \
  --config config.yaml \
  --gateway_name <gateway> \
  --stage_name <stage> \
  --current-version

# Filter by resource ID or name
./build/micro-gateway-operator list-apisix \
  --config config.yaml \
  --gateway_name <gateway> \
  --stage_name <stage> \
  --resource_id <id> \
  --resource_name <name>
```

## Architecture Overview

### Core Components

```
pkg/
├── core/               # Core synchronization logic
│   ├── agent/          # EventAgent - watches Control Plane etcd
│   │   └── timer/      # ReleaseTimer - manages per-stage event time windows
│   ├── committer/      # Committer - batches and commits changes
│   ├── synchronizer/   # ApisixConfigSynchronizer - writes to Data Plane etcd
│   ├── registry/       # APIGWEtcdRegistry - Control Plane interface
│   ├── store/          # ApisixEtcdStore - Data Plane interface
│   ├── validator/      # APISIX resource schema validator
│   ├── differ/         # Configuration differ for change detection
│   └── runner/         # EtcdAgentRunner - main orchestrator
├── apis/open/          # HTTP REST API (Gin framework)
│   └── handler/        # API request handlers
├── biz/                # Business logic layer (resource key generation, queries)
├── client/             # HTTP clients (Resource, CoreAPI, Apisix)
├── server/             # HTTP server setup, router registration, auth middleware
├── entity/             # Resource data models (Route, Service, SSL, etc.)
├── config/             # Configuration loader (Viper)
├── constant/           # Constants and resource type definitions
├── leaderelection/     # etcd-based leader election
├── eventreporter/      # Event publishing to Control Plane CoreAPI
├── metric/             # Prometheus metrics definitions
├── logging/            # Structured logging (Zap)
├── trace/              # OpenTelemetry tracing
├── utils/              # Utility functions
│   ├── envx/           # Environment variable handling
│   ├── schema/         # JSON schema validation
│   └── sslx/           # SSL/TLS certificate utilities
└── version/            # Build version info
```

### Execution Flow

1. **main.go** -> **cmd/root.go** defines root command
2. **cmd/init.go** `preRun` hook:
   - `initConfig()` - loads YAML config via Viper
   - `initSentry()` - initializes error reporting
   - `initLog()` - initializes Zap structured logging
   - `initClient()` - initializes Resource, CoreAPI, and Apisix HTTP clients
   - `eventreporter.InitReporter()` - initializes event reporter
3. **cmd/root.go** `rootRun`:
   - `initOperator()` - initializes Synchronizer and Agent globals
   - Sets up graceful shutdown (SIGTERM/SIGINT)
   - `initTracing()` - initializes OpenTelemetry
   - Starts EventReporter
   - Creates and runs **EtcdAgentRunner**
4. **pkg/core/runner/etcd.go** (EtcdAgentRunner):
   - Initializes metrics, etcd clients for Control & Data planes
   - Creates APIGWEtcdRegistry, leader elector, ApisixEtcdStore
   - Creates ApisixConfigSynchronizer, ReleaseTimer, Committer, EventAgent
   - Starts HTTP server, waits for leader election
   - Starts Committer (goroutine) and EventAgent (blocking)

### Data Flow

```
Control Plane (etcd)
  └─ EventAgent watches (via APIGWEtcdRegistry)
     └─ ReleaseTimer batches events per stage (configurable, default 5s)
        └─ Committer receives batch of ReleaseInfo
           └─ Retrieves full config from Control Plane
              └─ Validates & transforms to APISIX format
                 └─ ApisixConfigSynchronizer writes to Data Plane etcd
                    └─ EventReporter reports status to CoreAPI
                       └─ Version probe verifies APISIX loaded new config
```

### Two etcd Instances

1. **Control Plane etcd** (APIGWEtcdRegistry):
   - Contains BlueKing-specific resource definitions
   - Watched by EventAgent for changes
   - Default key prefix: `/bk-gateway-apigw/default` (configurable)

2. **Data Plane etcd** (ApisixEtcdStore):
   - Contains APISIX native configuration
   - Written by ApisixConfigSynchronizer
   - Default key prefix: `/apisix` (configurable)

### etcd Key Structure and Gateway/Stage Mapping

Resources are stored in two etcd instances with distinct key formats. Understanding these formats is critical to avoid prefix-collision bugs.

#### Control Plane etcd Keys

Stage-scoped resources use path-based keys with `/` separators:

```
/{key_prefix}/{api_version}/gateway/{gateway_name}/{stage_name}/{resource_type}/{resource_id}
```

Format constant (`pkg/constant/apisix.go`):
```go
ApigwStageResourcePrefixFormat = "%s/%s/gateway/%s/%s/"
```

Examples:
- Route: `/bk-gateway-apigw/default/v2/gateway/my-gw/prod/route/my-gw.prod.123`
- BkRelease: `/bk-gateway-apigw/default/v2/gateway/my-gw/prod/_bk_release/bk.release.my-gw.prod`

Global resources (e.g., PluginMetadata) use a separate path without gateway/stage:
```
/{key_prefix}/{api_version}/global/{resource_type}/{resource_id}
```

**Prefix safety**: The trailing `/` after `{stage_name}` in `ApigwStageResourcePrefixFormat` ensures that etcd prefix queries for gateway `ab` (prefix `/.../gateway/ab/`) will NOT match keys for gateway `abc` (which live under `/.../gateway/abc/`). The same protection applies to stage names.

#### Data Plane (APISIX) etcd Keys

APISIX resources are stored flat under their resource type:
```
/{key_prefix}/{resource_type_plural}/{resource_id}
```

Examples:
- Route: `/apisix/routes/my-gw.prod.123`
- Service: `/apisix/services/my-gw.prod.456`
- SSL: `/apisix/ssls/my-gw.prod.789`
- PluginMetadata: `/apisix/plugin_metadata/bk-concurrency-limit`

The Data Plane does NOT use gateway/stage in the key path. Instead, resource ownership is determined by the `labels` field inside the JSON value (`labels.gateway.bk.tencent.com/gateway` and `labels.gateway.bk.tencent.com/stage`), matched via exact string comparison — never prefix matching.

#### Key Generation Functions

| Function | Location | Format | Purpose |
|----------|----------|--------|---------|
| `GenStagePrimaryKey` | `pkg/config/config.go` | `bk.release.{gateway}.{stage}` | Stage identifier for Data Plane cache lookup (exact match) |
| `GenResourceIDKey` | `pkg/biz/common.go` | `{gateway}.{stage}.{resourceID}` | Control Plane resource ID |
| `GenApigwResourceNameKey` | `pkg/biz/common.go` | `{gateway}.{stage}.{resourceName}` | Control Plane resource name key (truncated at 100 chars) |
| `GenApisixResourceNameKey` | `pkg/biz/common.go` | `{gateway}-{stage}-{resourceName}` | APISIX resource name key (lowercase, dashes, md5-hashed if >64 chars) |

#### Prefix-Collision Safety Summary

All operations that could theoretically cause prefix collision are protected:

| Layer | Mechanism | Safe? |
|-------|-----------|-------|
| Control Plane etcd queries | Path separator `/` after each segment (`/.../gateway/{gw}/{stage}/`) | Yes — `/ab/` does not match `/abc/` |
| Data Plane cache lookup | Exact string comparison on `GenStagePrimaryKey` result | Yes — `bk.release.ab.prod` ≠ `bk.release.abc.prod` |
| Data Plane etcd put/delete | Exact key operations, no `WithPrefix()` | Yes — per-resource exact key |

### Resource Types

Actively supported (`SupportResourceTypeMap`):
- **Route**: API route definitions (URI, methods, plugins, upstream)
- **Service**: Backend service definitions with upstream config
- **SSL**: TLS certificate configurations
- **PluginMetadata**: Global plugin metadata (global resource, not stage-scoped)

Event-triggering resources (`SupportEventResourceTypeMap`):
- Route, Service, PluginMetadata, BkRelease

Special types:
- **BkRelease** (`_bk_release`): Internal type marking configuration releases, triggers commit

Defined but not actively supported: Upstream, PluginConfig, Consumer, ConsumerGroup, GlobalRule, Proto, StreamRoute.

## Key Concepts

### Event Batching
Changes are NOT processed immediately. EventAgent uses a ReleaseTimer with a configurable time window (default 5 seconds, via `operator.agent_commit_time_window`). Events update per-stage timers, and stages are committed when their timer expires. This reduces load on APISIX.

### Leader Election
Only one operator instance processes changes at a time using etcd-based leader election (via etcd concurrency primitives). Other instances remain as standbys. Essential for multi-instance deployments to prevent duplicate syncs.

### Resource Transformation
Control Plane resources use BlueKing-specific schemas -> Operator transforms -> APISIX native format. Validation ensures only valid APISIX configs are written.

### Stage-based Configuration
Resources are organized by Gateway and Stage (environment). Each stage has its own set of routes, services, and SSL configs. PluginMetadata is the exception - it's a global resource not scoped to a stage.

### Event Reporting
After synchronization, the EventReporter reports status events (ParseConfiguration, ApplyConfiguration, LoadConfiguration) back to the Control Plane CoreAPI. It includes a version probe that waits (default 15s) then checks APISIX to verify the new configuration was loaded (with 2-minute timeout).

## Important Files

**Entry Points**:
- `main.go` - Main entry point
- `cmd/root.go` - Root command definition and operator run logic
- `cmd/init.go` - CLI initialization (config, logging, clients, sentry, tracing)
- `cmd/version.go` - Version command

**Core Logic**:
- `pkg/core/runner/etcd.go` - Main orchestrator (EtcdAgentRunner)
- `pkg/core/agent/agent.go` - Event watching and batching
- `pkg/core/agent/init.go` - Agent configuration (commit time window)
- `pkg/core/agent/timer/` - ReleaseTimer for per-stage event windowing
- `pkg/core/committer/committer.go` - Commit logic with retry
- `pkg/core/synchronizer/synchronizer.go` - APISIX etcd writer
- `pkg/core/differ/` - Configuration diff computation
- `pkg/core/registry/` - Control Plane etcd registry
- `pkg/core/store/` - Data Plane etcd store
- `pkg/core/validator/` - APISIX resource schema validator

**HTTP Server**:
- `pkg/server/server.go` - HTTP server setup
- `pkg/server/router.go` - Route registration with BasicAuth middleware
- `pkg/apis/open/router.go` - API route definitions
- `pkg/apis/open/handler/` - API request handlers

**Business Logic**:
- `pkg/biz/apigw.go` - Control Plane query logic
- `pkg/biz/apisix.go` - Data Plane query logic
- `pkg/biz/common.go` - Resource key generation utilities

**Resource Models**:
- `pkg/entity/entity.go` - Resource structures (Route, Service, SSL, PluginMetadata, etc.)
- `pkg/constant/apisix.go` - Resource type constants and supported type maps

**Configuration**:
- `pkg/config/config.go` - Configuration structure and defaults

**Event Reporting**:
- `pkg/eventreporter/reporter.go` - Event publishing with version probe

**Debug Tools**:
- `cmd/list_apigw.go` - Query Control Plane resources
- `cmd/list_apisix.go` - Query Data Plane resources

## Configuration File Structure

```yaml
debug: false

http_server:
  bind_address: ""
  bind_address_v6: ""           # IPv6 support
  bind_port: 6004
  auth_password: "DebugModel@bk"  # BasicAuth password for API access

dashboard:
  etcd:
    endpoints: "etcd1:2379"
    key_prefix: "/bk-gateway-apigw/default"
    ca_cert: ""
    cert: ""
    key: ""
    username: ""
    password: ""
    without_auth: false

operator:
  default_gateway: "-"
  default_stage: "global"
  agent_events_waiting_time_window: 2s
  agent_force_update_time_window: 10s
  agent_commit_time_window: 5s          # Event batching window
  agent_concurrency_limit: 4
  etcd_put_interval: 50ms
  etcd_del_interval: 16s
  etcd_sync_timeout: 60s
  commit_resource_chan_size: 100
  watch_event_chan_size: 100

apisix:
  etcd:
    endpoints: "apisix-etcd:2379"
    key_prefix: "/apisix"
  virtual_stage:
    virtual_gateway: "-"
    virtual_stage: "-"
    extra_apisix_resources: ""
    file_logger_log_path: "/usr/local/apisix/logs/access.log"

auth:
  id: ""
  secret: ""

eventreporter:
  core_api_host: ""
  apisix_host: ""
  event_buffer_size: 300
  reporter_buffer_size: 100
  version_probe:
    buffer_size: 100
    retry:
      count: 60
      interval: 1s
    timeout: 2m
    wait_time: 15s

logger:
  default:
    level: "info"
    writer: "os"
    settings:
      name: "stdout"
  controller:
    level: "info"
    writer: "os"
    settings:
      name: "stdout"

sentry:
  dsn: ""
  report_level: 2

tracing:
  enable: false
  type: ""
  endpoint: ""
  token: ""
  sampler: ""
  sampler_ratio: 0
  service_name: ""
```

## HTTP API Endpoints

All `/v1/open/*` endpoints require BasicAuth (account: `bk-apigateway`, password from `httpServer.authPassword` config).

- **GET /ping** - Health check
- **GET /healthz** - Health check
- **GET /v1/open/leader/** - Get current leader info
- **POST /v1/open/apigw/resources/** - List Control Plane resources
- **POST /v1/open/apigw/resources/count/** - Get Control Plane resource count
- **POST /v1/open/apigw/resources/current-version/** - Get Control Plane current version
- **POST /v1/open/apisix/resources/** - List Data Plane resources
- **POST /v1/open/apisix/resources/count/** - Get Data Plane resource count
- **POST /v1/open/apisix/resources/current-version/** - Get Data Plane current version
- **GET /metrics** - Prometheus metrics
- **GET /debug/pprof/** - Go profiling endpoints (requires BasicAuth)

## Prometheus Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `leader_election_info` | Gauge | hostname | Whether agent is leader |
| `resource_event_triggered_count` | Counter | gateway, stage, type | Event trigger count |
| `resource_converted_count` | Counter | gateway, stage, type | Resource conversion count |
| `sync_cmp_count` | Counter | gateway, stage, type | Compare operation count |
| `sync_cmp_diff_count` | Counter | gateway, stage, type | Compare diff count |
| `synchronizer_event_count` | Counter | gateway, stage | Synchronizer event count |
| `synchronizer_flushing_count` | Counter | gateway, stage, result | Flush operation count |
| `synchronizer_flushing_histogram` | Histogram | gateway, stage, result | Flush latency distribution |
| `apisix_resource_written_count` | Counter | gateway, stage, type | Resources written to APISIX |
| `apisix_operation_count` | Counter | type, action, result | APISIX operation count |
| `apisix_operation_histogram` | Histogram | type, action, result | APISIX operation latency |
| `registry_action_count` | Counter | type, action, result | Registry action count |
| `registry_action_histogram` | Histogram | type, action, result | Registry action latency |

## Testing Strategy

- **Unit tests**: Use Ginkgo/Gomega BDD framework
- **Mocks**: Generated with mockgen in `*_mock.go` files
- **Integration tests**: Docker Compose setup in `tests/integration/`
- **envtest**: For controller-runtime based tests

When writing tests:
- Use `BeforeEach` for test setup
- Use descriptive `Describe`, `Context`, `It` blocks
- Mock external dependencies (etcd, HTTP clients)
- Test both success and error paths

## Debugging

### Check Sync Status
```bash
# Compare Control Plane vs Data Plane resources
./build/micro-gateway-operator list-apigw --config config.yaml --gateway_name <gateway> --stage_name <stage> > apigw.json
./build/micro-gateway-operator list-apisix --config config.yaml --gateway_name <gateway> --stage_name <stage> > apisix.json
diff apigw.json apisix.json
```

### Logs
- Structured JSON logs with Zap
- Key fields: `gateway_name`, `stage_name`, `resource_type`, `event_type`
- Named loggers: `setup`, `etcd-agent-runner`, `event-agent`, `committer`, `synchronizer`

### Metrics
- Prometheus metrics exposed at `/metrics`
- Key metrics: sync latency, error counts, event trigger counts

### Tracing
- OpenTelemetry traces show full request flow
- Traces include: event receipt -> transformation -> validation -> etcd write

## Common Issues

### Resources Not Syncing
1. Check if operator is the leader: `curl -u admin:<password> http://operator:6004/v1/open/leader/`
2. Check logs for validation errors
3. Compare Control Plane vs Data Plane with CLI tools
4. Verify etcd connectivity and permissions

### Leader Election Not Working
- Ensure multiple instances can reach the same etcd
- Check etcd lease TTL settings
- Look for "leader election" in logs

### Performance Issues
- Check event queue sizes (metrics)
- Adjust `commit_resource_chan_size` and `watch_event_chan_size` in config
- Adjust `agent_commit_time_window` for batching behavior
- Check `agent_concurrency_limit` for parallel processing

## Development Workflow

1. Make changes to code
2. Run `make fmt` and `make lint`
3. Run `make test` for unit tests
4. Build with `make build`
5. Test locally or run `make integration`
6. Commit changes with descriptive message
7. Create PR following CONTRIBUTING guidelines

## After Code Changes

Always run `make lint` and `make test` after making code changes and fix any issues before considering the work done.

When asked to "make a PR", create the pull request targeting `upstream/master`.

## Related Projects

- **Control Plane**: https://github.com/TencentBlueKing/blueking-apigateway
- **Data Plane (APISIX)**: https://github.com/TencentBlueKing/blueking-apigateway-apisix
