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

## OAuth2 app channel storage

- `Gateway.oauth2_app_enabled` (`db_default=True`) is the writable gateway
  switch. `ReleasedResource.oauth2_app_delegated_enabled` (U && A) and
  `oauth2_app_only_enabled` (!U && A) are projections with `db_default=False`.
  Both are false when the snapshot's `plugins` bind `bk-access-token-source`
  with any `source` or `allow_fallback`
  (`released_resource_binds_access_token_source`). This mirrors the
  controller rule that drops `support_app`; change both together. `core`
  cannot import `apps`, so the plugin type lives in
  `core.constants.BK_ACCESS_TOKEN_SOURCE_PLUGIN_TYPE`, pinned by a test.
- The Web read-only `auth_config.oauth2_app_delegated_enabled` stays U && A and
  ignores the `bk-access-token-source` rule.
- The projection columns hold only values derived from the snapshot, never the
  gateway switch: a `ReleasedResource` row is written once per resource version
  and shared by every stage that releases it. Consumers AND the switch at query
  time.
- `get_released_resource_oauth2_app_flags` is the single derivation, shared by
  migration `0059`, `ReleasedResourceManager.save_released_resource` and
  `refresh_oauth2_app_flags`. Change all of them together.
- The `db_default`s are what lets a rolled-back Dashboard keep `0059`; do not
  drop them.
- `0059` is non-atomic. Its DDL uses `SeparateDatabaseAndState` and checks for
  the column or index before creating it. The backfill pages by primary key and
  reads only `id` and `data`. Keep it re-runnable after a partial failure.
- After a rollback that kept `0059`, the old Dashboard writes new projections
  with `false`. On the next upgrade, run
  `sync_released_resource --all --oauth2-app-flags` (`--dry-run` first). It
  refreshes rows in place and creates missing ones. Do not use `--force` for
  this: it deletes rows before rebuilding, so scope and lookup briefly return
  nothing.

Migration tests (`tests/core/test_migration_*.py`) are excluded from
`make test-fast`; run them with `make test-migrations` (see `TESTING.md`).

Tests mirror `tests/core/`. Cover model/manager constraints, kinds, configuration,
encryption and masking as affected; changes to a core contract also need the
identified API/service/controller consumer tests.
