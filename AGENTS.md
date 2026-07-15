# AGENTS.md

## Overview

## Project Structure

```
.
├── AGENTS.md
├── README_EN.md
├── README.md
├── Makefile                # make test-bdd — run BDD test suite
├── specs                   # SDD docs
│   ├── 001-agent-test-suite
│   └── 002-bdd-test-refactor
├── src
│   ├── core-api            # the core-api service, ref: src/core-api/AGENTS.md
│   ├── dashboard           # the dashboard, ref: src/dashboard/AGENTS.md
│   ├── dashboard-front     # the frontend of dashboard, ref: src/dashboard-front/AGENTS.md
│   ├── esb                 # abandoned, not important, ignore it
│   ├── mcp-proxy           # the mcp-proxy service, ref: src/mcp-proxy/AGENTS.md
│   └── operator            # the operator service, ref: src/operator/AGENTS.md
├── test                    # existing e2e test suite
│   ├── bin
│   ├── cases
│   ├── Dockerfile
│   ├── README.md
│   └── sync
└── test-bdd                # BDD test suite (new)
    ├── .gitignore          # Ignores runtime artifacts
    ├── AGENTS.md           # Business context, module classification, domain gotchas
    ├── cases/              # BDD test cases (Chinese markdown, ~87 scenarios)
    ├── scripts/            # Playwright test scripts (.spec.js only, no deps)
    └── runtime/            # Test runner (package.json, helpers, setup, teardown, config)
        └── reports/        # Timestamped test reports (gitignored)
```

## Project Relationship

```
apis create and publish:
dashboard-front -> dashboard -> mysql -> dashboard(controller) -> etcd -> operator -> etcd -> blueking-apigateway-apisix

publish event report:
operator -> core-api -> mysql

permission:
blueking-apigateway-apisix -> core-api -> mysql

mcp server:
dashboard-front -> dashboard -> mysql -> mcp-proxy
```

## SKILLs

Agent skills are located in `.agents/skills/`. Before executing any agent task described below, **read the full skill file first** to get detailed instructions, templates, and patterns.

These skills are designed to work with **any AI coding agent** (Claude Code, Codex, Cursor, Windsurf, Aider, etc.) that has access to Playwright MCP browser tools, file system operations, and shell commands.

`bk-apigateway-openapi-check` is opt-in. Do not invoke it unless the user explicitly asks to use that skill. Merely mentioning, editing, or reviewing the skill, or working on OpenAPI-related files, does not authorize its use.

| Skill | File | Description |
|-------|------|-------------|
| bdd-test-gen | `.agents/skills/bdd-test-gen/SKILL.md` | Generate executable Playwright test scripts from BDD case files by exploring a live environment |
| bk-apigateway-openapi-check | `.agents/skills/bk-apigateway-openapi-check/SKILL.md` | Explicit invocation only. Checks consistency between API code, YAML gateway definitions, and API docs (8 checks incl. parameter consistency). |
