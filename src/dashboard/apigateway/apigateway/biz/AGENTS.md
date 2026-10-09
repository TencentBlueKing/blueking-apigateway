# Business Layer Guide

## Use-case and domain contracts

Business modules own permission-aware decisions, lifecycle branches,
transactions, audit and side-effect sequencing. Transactions encompass the
complete use case that must commit or roll back together. Extract only focused
queries, snapshots, relationship operations or cleanup into `service/`.

`biz-domain-independence` and `biz-package-public-api` in `pyproject.toml` define
peer-domain and caller boundaries:

- `gateway`, `resource`, `permission`, and `mcp_server` remain independent peer
  domains; imports within a domain are allowed.
- Coordinate cross-domain workflows in a neutral use-case module, or
  `controller/` for publication. Do not relocate decisions into `service/` to
  bypass a peer import restriction.
- API/app callers import contracted public symbols from `apigateway.biz.<domain>`;
  the exact forbidden leaf modules are enumerated in the import contract.
- Package `__init__.py` owns exports. Keep `__all__` sections in the established
  `constant`, `Enum`, `class`, `functions`, `others` order, including empty ones.
- A forwarding wrapper needs an interface, compatibility, instrumentation or
  lifecycle purpose; retain those roles when auditing wrapper removal.

## Coverage

Tests mirror `tests/biz/<domain>/` and cover workflow decisions, transaction
behavior, permissions, lifecycle, audit and side effects. A move to/from
`service/` needs focused coverage for both owners and affected callers.
