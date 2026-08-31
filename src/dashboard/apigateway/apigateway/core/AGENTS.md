# Core Module Guide

This guide applies under `apigateway/apigateway/core/`. The dashboard and
repository-root `AGENTS.md` files also apply.

## Module Ownership

`core/` owns the central gateway domain model and normalized configuration:
`Gateway`, `Stage`, `Resource`, `ResourceVersion`, `Release`, `Backend`,
`BackendConfig`, and `Context`-related domain types.

- Keep rich behavior that concerns one model in `models.py`.
- Keep reusable single-model queryset logic in `managers.py`.
- Put multi-model queries or workflows in the appropriate `service/`, `biz/`,
  or `controller/` layer; do not grow managers into business services.
- Keep constants and stored enum values backward compatible with existing rows
  and public payloads.
- Do not import API serializers, Web DTOs, or controller models into `core/`.

## Domain Names And Kinds

- `Gateway.kind` stores numeric `GatewayKindEnum` values. API names use
  `GatewayKindNameEnum` conversion.
- `Backend.kind` and `Resource.kind` store the string values `standard` and
  `ai`.
- Transport fields named `type` are not kind discriminators. Do not repurpose
  them to select gateway, backend, or resource behavior.

## AI Backend Configuration

Read the repository-root AI Gateway model and Web/storage/publish protocol
documents listed in the dashboard guide before changing AI configuration.

`core/backend_config.py` owns the normalized Pydantic storage contract.
`core/ai_backend.py` owns the built-in provider registry used by Web adaptation,
connectivity tests, and publishing.

- Store built-in providers by product identity. APISIX-specific
  `openai-compatible` conversion, endpoint overrides, and timeout conversion
  belong at the controller publish boundary.
- Keep Web-only input limits out of the core model. The normalized core config
  may support shapes that a particular API surface does not expose.
- A provider change must account for enum choices, registry entries, Web
  adapter rules, connectivity behavior, publish conversion, tests, and API
  documentation. Change each representation at its owning layer.
- `BackendConfig.config` encrypts AI configuration at the ORM persistence
  boundary. Do not bypass its model field or persistence helpers with raw
  plaintext writes.

## Verification

- Add focused tests under `apigateway/apigateway/tests/core/` for model,
  manager, kind, serialization, encryption, or masking behavior.
- When a core contract changes, also run the focused tests for every API,
  service, or controller consumer identified by call-site search.
- Follow the dashboard guide for the exact pytest wrapper and final lint/test
  gates.
