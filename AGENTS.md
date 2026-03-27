# AGENTS.md

## Skills

Agent skills are located in `.agents/skills/`. Before executing any agent task described below, **read the full skill file first** to get detailed instructions, templates, and patterns.

These skills are designed to work with **any AI coding agent** (Claude Code, Codex, Cursor, Windsurf, Aider, etc.) that has access to Playwright MCP browser tools, file system operations, and shell commands.

| Skill | File | Description |
|-------|------|-------------|
| agent-test | `.agents/skills/agent-test/SKILL.md` | Browser-based regression test runner for the BlueKing API Gateway dashboard |

---

## Agent Test Suite (`agent-test`)

> Full documentation, knowledge base, URL mappings, selectors, and gotchas: **[test/agent-tests/AGENTS.md](test/agent-tests/AGENTS.md)**
>
> Skill file: **`.agents/skills/agent-test/SKILL.md`** — read this file before executing any test commands.
