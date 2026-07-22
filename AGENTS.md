# AGENTS.md

## Overview

This is a multi-component API Gateway repository. The root guidance applies to
the whole checkout; each component's nearest `AGENTS.md` defines its local
runtime, architecture, and verification commands.

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
└── test-bdd                # Playwright BDD test suite
    ├── .gitignore          # Ignores runtime artifacts
    ├── AGENTS.md           # Business context, module classification, domain gotchas
    ├── cases/              # BDD test cases in Chinese markdown
    ├── scripts/            # Generated Playwright test scripts
    ├── runtime/            # Runner helpers, setup, teardown, and config
    │   └── package-lock.json # Additional tracked runtime lockfile
    ├── package.json
    └── package-lock.json
```

## Working In This Repository

- Read this file and the nearest nested `AGENTS.md` for every target path. Run
  commands from the component root documented there; do not assume one runtime
  or top-level gate covers all projects.
- Keep component-local work inside that component unless the request or a
  verified producer/consumer path requires a cross-component change.
- Start investigations from the exact log, path, URL, endpoint, commit, PR, or
  report named by the user, then verify it against the current checkout before
  generalizing.
- Before editing, testing, reviewing, or publishing from a repository with
  multiple worktrees, verify the active root, branch, and commit with
  `git rev-parse --show-toplevel`, `git status --short --branch`, and
  `git rev-parse HEAD`. When a PR or worktree is named, match its explicit head
  to `git worktree list --porcelain`; do not let a helper infer a PR from an
  unrelated checkout.
- For review findings, answer two questions separately: whether the issue is
  real in the inspected code and whether the selected diff introduced it.
- Follow the target component's verification contract. Markdown-only changes
  require diff and reference checks, not unrelated component lint or test runs.

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

| Skill | File | Description |
|-------|------|-------------|
| bdd-test-gen | `.agents/skills/bdd-test-gen/SKILL.md` | Generate executable Playwright test scripts from BDD case files by exploring a live environment |
