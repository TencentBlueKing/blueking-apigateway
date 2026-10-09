# Operator

## Runtime and verification

Run commands from `src/operator`. This is the standalone etcd synchronization
service (module `operator`), using Go 1.25.5 in `go.mod`, `Dockerfile`, and
`.github/workflows/operator.yaml`. An ignored local `.envrc` is optional.

| Command | Effect |
| --- | --- |
| `make init` | Install pinned tools into ignored `bin/` |
| `make build` | Build `build/micro-gateway-operator` with Git/version ldflags |
| `make fmt` / `make lint` | Apply formatters / run golangci-lint **with fixes** |
| `make test` | Ginkgo unit suites, excluding vendor and integration; `cover.out` |
| `make docker-build` | Build the development image |
| `make integration` | Build image, start Compose stack, run integration specs, tear down |

For Go/config/Docker/CI changes, run affected package tests followed by
`make fmt`, `make lint`, and `make test`; inspect resulting edits. For example:

```bash
bin/ginkgo -v pkg/core/committer
bin/ginkgo -v --focus "ForceCommit" pkg/core/committer
```

Also run `make integration` for runtime wiring, real etcd watch/sync, version
probing, Docker startup, or fixture changes. It requires Docker Compose and
uses `tests/integration/docker-compose.yml`. Read command output: the current
recipe ends with cleanup, so its exit status alone does not prove specs passed.
Keep `bin/`, `build/`, coverage, and local `config.yaml` uncommitted.

## Runtime path

Startup enters `cmd/root.go`/`cmd/init.go`; `pkg/core/runner/etcd.go` wires the
control-plane client, leader election, APISIX cached store, timer, committer,
watcher, and HTTP server. The store initially lists each APISIX resource type,
then watches incremental changes. Only the elected leader runs the commit/watch
processing path.

| Package under `pkg/` | Responsibility |
| --- | --- |
| `core/registry` | List/watch control-plane and data-plane etcd |
| `core/agent` and `core/agent/timer` | Interpret watch events and coalesce releases |
| `core/committer` | Read full target config, validate schemas, retry and report parse/apply events |
| `core/synchronizer` | Bound stage synchronization and serialize global updates |
| `core/store` and `core/differ` | Compare cached APISIX state and write/delete keys |
| `eventreporter` | Report events to CoreAPI and probe APISIX loading |
| `entity`, `constant`, `biz` | Resource representations, key formats, ID/name helpers |

## Watch and process flow

The coalesced watch path branches by stage/global scope:

```text
control-plane etcd → APIGWEtcdRegistry.Watch → EventAgent.Run
  → ReleaseTimer.Update / ListReleaseForCommit → commitChan → Committer.Run
    stage  → ListStageResources → SyncRelease → AlterStage
    global → ListGlobalResources → SyncGlobal → AlterGlobal
                                             → AlterVirtualStage
```

Registry listing calls `ValidateApisixJsonSchema`; synchronizer methods call
the store, whose `ConfigDiffer` compares cached state before APISIX etcd
put/delete operations. Stage commits report parse/apply milestones and delegate
the load probe to `eventreporter` after successful sync. Global commits update
plugin metadata and the virtual stage without the stage event/probe lifecycle.
Delete-release markers go directly to `commitChan`, bypassing the timer.

## Watch, concurrency, and write contracts

- `APIGWEtcdRegistry.Watch` uses a trailing-slash prefix, previous values, leader
  requirement, and cached revision. Broken watches retry; compacted/future
  revisions terminate that watcher and require full-sync recovery. Preserve
  cancellation and restart behavior when editing `core/registry/apigw.go`.
- `SupportEventResourceTypeMap` accepts `route`, `service`, `plugin_metadata`,
  and `_bk_release`. Raw non-global DELETE events are skipped; stage deletion
  uses the release-marker PUT contract. Metadata extraction needs valid labels.
- `ReleaseTimer` uses waiting and force-update windows. `_bk_release` non-delete
  events flush ready work without inserting a timer entry themselves. Global
  plugin metadata uses `global_resource`.
- Commits serialize stages of the same gateway with `gatewayStageChanMap`;
  different gateways can proceed concurrently. Parse/sync failures requeue up
  to `maxStageRetryCount`. After successful sync, the reporter owns releasing
  the stage-channel token, including skipped reports and probe failures.
- `operator.gatewaySyncConcurrency` bounds concurrent stage syncs; each slot is
  held through writes and configured delays. Global sync waits for stage syncs
  and runs exclusively. `agentConcurrencyLimit` is not the active limiter.
- Store entrypoints are `AlterStage`, `AlterVirtualStage`, and `AlterGlobal`.
  Preserve release context and the distinct virtual-stage path.
- Put order: SSL → Service → `etcdPutInterval` delay → Route. Delete order:
  Route → SSL → `etcdDelInterval` delay → Service. The corresponding delay is
  applied whenever the put diff is nonnil (including empty route sets), while
  the delete delay requires service deletes. Do not remove them as dead time.
- Global sync writes plugin metadata and refreshes the virtual stage with its
  default 404, outer health-check, root HEAD, and configured extra resources.
- The APISIX load probe targets `/api/:gateway/:stage/__apigw_version`. A completed
  etcd write alone does not establish loading success.

Tests for this path should cover watch recovery, timer coalescing, per-gateway
serialization, channel ownership, retry limits, write ordering, version/schema
selection, and virtual-stage updates as applicable to the change.

## Keys and supported resources

`pkg/constant` defines the formats (prefixes below already include the leading
slash):

```text
{dashboard.etcd.keyPrefix}/{apiVersion}/gateway/{gateway}/{stage}/{resourceType}/{resourceID}
{dashboard.etcd.keyPrefix}/{apiVersion}/global/{resourceType}/{resourceID}
{apisix.etcd.keyPrefix}/{routes|services|ssls|plugin_metadata}/{resourceID}
```

Stage output supports routes/services/SSLs; global output supports plugin
metadata. Constants naming other kinds do not mean `SupportResourceTypeMap`
accepts them. Preserve trailing separators in stage prefixes to avoid matching
neighboring gateway names. Use existing `pkg/biz` ID/name helpers so truncation
and hash suffixes remain compatible.

## Configuration and operations

- Start with `config.yaml.tpl`; field names, defaults, and normalization are
  defined in `pkg/config/config.go`. Validate both when changing configuration.
- `dashboard.etcd` is the source; `apisix.etcd` is the target. Keep their clients,
  key prefixes, timeouts, and credentials distinct. Timing knobs include agent
  batching, put/delete intervals, and `eventReporter.versionProbe`.
- `pkg/server` exposes `/ping`, `/healthz`, and metrics. Debug/open APIs use
  BasicAuth account `bk-apigateway` with `httpServer.authPassword`; routes live
  in `pkg/apis/open` and server registration.
- Run `./build/micro-gateway-operator --config config.yaml` after building.
  Its `list-apigw`/`list-apisix` subcommands discover the leader via the local
  endpoint, then query that instance. See their Cobra flags before use.
- `pkg/utils/groutine.go` recovers goroutine panics and uses
  `sentry.CaptureMessage`. Keep cancellation and channel release explicit;
  recovery does not complete interrupted work.
- `.golangci.yaml` owns style/import rules (local prefix `operator`). Build
  metadata comes from the Makefile and `pkg/version`; Docker build args carry
  version/commit into a context that may lack Git metadata.
