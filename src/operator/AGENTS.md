# AGENTS.md

This file applies to `src/operator`. It is a monorepo subproject, so run operator commands from this
directory unless a command explicitly says otherwise.

## Project Overview

BlueKing API Gateway Operator is a Go service that watches BlueKing API Gateway control-plane resources
in etcd and keeps APISIX data-plane etcd in sync. It is called an operator, but it is not a Kubernetes CRD
reconciliation loop. The hot path is etcd watch, release timer, committer, APISIX etcd diff/write, and
publish event reporting.

Key technologies:

- Go module: `operator`
- Go version: `1.25.5`
- CLI: Cobra and Viper
- HTTP server: Gin
- Storage/watch: etcd v3
- Tests: Ginkgo and Gomega
- Logs/tracing/metrics: Zap, OpenTelemetry, Prometheus

The current code reads APISIX-native resource JSON from control-plane etcd, validates it against APISIX
schema, and writes APISIX-native resources to data-plane etcd. Do not describe the runtime path as a
dashboard-model-to-APISIX conversion layer unless the code changes to add that layer.

## Environment

Use Go `1.25.5`, matching `go.mod`, `Dockerfile`, and `.github/workflows/operator.yaml`.

```bash
cd src/operator

# Optional local helper. This file is ignored by git, so it may not exist in clean clones.
if [ -f .envrc ]; then source .envrc; fi

go version
go env GOVERSION GOROOT
```

Do not source the repository-root `.envrc` for operator work. In this monorepo that file may activate the
dashboard Python environment, not the operator Go toolchain.

Install local development tools into `src/operator/bin`:

```bash
make init
```

`make init` installs `golangci-lint`, `mockgen`, `ginkgo`, `gci`, and `setup-envtest`. The generated
`bin/`, `build/`, `cover.out`, and local `config.yaml` files are ignored runtime artifacts.

## Common Commands

```bash
cd src/operator

# Build build/micro-gateway-operator
make build

# Format. This uses golangci-lint formatters and can modify files.
make fmt

# Lint. This runs golangci-lint with --fix and can modify files.
make lint

# Unit tests. Skips tests/integration and writes cover.out.
make test

# Run one package
bin/ginkgo -v pkg/core/committer

# Focus one Ginkgo spec
bin/ginkgo -v --focus "ForceCommit" pkg/core/committer

# Build image bk-micro-gateway-operator:development
make docker-build

# Docker Compose integration suite
make integration
```

`make integration` builds the Docker image, starts `tests/integration/docker-compose.yml`, runs the
integration Ginkgo suite, and tears the stack down. It requires Docker Compose, either `docker compose`
or `docker-compose`.

## Runtime Architecture

Important entry points:

- `main.go`: calls `cmd.Execute()`.
- `cmd/root.go`: root Cobra command, graceful shutdown, reporter start, runner creation.
- `cmd/init.go`: config load, Sentry, logging, clients, reporter, tracing, global synchronizer and timer config.
- `pkg/core/runner/etcd.go`: constructs the runtime graph and runs HTTP server, leader election, committer, and watcher.
- `pkg/core/registry/apigw.go`: watches and lists control-plane etcd resources.
- `pkg/core/agent/agent.go`: consumes watch events and updates the release timer.
- `pkg/core/agent/timer/timer.go`: batches release work per stage or global resource.
- `pkg/core/committer/committer.go`: reads full target config, retries failures, and sends work to the synchronizer.
- `pkg/core/synchronizer/synchronizer.go`: limits concurrent gateway sync operations and serializes global syncs.
- `pkg/core/store/store.go`: diffs cached APISIX resources and writes/deletes data-plane etcd keys.
- `pkg/eventreporter/reporter.go`: reports publish lifecycle events to CoreAPI and probes APISIX load status.
- `pkg/server/*` and `pkg/apis/open/*`: debug and list APIs.

`EtcdAgentRunner` wires the process in this order:

1. Create the control-plane etcd client from `dashboard.etcd`.
2. Create `APIGWEtcdRegistry` with `dashboard.etcd.keyPrefix` and `operator.watchEventChanSize`.
3. Create the etcd leader elector under `<dashboard keyPrefix>-leader-election`.
4. Create the data-plane APISIX etcd store from `apisix.etcd`.
5. Initialize one cached `ApisixEtcdRegistry` per APISIX resource type: `routes`, `services`, `ssls`,
   and `plugin_metadata`.
