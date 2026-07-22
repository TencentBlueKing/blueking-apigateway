# Business Layer Guide

This guide applies under `apigateway/apigateway/biz/`. The dashboard and
repository-root `AGENTS.md` files also apply.

## Layer Boundary

`biz/` owns use-case decisions and orchestration: permission-aware behavior,
lifecycle branching, audit and side effects, transaction boundaries, and the
sequence of lower-layer operations.

- Keep transport validation, response shaping, and API-surface branching in
  `apis/`.
- Keep APISIX resource compilation and publication in `controller/`.
- Extract only focused reusable queries, relationship operations, snapshots,
  cleanup, or data shaping into `service/`.
- Do not add a `biz` wrapper that merely delegates to a service or another
  domain. Keep local behavior local, or move the real ownership boundary.
- Place transactions around the complete use case that must commit or roll
  back together; do not hide a partial transaction inside an unrelated helper.

## Domain Independence And Public APIs

`pyproject.toml` is authoritative for the `biz-domain-independence` and
`biz-package-public-api` contracts.

- `biz.gateway`, `biz.resource`, `biz.permission`, and `biz.mcp_server` must
  remain independent peer domains. Package-local imports within one domain are
  allowed.
- Put cross-domain workflow coordination in a neutral use-case module or in
  `controller/` when it is part of publication. Put only reusable leaf
  capabilities in `service/`.
- Callers from `apis/` and `apps/` must import contracted public symbols from
  `apigateway.biz.<domain>`, not forbidden leaf modules.
- A package `__init__.py` owns its public API. Keep `__all__` grouped in the
  established `constant`, `Enum`, `class`, `functions`, `others` order,
  retaining empty section comments.
- Before moving, renaming, or deleting a public symbol, search production and
  test call sites. Remove proxy-only wrappers unless a documented compatibility
  boundary requires them.

## Testing

- Mirror tests under `apigateway/apigateway/tests/biz/<domain>/`.
- Test observable workflow decisions, transaction behavior, permissions,
  lifecycle transitions, audit records, and side effects rather than private
  helper structure.
- When logic moves between `biz/` and `service/`, run focused tests for both
  owners and the callers whose behavior must remain unchanged.
- Follow the dashboard guide for the exact pytest wrapper and final lint/test
  gates.
