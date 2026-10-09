# Service Layer Guide

## Capability boundaries

Services expose reusable queries, snapshots, schema lookup, relation
normalization, cleanup and data shaping. Modules may compose other services
and span models while remaining focused leaf operations. Workflow transactions,
permission decisions and lifecycle orchestration stay with their owning use case.
`service.release.PublishValidator` is an existing compatibility exception,
not a precedent for moving new release workflows here.

## Modules and public exports

- Name modules by domain/capability, such as `resource_snapshot.py`; keep a small
  capability in one module. Create a domain package for related capabilities,
  rather than a generic utility bucket.
- External callers use `apigateway.service.<domain>` exports. The
  `service-package-public-api` import contract forbids their leaf-module imports;
  package internals may use single-dot imports. Use absolute imports outside
  the package, without parent-relative imports.
- Package `__init__.py` owns `__all__`; leaf modules do not define it. Preserve
  these ordered sections, including empty ones:

```python
# constant
# Enum
# class
# functions
# others
```

Group every export under its matching section. Put module re-exports or other
uncategorized names under `# others`.

- Keep public exports small and private helpers prefixed with `_`. Document
  non-trivial module ownership. Prefer stateless functions; classes need state,
  strategy, validation, factories or polymorphism.
- Names express behavior: `get_*`, `delete_*` / `clear_*`, `build_*`,
  `format_*` / `normalize_*`, `snapshot_*`, or idempotent `ensure_*`.
- Keep wrappers with required compatibility/interface/lifecycle roles; remove
  proxy-only residue introduced by a move.

## Coverage

Tests mirror `tests/service/`. Package/export changes also need the public API
contract target documented in `tests/AGENTS.md`, alongside focused behavior tests.
