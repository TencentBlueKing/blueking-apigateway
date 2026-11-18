# Controller Layer Guide

## Publish Pipeline

The normal gateway publication path is:

```text
biz/release -> controller/tasks -> GatewayResourceDistributor
            -> GatewayApisixResourceTransformer
            -> ServiceConvertor + RouteConvertor -> EtcdRegistry
```

- `release_data.py` materializes the release input consumed by conversion.
- `transformer.py` coordinates APISIX resource conversion.
- `convertor/` builds native Services, Routes and release markers. SSL/proto
  conversion remains unimplemented in the gateway transformer; do not infer support
  from model/convertor names.
- `distributor/` owns registry selection and synchronization.
- `tasks/` and `publisher/` own asynchronous publication, revoke, and lifecycle
  entrypoints.

Controller code consumes domain state and emits data-plane configuration. It
does not own Web DTOs, API response compatibility, normalized persistence
models, or general-purpose domain workflows.

### Distribution and failure contracts

- The transformer accumulates converted resources in memory. Distribution starts
  registry synchronization only after transformation succeeds. This ordering does
  not promise atomic etcd synchronization.
- Preserve event transitions and existing tuple/exception failure contracts:
  distributor failures can return `(False, message)` for the task to handle.

## Conversion boundaries

- Keep standard Service/Route behavior stable when adding AI branches.
- Apply provider endpoint overrides, remove storage-only fields and convert
  timeout seconds to milliseconds at publication, rather than in storage or DTOs.
- Generate system-managed AI/OAuth2 plugins from controller state; resource
  bindings cannot be their source. Plugin ownership sets live in
  `service/plugin/compatibility.py`.
- Stage bindings are permissive at validation. AI Service compilation filters
  them through `AI_COMPATIBLE_PLUGIN_CODES`; skipped-plugin warnings contain
  type codes only.
- Use `apps/data_plane/constants.py` for AI APISIX version compatibility.
  Preserve publish-only checks and revoke bypasses, propagating `revoke_flag`
  through transformer and convertors.

## OAuth2 plugin injection

`convertor/route.py::_build_oauth2_plugins` is shared by standard and AI routes;
keep both on it. Design and decisions:
[resource-oauth2-app-access-design.md](../../../../../docs/resource-oauth2-app-access-design.md)
sections 4 and 7.

```text
support_public   = U and oauth2_public_client_enabled
support_personal = U and oauth2_personal_client_enabled
support_app      = gateway.oauth2_app_enabled and A
                   and not bound bk-access-token-source (any source)
inject           = (support_public or support_personal or support_app) and apisix >= 3.16
challenge_on_missing_credential = support_public or support_personal
```

- Read `gateway.oauth2_app_enabled` from `ReleaseData.gateway` at publish time;
  it is not part of the resource version snapshot.
- Evaluate the `bk-access-token-source` rule on the plugin bindings of the
  release being published (`ReleaseData.get_resource_plugins`). Any binding
  blocks the app channel: it runs before `bk-oauth2-verify`, and both
  `source=bearer` (consumes `Authorization`) and strict `api_key` (400 without
  `X-API-KEY`) break Bearer-only calls. The plugin is no longer public and has
  very few users, so do not split the rule by config again. With
  personal/public enabled, the plugins are still injected with `support_app=false`.
  `core.managers.released_resource_binds_access_token_source` applies
  the same rule to the `ReleasedResource` projection used by scope and lookup;
  keep the two in sync.
- Do not emit a token type. APISIX picks delegated vs app tokens from
  `bk-resource-context.verified_user_required`, so new token types only need a
  plugin upgrade.
- `resource_version_uses_oauth2` (the publish gate) stays limited to
  public/personal: app-channel-only resources degrade to the legacy entry on old
  data planes and must not block publishing.
- New-plugin defaults equal the pre-change behavior (`support_app=false`,
  `challenge_on_missing_credential=true`), so emitting those values is the
  same as omitting them.

### Rollback candidate command

`management/commands/sync_releases_to_gateway_parallel.py --released-since T`
selects gateways with `ReleaseHistory.created_time >= T` **or**
`Release.updated_time >= T`. CLI and some ops publishes write no
`ReleaseHistory` but still update `Release.updated_time`. `--dry-run` prints
names to stdout and the count to stderr. When nothing matches, stdout must stay
0 bytes: Django's `OutputWrapper` appends a newline even to `""`, so do not
write an empty string. The old Dashboard's `--gateway-names` with an empty list
syncs every gateway, so the runbook counts the parsed names instead of testing
file size; `test_restore_runbook_*` runs the exact snippet from the design doc. The DB candidates
alone are not the restore scope: the design doc 7.4 also requires scanning raw
etcd routes.

## Coverage

Tests mirror `tests/controller/`. Conversion changes cover standard behavior
and affected AI, version, plugin and revoke branches. Task/distributor changes
cover synchronization, events, failure propagation and data-plane selection.