6. Create `ApisixConfigSynchronizer`, `ReleaseTimer`, `Committer`, and `EventAgent`.
7. Start the HTTP server.
8. Wait to become leader.
9. Start the committer goroutine.
10. Run the event agent in the foreground.

The APISIX store performs a full sync on startup and then starts incremental watches for each APISIX
resource type. The committer uses this local cache as the old state for diffing before it writes
data-plane etcd.

## Watch And Process Flow

The watch path is the most load-bearing part of this project. Read these files together before changing it:
`pkg/core/registry/apigw.go`, `pkg/core/agent/agent.go`, `pkg/core/agent/timer/timer.go`,
`pkg/core/committer/committer.go`, `pkg/core/synchronizer/synchronizer.go`, `pkg/core/store/store.go`,
and `pkg/eventreporter/reporter.go`.

Process flow:

```text
control-plane etcd
  -> APIGWEtcdRegistry.Watch()
  -> EventAgent.Run()
  -> ReleaseTimer.Update() / ListReleaseForCommit()
  -> Committer.Run()
  -> ListStageResources() or ListGlobalResources()
  -> ValidateApisixJsonSchema()
  -> ApisixConfigSynchronizer.Sync() or SyncGlobal()
  -> ApisixEtcdStore.Alter() or AlterGlobal()
  -> ConfigDiffer
  -> data-plane APISIX etcd put/delete
  -> EventReporter lifecycle events and APISIX version probe
```

Watch details:

- `APIGWEtcdRegistry.Watch()` watches `strings.TrimSuffix(keyPrefix, "/") + "/"` with `WithPrefix()`,
  `WithPrevKV()`, `WithRequireLeader()`, and `WithRev(currentRevision)`.
- Watch channel breaks and most etcd watch errors are retried from `currentRevision` after a sleep.
  `ErrCompacted` and `ErrFutureRev` are treated as unrecoverable in the control-plane watcher.
- `extractResourceMetadata()` derives resource kind from the second-last key segment. The event path only
  supports `route`, `service`, `plugin_metadata`, and `_bk_release`.
- Raw etcd DELETE events for non-global resources are skipped because their previous value can carry stale release info.
- `plugin_metadata` is the current global resource. It has no stage label and uses the timer key `global_resource`.
- A delete-stage release is represented by a `_bk_release` PUT whose publish id is `-2`, not by a raw etcd DELETE.

Timer details:

- `agent.Init()` sets the ticker interval from `operator.agentCommitTimeWindow`, default `5s`.
- `timer.Init()` sets `eventsWaitingTimeWindow`, default `2s`, and `forceUpdateTimeWindow`, default `10s`.
- `ReleaseTimer.Update()` stores the latest release info for a stage. Normal stage keys are
  `bk.release.<gateway>.<stage>`. Global plugin metadata uses `global_resource`.
- `ListReleaseForCommit()` emits a release when the waiting window has expired or the force-update window is exceeded.
- A `_bk_release` non-delete event calls `handleTicker()` immediately. It does not itself add a new timer entry.

Commit details:

- `Committer.Run()` consumes lists from `commitResourceChan`, chunks them into groups of 10, and calls
  `commitGroup()`.
- Stage commits are serialized per gateway with `gatewayStageChanMap`. Different gateways can proceed concurrently.
- `commitStage()` owns parse/apply event reporting and hands the gateway-stage channel token to
  `ReportLoadConfigurationResultEvent()` after a successful sync. Do not add an extra receive on that
  channel after calling the reporter.
- Parse failures and sync failures call `retryStage()`, which re-adds the release to the timer up to
  `maxStageRetryCount` of 3.
- Global resources go through `commitGlobalResource()`, `ListGlobalResources()`, and `SyncGlobal()`.
  They do not use the stage publish-event lifecycle.

Sync details:

- `ApisixConfigSynchronizer` limits concurrent Stage syncs with `operator.gatewaySyncConcurrency`. The
  Committer still serializes stages of the same gateway, so each active slot represents one gateway in the
  production path. A slot is held for the complete Stage sync, including put/delete intervals.
- Global resource syncs remain exclusive with Stage syncs. They do not consume gateway synchronization slots,
  but wait for active Stage syncs to finish before updating global resources and the virtual Stage.
