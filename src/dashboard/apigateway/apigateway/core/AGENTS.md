# Core Module Guide

This guide applies under `apigateway/apigateway/core/`. The dashboard and
repository-root `AGENTS.md` files also apply.

## Module Ownership

`core/` owns domain models and normalized configuration.

- Keep rich behavior that concerns one model in `models.py`.
- Keep reusable single-model queryset logic in `managers.py`.
- Put multi-model queries or workflows in the appropriate `service/`, `biz/`,
  or `controller/` layer; do not grow managers into business services.
- Do not import API serializers, Web DTOs, or controller models into `core/`.

## AI Backend Configuration

Read the repository-root AI Gateway model and Web/storage/publish protocol
documents listed in the dashboard guide before changing AI configuration.

`core/backend_config.py` owns the normalized Pydantic storage contract.
`core/ai_backend.py` owns the built-in provider registry used by Web adaptation,
connectivity tests, and publishing.

- A provider change must account for enum choices, registry entries, Web
  adapter rules, connectivity behavior, publish conversion, tests, and API
  documentation. Change each representation at its owning layer.

## Verification

- Add focused tests under `apigateway/apigateway/tests/core/` for model,
  manager, kind, serialization, encryption, or masking behavior.
- When a core contract changes, also run the focused tests for every API,
  service, or controller consumer identified by call-site search.
- Follow the dashboard guide for the exact pytest wrapper and final lint/test
  gates.
