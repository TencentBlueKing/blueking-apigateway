# Skill Generation and Injection

Paths below start at `apigateway/apigateway/`. Shared terms (declaration, resource
definition, patch snapshot) live in the DDD glossary. Callers outside `biz/` use
only the names exported from `biz/skill/__init__.py`.

Flow: `declaration.parse_declaration` → `validator.validate_declaration` →
`renderer.render_skill_body` → `writer.save_skill_version`. `syncer` runs that
flow for built-in declarations in `data/skill/declarations/`; the
`sync_platform_skills` command (`apps/skill/management/commands/`) wraps it and
runs from `bin/post_migrate`.

| Module | Owns |
| --- | --- |
| `declaration.py` | pydantic model of the declaration YAML; field rules and error messages |
| `refs.py` | reference syntax (`inputs.x`, `each.x`, `<step>.<resource>.<path>`, `{value}`, `{ref, where}`) and poll expressions |
| `resource_definition.py` | `ResourceDefinition` and the `ResourceProvider` protocol |
| `resource_loader.py` / `schema_converter.py` / `patch_snapshot.py` | definitions from the current release + OpenAPI schema, patched by resource patch snapshots |
| `validator.py` | cross-checks between the orchestration and resource definitions |
| `renderer.py` | template context and the per-call OpenAPI snippet |
| `frontmatter.py` | SKILL.md frontmatter render/parse: Agent Skills keys plus `display_name` / `display_name_en` |
| `package.py` | SKILL.md + `references/` file map for download packages |
| `writer.py` | one transactional publish: metadata, tags, config, version, relations |
| `syncer.py` | per-declaration status for built-in injection |

## Where to change what

- SKILL.md body wording or section order: `data/skill/templates/SKILL.md.j2`.
  The template uses `trim_blocks`/`lstrip_blocks`; keep the whitespace notes at
  its top. Context fields come from `renderer._SkillBodyContext`.
- `references/*.md`: `data/skill/references/`; placeholders are listed in
  `SkillReferencePlaceholderEnum`. `package.load_references()` returns them
  unfilled; the download package build fills them.
- New declaration field or rule: `declaration.py`; reference checks against
  resources go in `validator._RefChecker`.
- Frontmatter keys or format: `frontmatter.py` and the `SKILL_FRONTMATTER_*`
  constants; the glossary records the spec.

## Constraints

- Built-in injection must not break deployment: one bad declaration only affects
  its own result, and the command exits 0. Missing resources skip the declaration
  until the next deploy; do not partially write it.
- A version is immutable once written; the same version (case-insensitive) is
  skipped, not overwritten.
- Update `SkillMetadata` with `save(update_fields=...)` so concurrent
  `download_count` increments are kept.
- Injection reads only the database and repository files; it never calls
  gateways or external systems.
- Rendering is deterministic: no timestamps or environment URLs in the body. The
  frontmatter `datetime` comes from the version's `created_time` when packaging.

## Tests

`tests/biz/skill/` holds one golden fixture, `fixtures/declarations/job-plan-run-and-log.yaml`,
plus `fixtures/resources.json` and `fixtures/expected/job-plan-run-and-log.md`. That
declaration covers poll, for_each, where, literal values and write calls; rule tests
mutate this one declaration. Shipped declarations in `data/skill/declarations/` are
not snapshotted one by one. After an intentional template change, regenerate
`expected/` from the renderer and review the diff; the rendered snippet must stay
valid OpenAPI 3.1. Command output is covered by
`tests/apps/skill/management/commands/test_sync_platform_skills.py`.
