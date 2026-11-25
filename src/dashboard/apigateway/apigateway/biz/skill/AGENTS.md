# Skill Generation and Injection

Paths below start at `apigateway/apigateway/`. Shared terms (declaration, resource
definition) live in the DDD glossary. Callers outside `biz/` use
only the names exported from `biz/skill/__init__.py`.

Flow: `declaration.parse_declaration` → `validator.validate_declaration` →
`renderer.render_skill_body` → `writer.save_skill_version`. `syncer` runs that
flow for built-in declarations in `data/skill/declarations/`; the
`sync_platform_skills` command (`apps/skill/management/commands/`) wraps it and
runs from `bin/post_migrate`. Gateway Skill upload (`uploader`) runs the same
flow on the `declaration.yaml` of an uploaded package; downloads and file
previews rebuild the package from the stored version (`package`).

| Module | Owns |
| --- | --- |
| `declaration.py` | pydantic model of the declaration YAML; field rules and error messages |
| `refs.py` | reference syntax: a whole-string `${{ inputs.<name> }}` or `${{ steps.<id>.outputs.<path> }}`; any other value is fixed |
| `schema_converter.py` | OpenAPI schema converted to parameters and response fields |
| `resource_loader.py` | `SkillResource`, `ResourceProvider`, and loading the current release |
| `validator.py` | cross-checks between the orchestration and resource definitions |
| `renderer.py` | template context and the per-step OpenAPI snippet |
| `writer.py` | one transactional publish: metadata, tags, config, version, relations; version rules for both Skill types |
| `syncer.py` | per-declaration status for built-in injection |
| `frontmatter.py` | SKILL.md frontmatter rendering for download packages |
| `package.py` | download package: SKILL.md (frontmatter, H1 replaced by the display name, body) plus filled `references/`; optionally a `declaration.yaml` regenerated from the database |
| `archive.py` | in-memory zip reading: path, symlink, layout, declaration size and UTF-8 checks; lists ignored files |
| `uploader.py` | gateway Skill precheck and publish: package checks, ignored-file warning, form overlay, gateway-only `uses` |
| `manager.py` | basic info, current version, archive/restore and delete of an existing Skill |
| `skill.py` | `SkillHandler`: market/gateway/open querysets, filters, ordering, counts, tags, detail context, download count |

## Where to change what

- SKILL.md body wording or section order: `data/skill/templates/SKILL.md.j2`.
  The template uses `trim_blocks`/`lstrip_blocks`; keep the whitespace notes at
  its top. Context fields come from `renderer._SkillBodyContext`.
- `references/*.md`: `data/skill/references/`. The body links to these files;
  wording changes belong in the file itself.
- New declaration field or rule: `declaration.py`; reference checks against
  resources go in `validator._RefChecker`.

## Docstrings

Every function and method in this package has a docstring that says what it
does, followed by a `例如：` block of typical cases:

- Conversions and predicates: 2–4 `输入 -> 输出` lines.
- Validators (`_check_*`): the rule, then an accepted and a rejected value.
- Functions with side effects or that drive a flow: what they do, when they
  run, and a typical scenario in words.
- Trivial properties and lookups: one line, no example. `__init__` needs none.