- `ApisixEtcdStore.Alter()` diffs the target stage config against the cached APISIX state.
- Put order is SSL, Service, sleep `operator.etcdPutInterval`, then Route.
- Delete order is Route, SSL, sleep `operator.etcdDelInterval`, then Service.
- `SyncGlobal()` writes global `plugin_metadata` and then refreshes the virtual stage.
- The virtual stage always adds the default 404 handler, outer `/healthz` GET route, and root HEAD route.
  It can also load extra routes/services/SSLs from `apisix.virtualStage.extraApisixResources`.

Event reporting details:

- `eventreporter.Start()` drains an event queue and reports to CoreAPI with bounded concurrency.
- `ReportLoadConfigurationResultEvent()` waits `versionProbe.waitTime`, probes APISIX
  `/:gateway/:stage/__apigw_version`, and reports load success or failure.
- Publish ids `""`, `-1`, and `-2` do not need report events.
- `ReportLoadConfigurationResultEvent()` releases the gateway-stage channel token in all branches.
  Keep this ownership clear when editing commit or probe code.

## Resource And Key Contracts

Control-plane stage resources:

```text
/{dashboard.etcd.keyPrefix}/{apiVersion}/gateway/{gateway}/{stage}/{resourceType}/{resourceID}
```

Control-plane global resources:

```text
/{dashboard.etcd.keyPrefix}/{apiVersion}/global/{resourceType}/{resourceID}
```

Data-plane APISIX resources:

```text
/{apisix.etcd.keyPrefix}/routes/{resourceID}
/{apisix.etcd.keyPrefix}/services/{resourceID}
/{apisix.etcd.keyPrefix}/ssls/{resourceID}
/{apisix.etcd.keyPrefix}/plugin_metadata/{resourceID}
```

Do not infer APISIX stage ownership from the data-plane key path. Data-plane resources are flat under their
resource type, and stage ownership comes from labels:

- `gateway.bk.tencent.com/gateway`
- `gateway.bk.tencent.com/stage`
- `gateway.bk.tencent.com/publish-id`
- `gateway.bk.tencent.com/apisix-version`

Supported runtime resources:

- Watch-triggering resources: `route`, `service`, `plugin_metadata`, `_bk_release`.
- Stage resources written to APISIX: routes, services, SSLs.
- Global resources written to APISIX: plugin metadata.
- Other APISIX kinds are defined in constants but currently unsupported by `SupportResourceTypeMap`.

Key helpers:

- `config.GenStagePrimaryKey(gateway, stage)`: `bk.release.<gateway>.<stage>`.
- `biz.GenResourceIDKey(gateway, stage, id)`: `<gateway>.<stage>.<id>`.
- `biz.GenApigwResourceNameKey(gateway, stage, name)`: `<gateway>.<stage>.<name>`, truncated at 100 chars.
- `biz.GenApisixResourceNameKey(gateway, stage, name)`: lower dash-case, max 64 chars with hash suffix.

The trailing slash in `constant.ApigwStageResourcePrefixFormat` is intentional. Preserve it to avoid prefix
collisions such as gateway `ab` matching gateway `abc`.

## HTTP And CLI Surface

Unauthenticated:

- `GET /ping`
- `GET /healthz`
- `GET /metrics`

BasicAuth-protected with account `bk-apigateway` and password `httpServer.authPassword`:

- `GET /debug/pprof/*`
- `GET /v1/open/leader/`
- `POST /v1/open/apigw/resources/`
- `POST /v1/open/apigw/resources/count/`
- `POST /v1/open/apigw/resources/current-version/`
- `POST /v1/open/apisix/resources/`
- `POST /v1/open/apisix/resources/count/`
- `POST /v1/open/apisix/resources/current-version/`

Debug CLI examples after `make build`:

```bash
./build/micro-gateway-operator --config config.yaml
./build/micro-gateway-operator version

./build/micro-gateway-operator list-apigw \
  --config config.yaml \
  --gateway_name <gateway> \
  --stage_name <stage> \
  --write-out json

./build/micro-gateway-operator list-apisix \
  --config config.yaml \
  --gateway_name <gateway> \
  --stage_name <stage> \
  --count
```

`list-apigw` and `list-apisix` first call the local leader endpoint, derive the leader host from
`<podName>_<podIP>`, and then query the leader instance.

