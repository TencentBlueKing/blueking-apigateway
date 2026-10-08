# AGENTS.md

## Scope and shared language

This checkout contains independently built components. Apply this guide and each
`AGENTS.md` along the path to the files being changed; a deeper guide adds local
requirements. When starting at the repository root, read those descendant guides
before working in their directories. Do not load sibling components' guides
unless the task crosses their boundary.

Read [DDD ubiquitous language](docs/ddd-ubiquitous-language.md) once per task for
shared terms, identity scopes, lifecycles, compatibility mappings, and component
relationships. Maintain those definitions there; local guides describe development
and module-specific constraints without copying the glossary.

## Component entrypoints

| Directory | Responsibility / guide |
| --- | --- |
| [src/dashboard](src/dashboard/AGENTS.md) | Django management APIs, database models, configuration publishing |
| [src/dashboard-front](src/dashboard-front/AGENTS.md) | Vue dashboard |
| [src/core-api](src/core-api/AGENTS.md) | Runtime permission/key queries and publish-event ingestion |
| [src/operator](src/operator/AGENTS.md) | Control-plane to APISIX etcd synchronization |
| [src/mcp-proxy](src/mcp-proxy/AGENTS.md) | MCP protocol serving and gateway tool calls |
| [src/esb](src/esb/AGENTS.md) | Legacy ESB; outside normal development scope |
| [test-bdd](test-bdd/AGENTS.md) | Playwright BDD cases, generated scripts, and runner |
| `test/` | Existing API integration suite; see `test/README.md` |

## Working in this checkout

- Before editing or running checks, verify `git rev-parse --show-toplevel`,
  `git status --short --branch`, and `git rev-parse HEAD`. For a named PR or
  worktree, match its head to `git worktree list --porcelain`.
- Start from the named endpoint, log, path, or revision. Keep changes inside its
  component unless a verified producer/consumer contract requires more.
- Run component commands from the directory its guide specifies. Runtime and
  checks are component-local; the root `.envrc` is not a shared activation script.
- For review findings, distinguish issues present in the inspected code from
  issues introduced by the selected diff.
- For Markdown-only changes, check the diff, references, and executable examples;
  do not run application lint/test/build suites. Code and configuration changes
  use the affected component's gates. Report skipped checks and their limits.

## BDD generation

Before generating Playwright scripts from cases, read
[the bdd-test-gen skill](.agents/skills/bdd-test-gen/SKILL.md).
