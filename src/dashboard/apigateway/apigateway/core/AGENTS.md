# Core Module Guide

Keep model-local behavior in `models.py` and reusable single-model queries in
`managers.py`. Core must not import API DTOs or controller models.

## Configuration ownership

- `backend_config.py` defines normalized Pydantic configuration and validation;
  `ai_backend.py` owns built-in provider metadata for adaptation, connectivity
  and publication.
- Persist AI configuration through `BackendConfig.config`: its setter encrypts
  storage and its getter decrypts it. `_config` is the internal encrypted
  representation. `get_config_for_display()` masks credential headers.
- Provider changes must account for enum choices, registry entries, Web adapters,
  connectivity, publication, tests and API documentation at their owning layers.
  Verify each producer/consumer against this branch before changing the contract.

Tests mirror `tests/core/`. Cover model/manager constraints, kinds, configuration,
encryption and masking as affected; changes to a core contract also need the
identified API/service/controller consumer tests.
