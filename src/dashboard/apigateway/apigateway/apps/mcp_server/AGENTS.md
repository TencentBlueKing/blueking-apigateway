# MCP App Persistence and Tasks

Paths below start at `apigateway/apigateway/`. Models, migrations, management
commands and asynchronous entrypoints live here; use-case behavior is owned by
`biz/mcp_server/` and its guide.

- Update selected tools through `MCPServer.update_resource_names()` /
  `delete_resource_names()`. The `resource_names` setter rejects assignment;
  `_resource_names` preserves resource/tool alias pairs. Do not write a list
  directly to the private storage field.
- In `tasks.py`, publish permission sync is serialized by a Stage-scoped Redis
  lock. Before Release changes, add permissions with `delete_stale=False`;
  after publication, reconcile against the current version with stale-task and
  newer-publish checks before deleting old permissions. Preserve both phases.
- `sync_mcp_server_after_release()` uses `service.release.wait_release_ready()`;
  a success event alone is insufficient. Write MCP definitions only after the
  Release matches the expected version and Stage is active; failure/timeout
  skips the write through the existing status path.
- Task imports into business/service layers are explicit import-linter
  entrypoint exceptions in `pyproject.toml`; models do not inherit that freedom.

Cover `tests/apps/mcp_server/` for model parsing, task sequencing, lock behavior,
readiness and stale reconciliation. Changes to permission mapping also need the
owning `tests/biz/mcp_server/` coverage.
