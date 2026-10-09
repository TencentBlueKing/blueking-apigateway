# API Layer Guide

## Surface and boundary contracts

`api-layers` in `pyproject.toml` enforces independence between `apis.web`,
`apis.open`, `apis.v2.open`, `apis.v2.inner`, and `apis.v2.sync`.

- `apis.web` serves `dashboard-front` and may use Web-specific DTOs.
- `apis.open` is the legacy open API with compatibility response formats.
- `apis.v2.open` is the public v2 open API.
- `apis.v2.inner` serves BlueKing internal callers.
- `apis.v2.sync` serves gateway automation and SDK sync clients.

### Boundary rules

- Do not import another surface's views, serializers or helpers. Keep local
  shaping and compatibility in that surface; extract only shared lower-layer
  behavior.
- Serializers own transport validation and input/output definitions. Views own
  request context, lower-layer calls and response assembly.
- Shape queries or batch lower-layer reads instead of per-row serializer lookups.
- Validate identifier ownership alongside permission classes and tenant scope.
  An input gap alone does not establish an authorization bypass.
- Preserve `OKJsonResponse` / `FailJsonResponse` and legacy
  `V1OKJsonResponse` / `V1FailJsonResponse` contracts at their existing boundaries.
- Keep client-visible security errors sanitized; record diagnostic exceptions
  through the existing logger without credential material.
- Keep serializer schema names unique. Existing `Meta.ref_name` overrides are
  supported by drf-spectacular for compatibility.

Open and v2 Sync AI backend input uses normalized storage configuration; submitted
secret values are literal. Web masked-secret restoration belongs only to
`web/ai_backend/adapter.py`: it requires an existing matching mask and unchanged
provider/destination origin and auth-header identity. Web represents one instance
and at most one auth header; preserve nonrepresentable-config errors in
`web/ai_backend/presentation.py` instead of silently dropping valid stored fields.

## API consistency and coverage

Open API changes that affect registrations or documentation also require
`apigateway/apigateway/data/AGENTS.md`; it owns consistency paths and commands.
Tests mirror `tests/apis/<surface>/`; URL tests normally use `view_name` and
`resp.json()`. Cover every affected surface and retain intentional differences.
