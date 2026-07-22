# API Layer Guide

This guide applies under `apigateway/apigateway/apis/`. The dashboard and
repository-root `AGENTS.md` files also apply. Read a deeper guide when present,
including `apis/web/plugin/AGENTS.md` for plugin work.

## Surface Ownership

The API surfaces are intentionally independent and enforced by the
`api-layers` import-linter contract in `pyproject.toml`:

- `apis.web` serves `dashboard-front` and may use Web-specific DTOs.
- `apis.open` is the legacy open API with compatibility response formats.
- `apis.v2.open` is the public v2 open API.
- `apis.v2.inner` serves BlueKing internal callers.
- `apis.v2.sync` serves gateway automation and SDK sync clients.

- Do not import views, serializers, or helpers from one API surface into
  another.
- Keep small surface-specific parameter shaping, response assembly, and
  compatibility behavior in the owning surface, even when similar code exists
  elsewhere.
- Move behavior down only when it is genuinely shared workflow, domain,
  service, or utility logic. Do not create a shared API helper that couples
  otherwise independent surfaces.

## Boundary Responsibilities

- Serializers own transport validation and input/output definitions. Views own
  request context, thin control flow, lower-layer calls, and response assembly.
- Avoid per-row model lookups from serializer methods or response filters; use
  query shaping, annotations, or lower-layer batching to prevent N+1 behavior.
- Verify gateway/resource ownership, permission classes, tenant context, and
  object scope before accepting identifiers from a request. Do not confuse an
  input-validation gap with proof of an authorization bypass.
- Web and v2 APIs normally use `OKJsonResponse` / `FailJsonResponse`. Preserve
  `V1OKJsonResponse` / `V1FailJsonResponse` where the legacy open contract
  requires them.
- Keep client-visible security errors sanitized and log the original exception
  with `logger.exception(...)`.
- Preserve unique drf-yasg `Meta.ref_name` values when adding serializers.

Web AI backend payloads use the flat `AIBackendWebConfigAdapter` contract.
Open and v2 automation surfaces use the normalized stored protocol instead.
Masked-secret restoration is a Web update-boundary behavior; do not apply it to
Open or Sync input, where submitted stored-protocol values are literal.

## OpenAPI Contract

When changing an open API, keep these representations aligned:

- Views and serializers under `apigateway/apigateway/apis/`.
- Gateway YAML under `apigateway/apigateway/data/apigw-definitions/`.
- Markdown docs under `apigateway/apigateway/data/apidocs/zh/`.

Both dashboard lint targets run the consistency checker. For a focused rerun:

```bash
cd src/dashboard
uv run make lint-openapi
uv run make lint-openapi-help
```

The help target documents scope, API, JSON, and intentional fix options. Keep
method, path, request, response, status, and error documentation synchronized.

## Testing

- Mirror tests under `apigateway/apigateway/tests/apis/<surface>/`.
- API tests normally call URLs by `view_name` and assert through `resp.json()`.
- When a contract exists on several surfaces, test every surface intended to
  change and preserve tests for surfaces that intentionally differ.
- Follow the dashboard guide for the exact pytest wrapper and final lint/test
  gates.
