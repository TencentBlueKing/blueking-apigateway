# Controller Layer Guide

This guide applies under `apigateway/apigateway/controller/`. The dashboard and
repository-root `AGENTS.md` files also apply.

## Publish Pipeline

The normal gateway publication path is:

```text
biz/release -> controller/tasks -> GatewayResourceDistributor
            -> GatewayApisixResourceTransformer
            -> ServiceConvertor + RouteConvertor -> EtcdRegistry
```

- `release_data.py` materializes the release input consumed by conversion.
- `transformer.py` coordinates APISIX resource conversion.
- `convertor/` owns APISIX-native Service, Route, SSL, proto, and release
  resource construction.
- `distributor/` owns registry selection and synchronization.
- `tasks/` and `publisher/` own asynchronous publication, revoke, and lifecycle
  entrypoints.

Controller code consumes domain state and emits data-plane configuration. It
does not own Web DTOs, API response compatibility, normalized persistence
models, or general-purpose domain workflows.

## Conversion Rules

- Preserve existing standard Service and Route blocks, ordering, and useful
  comments when their behavior is unchanged. Add AI behavior through narrow,
  explicit branches rather than refactoring the standard path for symmetry.
- Convert stored provider identity to APISIX provider configuration only here:
  apply built-in endpoint overrides, remove storage-only fields, and convert
  timeout seconds to milliseconds at the publish boundary.
- `ai-proxy` and `ai-proxy-multi` are controller-managed plugins. Generate them
  here; never source them from user bindings.
- Stage plugin configuration remains permissive. When generating an AI Service,
  filter incompatible Stage plugins at publication without changing standard
  Service behavior.
- Use the shared data-plane compatibility helper for AI Gateway version checks.
  Preserve revoke paths that intentionally bypass publish-only compatibility
  checks, and propagate `revoke_flag` through transformer and convertors.
- Do not log plugin configs, backend credentials, plaintext secrets, encrypted
  payloads, or generated APISIX credential material. Warning logs may identify
  skipped plugin type codes without their configuration.

## Distribution And Failure Handling

- Conversion completes in the intermediate transformer registry before the
  target registry is synchronized. Do not write partially converted resources
  directly to the target registry.
- Preserve publish-event transitions and failure reporting when changing task,
  distributor, or publisher control flow.
- Do not swallow conversion or synchronization exceptions. Record the sanitized
  failure through the existing publish-event and procedure-logger paths, then
  preserve the caller-visible failure behavior.

## Testing

- Mirror tests under `apigateway/apigateway/tests/controller/`.
- For convertor changes, cover the unchanged standard path plus each affected
  AI, version, plugin, and revoke branch.
- For distributor or task changes, cover resource synchronization, publish
  events, failure propagation, and data-plane selection as applicable.
- Follow the dashboard guide for the exact pytest wrapper and final lint/test
  gates.