## Configuration Notes

Use `config.yaml.tpl` as the sample, but verify field names against `pkg/config/config.go` when adding new
config. The sample mostly uses camelCase keys such as `defaultGateway`, `etcdPutInterval`,
`versionProbe.waitTime`, and `httpServer.authPassword`.

Important defaults from `newDefaultConfig()`:

- `httpServer.bindPort`: `6004`
- `dashboard.etcd.keyPrefix`: `/bk-gateway-apigw/default`
- `apisix.etcd.keyPrefix`: `/apisix`
- `operator.agentEventsWaitingTimeWindow`: `2s`
- `operator.agentForceUpdateTimeWindow`: `10s`
- `operator.agentCommitTimeWindow`: `5s`
- `operator.gatewaySyncConcurrency`: `5`
- `operator.etcdPutInterval`: `50ms`
- `operator.etcdDelInterval`: `16s`
- `operator.etcdSyncTimeout`: `60s`
- `operator.commitResourceChanSize`: `100`
- `operator.watchEventChanSize`: `100`
- `eventReporter.versionProbe.waitTime`: `15s`
- `eventReporter.versionProbe.timeout`: `2m`

`operator.agentConcurrencyLimit` is loaded into config but is not currently used by the runtime path. Do not
document it as the active commit concurrency control unless code starts using it.

## Testing Instructions

Unit tests live beside packages as `*_test.go` and use Ginkgo/Gomega. Integration tests live under `tests/integration`.

Run the narrowest useful test first:

```bash
cd src/operator
bin/ginkgo -v pkg/core/agent
bin/ginkgo -v pkg/core/agent/timer
bin/ginkgo -v pkg/core/committer
bin/ginkgo -v pkg/core/registry
bin/ginkgo -v pkg/core/store
bin/ginkgo -v pkg/core/synchronizer
```

Then run the relevant gate:

```bash
make test
```

Use `make integration` when changes touch Docker startup, real etcd watch behavior, the runner, APISIX store
sync, publish/version probing, or integration fixtures.

When adding tests for the watch/process path, cover intent, not only lines:

- watch recovery and metadata extraction for control-plane etcd keys
- timer coalescing, force update, and global-resource keys
- stage commit serialization per gateway
- `stageChan` release ownership between committer and event reporter
- retry behavior after parse or sync failure
- APISIX diff put/delete order
- schema validation for APISIX version and resource kind
- virtual stage resources after global sync

## Code Style

- Follow the local module path `operator`.
- Keep imports formatted by `gci` with sections `standard`, `default`, and `prefix(operator)`.
- Keep lines at or below 120 chars.
- Package comments and exported identifiers are enforced by revive.
- Prefer `any` over `interface{}`; the formatter has rewrite rules for this.
- `make lint` runs with `--fix`, so always inspect `git diff` afterward.
- Do not clean unrelated lint findings or generated runtime artifacts.
- Keep panic recovery, channel ownership, and context cancellation explicit in concurrent code.

## Sharp Edges

- This subproject was imported into a monorepo. CI and GitHub Actions must use
  `working-directory: src/operator` and Go cache paths such as `src/operator/go.sum`.
- The Docker build runs from `src/operator` and `make build` uses `git describe` and `git rev-parse HEAD`
  for ldflags. Be careful when changing Docker context or release builds because missing `.git` metadata
  changes version output.
- `GoroutineWithRecovery()` currently reports panics through `sentry.CurrentHub().Client()`. If Sentry is
  disabled or error handling changes, guard this path before relying on it.
- `ResourceMetadata.GetReleaseInfo()` assumes labels are present. Tests or manual fixtures that construct
  metadata directly must set labels unless they are intentionally testing nil-label behavior.
- `config.yaml.tpl` should not be treated as proof that every key is wired correctly. Cross-check with
  `pkg/config/config.go` before changing config docs or defaults.

## Completion Requirements

For Markdown-only changes in this directory, do not run `make lint` or `make test`; verify by reviewing the
rendered Markdown or relevant diff.

For Go, Docker, CI, or config changes, run from `src/operator`:

```bash
make fmt
make lint
make test
```

Add `make integration` when the change affects runtime wiring, etcd watch/sync behavior, Docker startup, or
integration fixtures.

When asked to create a PR for this repository, target `upstream/master` unless the user names a different base branch.
