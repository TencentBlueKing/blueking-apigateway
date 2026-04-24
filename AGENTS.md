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
│   └── mcp-proxy           # the mcp-proxy service, ref: src/mcp-proxy/AGENTS.md
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

## Skills

Agent skills are located in `.agents/skills/`. Before executing any agent task described below, **read the full skill file first** to get detailed instructions, templates, and patterns.

These skills are designed to work with **any AI coding agent** (Claude Code, Codex, Cursor, Windsurf, Aider, etc.) that has access to Playwright MCP browser tools, file system operations, and shell commands.

| Skill | File | Description |
|-------|------|-------------|
| bdd-test-gen | `.agents/skills/bdd-test-gen/SKILL.md` | Generate executable Playwright test scripts from BDD case files by exploring a live environment |

---

## BDD Test Suite (`bdd-test-gen`)

> Full documentation, knowledge base, URL mappings, selectors, and gotchas: **[test-bdd/AGENTS.md](test-bdd/AGENTS.md)**
>
> Skill file: **`.agents/skills/bdd-test-gen/SKILL.md`** — read this file before executing any script generation commands.

### Workflow

1. **BDD Cases** (`test-bdd/cases/`): ~87 curated Chinese Gherkin scenarios covering 26 functional modules
2. **Script Generation**: Invoke the `bdd-test-gen` SKILL to convert BDD cases into Playwright scripts by exploring a live environment
3. **Script Execution**: Run `make test-bdd URL=<url> USER=<user> PASSWORD=<pass>` — no agent needed, pure script execution

### Quick Commands

```bash
# Run all BDD tests
make test-bdd URL=https://example.com USER=admin PASSWORD=secret

# Generate scripts from BDD cases (agent-assisted)
# Invoke the bdd-test-gen SKILL with: --url <URL> --user <USER> --password <PASS> --all
```
