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
| `schema_converter.py` | OpenAPI schema converted to parameters and response fields |
| `resource_loader.py` | `SkillResource`, `ResourceProvider`, and loading the current release |
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
- The resource definition (the released OpenAPI schema) is the only source of
  parameters and responses; the declaration references it and does not redefine
  it. Parameter locations and types come only from the definition; nothing is
  guessed from the HTTP method, because a version is immutable once written.
  Inputs and outputs declare a required `type` in the resource-definition
  notation (`string`, `array<object>`, `integer|string`); `example` and
  `default` must match it. An input's `type` must equal every typed parameter
  it is bound to in `with`, and its interface description comes from those
  parameters, so every input must be bound at least once. An output's `type`
  must equal the type derived from its source: an input's `type`, or the
  response field's type wrapped in one `array<…>` per `[]` in the path and one
  more when the source step is a per-item call (`failed_host_logs` is
  `array<object>` while one call's `data` is `object`). A response field
  without a type is not compared. An input's `description` is an optional orchestration
  hint (drafting rules, value strategy) and must not restate the OpenAPI
  description. `outputs` must have at least one entry: every orchestrable
  resource has response fields, so there is always a result to report.
  Every required or path parameter must appear in `with`. A per-item call binds
  a non-array parameter to a step reference containing `[]`
  (`task_id: ${{ steps.list-tasks.outputs.data[].id }}`): one call per element of
  the array before the last `[]`, rendered with `x-each: true`. Which elements to
  call stays in the step `description`. All per-item parameters of one step must
  come from the same array. An array parameter bound to `[]` still receives the
  collected array. `refs.each_array` owns this rule for the validator and the
  renderer.
  The declaration is rejected when a referenced resource's request body is not
  `application/json` (the body is always rendered as JSON), when a required or
  path parameter is missing from `with`, when a step maps a parameter missing
  from the definition, when a `${{ steps.* }}` reference names a response field
  missing from the definition, when an input's `type` differs from a bound
  parameter's type, when a required or path parameter is mapped from an
  optional input without a default, when a step's per-item parameters come
  from different arrays, or when an output's `type` differs from its source. Resource-level problems go
  in `SkillResource.errors`; the validator reports them as errors and skips
  field checks for that resource.
  Warnings are only for non-blocking resource facts, such as a non-public
  resource.
- A version is immutable once written; the same version (case-insensitive) is
  skipped, not overwritten. A new version must be higher than the current one by
  `major.minor.patch` (pre-release and build suffixes are ignored), otherwise it
  is rejected: a lower version made current would leave the higher one skipped
  as "already exists" on every later deploy. `writer.check_new_version` owns
  this rule for both the injection pre-check and the write transaction.
- `changelog` is a list of `{version, date, content}` entries, newest first;
  the first entry must be the declaration `version`, and versions strictly
  decrease by `major.minor.patch`. `date` is `YYYY-MM-DD` or
  `YYYY-MM-DD HH:MM:SS` without a time zone or fractional seconds; unquoted
  YAML dates/timestamps are accepted and a `T` separator is stored as a space.
  `SkillVersion.changelog` stores only that version's entry as JSON.
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
- The stored artifact is the body only; `SKILL.md.j2` does not render frontmatter.
  A download package's frontmatter follows the Agent Skills spec and contains
  only `name`, `description`, and `metadata`. `metadata` contains only `type`,
  `version`, `author`, `datetime`, and `source`. `datetime` is
  `SkillVersion.created_time`. Do not write `display_name`, `SkillMetadata.code`,
  or the `SkillMetadata.metadata` extension JSON into `SKILL.md`.
- Steps follow the GitHub Actions composite-action shape (`id`, `name`, `uses`,
  `description`, `with`) without `if`. Run conditions, polling and which
  elements a per-item call covers are natural language in `description`; do not
  add machine-checked condition, poll, loop or filter fields.
- Authentication methods are gateway-specific and must not be inferred from a
  fixed list of credential parameter names. The body tells the AI not to ask
  users for credentials; callers inject them using the target gateway's
  supported authentication method.
- `references/how-to-call-apis.md` contains literal `${{ }}` and
  `{{ ... }}` placeholders; do not render it with Jinja.

## Tests

`tests/biz/skill/` holds one golden fixture, `fixtures/declarations/job-plan-run-and-log.yaml`,
plus `fixtures/resources.json` and `fixtures/expected/job-plan-run-and-log.md`. That
declaration covers a run condition and polling described in text, a per-item `[]`
binding, fixed values and write calls; rule tests
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
