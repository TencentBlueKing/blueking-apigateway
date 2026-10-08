# Controller Layer Guide

## Compilation and distribution

The normal publication path runs through `biz/release`, `controller/tasks`,
`GatewayResourceDistributor` (`distributor/etcd.py`),
`GatewayApisixResourceTransformer` (`transformer.py`), and `EtcdRegistry`.

- `release_data.py` supplies conversion input; `convertor/` builds native
  Services, Routes and release markers. SSL/proto conversion remains unimplemented
  in the gateway transformer; do not infer support from model/convertor names.
- The transformer accumulates converted resources in memory. Distribution starts
  registry synchronization only after transformation succeeds. This ordering does
  not promise atomic etcd synchronization.
- `tasks/` and `publisher/` coordinate publish, revoke and lifecycle entrypoints.
  Preserve event transitions and existing tuple/exception failure contracts:
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

## Coverage

Tests mirror `tests/controller/`. Conversion changes cover standard behavior
and affected AI, version, plugin and revoke branches. Task/distributor changes
cover synchronization, events, failure propagation and data-plane selection.
