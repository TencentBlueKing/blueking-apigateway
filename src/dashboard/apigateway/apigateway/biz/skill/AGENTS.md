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
| `refs.py` | reference syntax: a whole-string `${{ inputs.<name> }}` or `${{ steps.<id>.outputs.<path> }}`; any other value is fixed |
| `resource_definition.py` | `ResourceDefinition` and the `ResourceProvider` protocol |
| `resource_loader.py` / `schema_converter.py` | definitions from the current release and its OpenAPI schema |
| `validator.py` | cross-checks between the orchestration and resource definitions |
| `renderer.py` | template context and the per-step OpenAPI snippet |
| `writer.py` | one transactional publish: metadata, tags, config, version, relations |
| `syncer.py` | per-declaration status for built-in injection |

## Where to change what

- SKILL.md body wording or section order: `data/skill/templates/SKILL.md.j2`.
  The template uses `trim_blocks`/`lstrip_blocks`; keep the whitespace notes at
  its top. Context fields come from `renderer._SkillBodyContext`.
- `references/*.md`: `data/skill/references/`. The body links to these files;
  wording changes belong in the file itself.
- New declaration field or rule: `declaration.py`; reference checks against
  resources go in `validator._RefChecker`.

## Constraints

- Built-in injection must not break deployment: one bad declaration only affects
  its own result, and the command exits 0. Missing resources skip the declaration
  until the next deploy; do not partially write it. A resource is unavailable
  when its gateway or Stage is inactive, the Stage has no release, the released
  version does not contain that standard resource, the resource is disabled in
  that Stage, or its versioned OpenAPI schema does not define both request
  parameters and response fields. `none_schema` (explicitly "no request
  parameters") counts as defined request parameters; an imported `responses`
  without fields does not count as a response definition. Log the skip so the
  gateway owner can fix the source schema.
- Parameter locations and types come only from the resource definition; nothing
  is guessed from the HTTP method, because a version is immutable once written.
  The declaration is rejected when a referenced resource's request body is not
  `application/json` (the body is always rendered as JSON), or when a step maps
  a parameter missing from the definition. Resource-level problems go in
  `ResourceDefinition.errors`; the validator reports them as errors and skips
  field checks for that resource.
- A version is immutable once written; the same version (case-insensitive) is
  skipped, not overwritten. A new version must be higher than the current one by
  `major.minor.patch` (pre-release and build suffixes are ignored), otherwise it
  is rejected: a lower version made current would leave the higher one skipped
  as "already exists" on every later deploy. `writer.check_new_version` owns
  this rule for both the injection pre-check and the write transaction.
- A written version is a snapshot of the resource definitions at injection time.
  Gateway releases do not re-render or update built-in Skills, and nothing yet
  detects drift. After a referenced resource changes, bump the declaration
  `version` and redeploy, or run `sync_platform_skills`. Do not auto-generate
  versions on release: they would collide with versions bumped in the
  repository, and hand-written step text would not be reviewed.
- Update `SkillMetadata` with `save(update_fields=...)` so concurrent
  `download_count` increments are kept.
- Injection reads only the database and repository files; it never calls
  gateways or external systems.
- Rendering is deterministic: no timestamps or environment URLs in the body.
- Steps follow the GitHub Actions composite-action shape (`id`, `name`, `uses`,
  `if`, `description`, `with`). `if`, polling and per-item calls are natural
  language for the AI; do not add machine-checked poll, loop or filter fields.
  Required parameters left out of `with` are listed in the snippet without a
  value and explained by the step description.
- Do not map credentials (`access_token`, `bk_token`, `bk_ticket`,
  `bk_app_secret`) in `with`; the body tells the AI not to pass or ask for them.
- `references/how-to-call-apis.md` contains literal `${{ }}` and
  `{{ ... }}` placeholders; do not render it with Jinja.

## Tests

`tests/biz/skill/` holds one golden fixture, `fixtures/declarations/job-plan-run-and-log.yaml`,
plus `fixtures/resources.json` and `fixtures/expected/job-plan-run-and-log.md`. That
declaration covers a step `if`, polling and per-item calls described in text, fixed
values and write calls; rule tests
mutate this one declaration. `fixtures/resources.json` is also the resource contract
for every file in `data/skill/declarations/`: `test_shipped_declarations.py` publishes
those resources with versioned OpenAPI schemas, then validates and renders each
shipped declaration. `errors` and warnings must be empty. For
bk-sops and devops the fixture records the parameters and response fields those
declarations map; `task_id` is a path
parameter and `X-DEVOPS-UID` is a header, and the other GET parameters are query,
POST parameters body. It is not a copy of the live OpenAPI document. After an
intentional template change, regenerate `expected/` from the renderer and review
the diff; the rendered snippet must stay valid OpenAPI 3.1. Command output is
covered by `tests/apps/skill/management/commands/test_sync_platform_skills.py`.