pytest runs with `-p no:doctest`, so examples are not executed; update them
together with the code.

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
  guessed from the HTTP method. The step snippet copies `ResourceParam.schema`
  minus its top-level `description` and `x-` keys, and the parameter's
  `style`/`explode`/`allowReserved` (`ResourceParam.serialization`; drops the
  invalid query `style: simple` that Swagger 2.0 import writes);
  `responses` copies `SkillResource.response_schema` (the published first 2xx
  `application/json` schema) unchanged; `SkillResource.responses` is the
  flattened field list used only to look up reference paths and their types.
  `ResourceParam.type` and `ResponseField.type` are only for type comparisons,
  never for rebuilding a schema.
  Types are `schema_converter.SchemaType`: `from_schema` reads a schema,
  `SchemaType.parse` is the only parser of the declared text, `str()` prints it
  (union names sorted, `null` last) and `==` is the only comparison, so union
  order does not matter. Inputs and outputs declare a required `type` in that
  text (`string`, `array<object>`, `integer|string`, `array<string>|null`);
  `example` and `default` must match it. An input's `type` must equal every typed parameter
  it is bound to in `with`, and its interface description comes from those
  parameters, so every input must be bound at least once.
  Request bodies and responses are read only from `application/json`
  (`charset` and other parameters ignored); neither falls back to another
  content type. A first 2xx response with content but no `application/json`
  makes the resource unavailable with its own reason. An output's `type`
  must equal the type derived from its source: an input's `type`, or the
  response field's type wrapped in one `array<…>` per `[]` in the path and one
  more when the source step is a per-item call (`failed_host_logs` is
  `array<object>` while one call's `data` is `object`). An element of an array
  field (`data.tags[0]`, `data.tags[]`) is a response field typed as the array's
  item type. A response field without a type is not compared. A parameter
  bound to `${{ steps.* }}` must match its source type; per-item compares one
  element. An input's `description` is an optional orchestration
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
  `requestBody.required` comes from the definition and is independent of its
  properties: a required body is rendered even when no property is bound, and
  the caller sends `{}`.
  The declaration is rejected when a referenced resource's request body is not
  a top-level object in `application/json` (`charset` is ignored), when a resource has
  parameters of the same name in different locations (`with` binds by name), when
  its method is `ANY`, when a `{name}` in its path has no path parameter of that
  name in the definition, when a required or
  path parameter is missing from `with`, when a step maps a parameter missing
  from the definition, when a `${{ steps.* }}` reference names a response field
  missing from the definition, when an input's `type` or a step reference's
  source type differs from the bound parameter's type, when a required or path parameter is mapped from an
  optional input without a default, when a step's per-item parameters come
  from different arrays, or when an output's `type` differs from its source. Resource-level problems go
  in `SkillResource.errors`; the validator reports them as errors and skips
  field checks for that resource.
  Warnings are only for non-blocking resource facts, such as a non-public
  resource.
- Versions are plain `major.minor.patch` (`apps/skill/constants.SKILL_VERSION_PATTERN`):
  no pre-release or build suffix, no leading zeros, so they compare strictly as
  integer triples.
- The same declaration version as the current version is
  overwritten in place: changelog, orchestration, SKILL.md body, relations,
  metadata, tags and config. The version row and its `created_time` stay, so
  the download package datetime does not change. A version that already exists
  but is not current is still skipped. A new version must be higher than the
  current one, otherwise it is rejected: a lower version made current would leave
  the higher one skipped as "already exists" on every later deploy.
  `writer.check_version` owns the overwrite/skip/reject rule; `syncer` calls it
  before rendering and `save_skill_version` calls it again under the metadata
  row lock. Platform injection passes `overwrite_existing=True`; other callers
  still reject a duplicate version.
- Gateway Skills use `writer.check_gateway_version` instead: any existing
  version (not only the current one) may be overwritten when the uploader
  confirms `overwrite`, and that version becomes current; a new version must
  be higher than the highest existing version. Writing to an archived Skill
  raises `SkillArchivedError`.
- Injection skips and upload rejects. Built-in injection records a reason and
  leaves the declaration for the next deploy; a gateway upload returns every
  error to the uploader and writes nothing. Upload warnings do not block; the
  gateway rendering is always the stored body. An upload package and its
  uncompressed `declaration.yaml` are each at most
  `constants.SKILL_PACKAGE_MAX_SIZE`, the package has at most
  `constants.SKILL_PACKAGE_MAX_ENTRIES` entries, and it must contain `declaration.yaml`;
  other files, including `SKILL.md` and `references/`,
  pass the path checks but are never read or stored, and one warning lists
  them (the first few, then the total). A top-level `__MACOSX/` is ignored.
  `references/` always comes from `data/skill/references/`. The directory name must equal the package
  declaration's `name` before the form overrides `display_name`,
  `display_name_en`, `description`, `tags` and `version`; `name` and
  `changelog` come only from the declaration.
- `changelog` is one `{date, content}` mapping describing the declaration
  `version`; history lives in git. `date` is `YYYY-MM-DD` or
  `YYYY-MM-DD HH:MM:SS` without a time zone or fractional seconds; unquoted
  YAML dates/timestamps are accepted and a `T` separator is stored as a space.
  `SkillVersion.changelog` stores `{version, date, content}` as JSON.
- A written version snapshots the resource definitions at injection time.
  Gateway releases do not re-render built-in Skills. The next injection
  overwrites the current version, including a refreshed snapshot of those
  definitions. Bump `version` only when the change should be published as a
  new version. Do not auto-generate versions on release: they would collide
  with versions bumped in the repository, and hand-written step text would
  not be reviewed.
- Update `SkillMetadata` with `save(update_fields=...)` so concurrent
  `download_count` increments are kept.
- Injection reads only the database and repository files; it never calls
  gateways or external systems.
- Built-in declarations may use either edition's gateway name; the
  `sync_platform_skills` command builds the name mapping for `settings.EDITION`
  and passes it as `gateway_names`; `syncer` maps `uses` and `tags` with it.
- Rendering is deterministic: no timestamps or environment URLs in the body.
- The stored artifact is the body only; `SKILL.md.j2` does not render frontmatter.
  A download package's frontmatter is built from the Agent Skills spec and
  contains, in order, only `name`, `description`, `display_name`,
  `display_name_en` (`""` when empty) and `metadata`. `metadata` contains only
  `type`, `version`, `author`, `datetime`, and `source`. `datetime` is
  `SkillVersion.created_time`. Basic info is read from `SkillMetadata` at
  download time, so editing it changes the frontmatter and the H1 without a new
  version. Do not write `SkillMetadata.code` or the `SkillMetadata.metadata`
  extension JSON into `SKILL.md`. Only the gateway Skill management download
  and file list (`with_declaration=True`, file name suffix
  `constants.SKILL_DECLARATION_PACKAGE_SUFFIX`) include `declaration.yaml`;
  market and open downloads do not. The declaration is not stored: it is
  regenerated from current basic info plus the version's `version`,
  `changelog` and `orchestration`, without YAML anchors or aliases, so the
  package can be uploaded again as is.
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
POST parameters body. It is not a copy of the live OpenAPI document. A fixture
parameter normally gives `type`; it gives `schema` instead when the golden must
show a nested published schema (`global_var_list` of `execute_job_plan`). After an
intentional template change, regenerate `expected/` from the renderer and review
the diff; the rendered snippet must stay valid OpenAPI 3.1. Command output is
covered by `tests/apps/skill/management/commands/test_sync_platform_skills.py`.
