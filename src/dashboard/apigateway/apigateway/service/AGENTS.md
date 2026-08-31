# Service Layer Guide

This guide applies under `apigateway/apigateway/service/`. The dashboard and
repository-root `AGENTS.md` files also apply.

## Layer Boundary

`service/` owns focused, reusable leaf capabilities over model relationships or
domain data: snapshots, schema lookup, cleanup, reusable cross-model queries,
relation normalization, and data shaping.

- Keep permission decisions, lifecycle branching, audit orchestration,
  transactions, and multi-step workflows in `biz/` or `controller/`.
- Do not move code into `service/` only to bypass a `biz`-to-`biz` import
  boundary. Extract only the smallest stable operation with clear inputs,
  outputs, reuse, and direct tests.
- Service modules may call each other and may perform cross-model work when the
  operation remains a reusable leaf capability.
- Historical exception: `service.release.PublishValidator` was moved during
  the `biz-domain-independence` refactor. Treat its location as compatibility
  debt, not placement precedent; new release workflow decisions belong in
  `biz/release/`.

## Module And Package Organization

- Name modules by domain plus capability, such as `resource_snapshot.py`,
  `resource_cleanup.py`, `resource_version_schema.py`, or `openapi_export.py`.
  Avoid generic buckets such as `utils.py` unless the behavior is domain-neutral.
- Keep a small capability as a top-level module. Create `service/<domain>/`
  only when several related capabilities exist or one file mixes unrelated
  responsibilities.
- External callers import package symbols from `apigateway.service.<domain>`,
  not `apigateway.service.<domain>.<capability>`. The package `__init__.py` owns
  its public API and `__all__`; leaf modules do not define `__all__`.
- Package internals may use single-dot relative imports for local leaf modules.
  Use absolute `apigateway.service...` imports outside the current package; do
  not add parent-relative `..` imports.
- Prefer free functions for stateless operations. Use classes when state,
  strategy selection, validation objects, factories, or polymorphism requires
  them.
- Name functions for their action and result: `get_*` for reads, `delete_*` or
  `clear_*` for destructive writes, `build_*` for construction, `format_*` or
  `normalize_*` for shape changes, `snapshot_*` for snapshots, and `ensure_*`
  for idempotent creation or backfill.
- Give non-trivial modules a docstring stating their ownership, keep the public
  surface small, and prefix private helpers with `_`.

## Package Exports

For package `__init__.py` files with `__all__`, keep every section comment in
this fixed order, including empty sections:

```python
# constant
# Enum
# class
# functions
# others
```

Group every export under its matching section. Put module re-exports or other
uncategorized names under `# others`.

## Verification

- Mirror service tests under `apigateway/apigateway/tests/service/`.
- When adding or changing a service package or export, run
  `apigateway/tests/service/test_public_api_contract.py` through the dashboard
  pytest wrapper, as well as focused behavior tests.
- Search production and test call sites before moving, renaming, or deleting a
  public service symbol; remove proxy-only compatibility wrappers unless a
  documented boundary requires them.
- Follow the dashboard guide for the exact pytest wrapper and final lint/test
  gates.
