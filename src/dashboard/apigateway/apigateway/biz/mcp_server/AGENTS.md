# MCP Business Workflows

Paths below start at `apigateway/apigateway/`. The public package exports
`MCPServerHandler` and related handlers; `mcp_server.py` owns save/sync, selection,
permission and client-configuration workflows.

- Resolve tools and permission resource IDs from the Stage's published version,
  using `service/resource_version/schema.py` and released projections, rather
  than current editable Resource rows. Coordinate version switches with
  `apps/mcp_server/tasks.py`; its guide owns asynchronous sequencing.
- `sync_permissions()` materializes enabled public/personal OAuth2 clients as
  MCP app permissions, then maps each permitted app to virtual-app resource
  permissions. Keep server identity in virtual app codes and retain
  `resource_version` / `delete_stale` semantics used by the release tasks.
- Candidate validation and API reachability have distinct checks: standard-kind
  selection does not currently exclude legacy `disabled_stages`; release route
  compilation still filters them. Do not silently widen candidate behavior.
- For results that vary by selected tools, key by `mcp_server_id`.
  `get_least_privileges_by_server()` returns that mapping; the older
  `get_least_privileges()` has a different gateway/Stage-keyed contract. Share
  Release loading by gateway/Stage, without sharing per-server privilege results.
- Permission apply/revoke/delete flows retain their status, soft-delete and ITSM
  contracts; follow the owning handlers and managers rather than deriving state
  transitions from UI wording.

Cover `tests/biz/mcp_server/` and affected API/app task callers, including servers
sharing a Stage with different tools, version changes and permission cleanup.
