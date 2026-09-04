# OAS3 Resource Documentation Renderer Design

## Background

Dashboard currently generates resource Markdown documentation through
`bkapi-client-generator==0.1.30`. The Python package writes a temporary Swagger
2 document, starts a bundled Go executable, and uses a fork of `go-swagger` plus
two large Go templates to produce Markdown.

The current path also converts OpenAPI 3 operations back to Swagger 2 before
rendering. This creates an unnecessary format round trip and makes the Dashboard
runtime depend on a separately built Go binary.

This change replaces that path with a Dashboard-owned OAS3 presenter and a
Jinja2 Markdown template. It does not change SDK generation, which uses a
separate OpenAPI Generator worker.

## Goals

- Remove the `bkapi-client-generator` runtime dependency.
- Render resource documentation directly from OAS3 data with the existing
  Jinja2 dependency.
- Continue accepting Swagger 2 documents through the existing import API.
- Normalize Swagger 2 inputs to OAS3 before they reach the renderer.
- Preserve one generated Markdown document per gateway resource.
- Preserve the current public import, preview, synchronization, and persistence
  contracts.
- Keep the generated document structurally familiar while improving its
  organization, type expressions, and coverage.
- Use one common implementation for CE, EE, and TE.

## Non-goals

- Building a general-purpose OpenAPI documentation generator.
- Supporting OpenAPI features outside the subset accepted by Dashboard.
- Changing SDK generation.
- Regenerating existing `ResourceDoc` rows during deployment.
- Supporting custom user templates for generated OAS3 documentation.
- Maintaining byte-for-byte compatibility with the old Go templates.
- Running the old and new renderers behind a long-lived feature flag.

## Confirmed Constraints

- Output should remain structurally compatible, but headings, tables, and type
  expressions may be improved.
- Swagger 2 remains a supported input format.
- The renderer itself accepts only normalized OAS3.
- The supported feature boundary is the OpenAPI subset accepted by Dashboard,
  not all of OpenAPI 3.0 and 3.1.
- Existing database documentation is not backfilled. New output appears on the
  next preview, import, or synchronization.
- Jinja2 and PyYAML are already direct Dashboard dependencies; no new rendering
  dependency is required.

## Edition Analysis

The current implementation is common code. There are no EE or TE overrides for:

- `apigateway.biz.resource_doc`
- `apigateway.biz.openapi`
- Web or Open API resource-document import views
- resource-document templates

The active TE edition metadata also contains no external files under those
paths, and the TE edition repository contains no matching renderer, parser, or
`bkapi-client-generator` implementation.

The new presenter, template, exceptions, and tests must therefore remain in the
common Dashboard tree. The implementation must not introduce
`settings.EDITION` branches or edition-specific copies. EE and TE activation
must resolve to the same common source files.

## Architecture

The public parser interface remains unchanged:

```python
OpenAPIParser.parse(openapi, language) -> list[OpenAPIDoc]
OpenAPIParser.parse_resource_data(resources, language) -> list[OpenAPIDoc]
```

Both input paths converge on a resource dictionary whose `openapi_schema` uses
the Dashboard OAS3 representation:

```text
Swagger 2 or OAS3 document
    -> OpenAPIImportManager validation and parsing
    -> resource dict with normalized OAS3 openapi_schema
                                                \
resource import or preview DTO -----------------+-> single-operation OAS3 document
                                                    -> OperationDocBuilder
                                                    -> OperationDocContext
                                                    -> Jinja2 template
                                                    -> Markdown
```

`OpenAPIExportManager(include_bk_apigateway_resource=False)` produces the
single-operation OAS3 document. The resource input must be copied first because
the current exporter removes internal fields such as `openapi_schema.version`
while constructing an operation.

`OpenAPIDoc.openapi` stores the single-operation OAS3 YAML. It is not consumed
by production code today, so this removes the remaining Swagger 2 intermediate
representation without changing persistence or API output.

## Component Boundaries

### `OpenAPIParser`

The parser owns input validation, Swagger 2 compatibility, resource iteration,
and orchestration. It does not format Markdown or interpret display details.

`parse()` uses `OpenAPIImportManager` to validate the source document and obtain
normalized resources. `parse_resource_data()` continues to trust its already
validated resource DTOs and must not add a second OpenAPI validation pass.

Both methods call one private per-resource generation path. Resources using the
`ANY` method continue to be skipped.

### `OperationDocBuilder`

The presenter in `resource_doc/importer/presenters.py` is the only component
that understands OAS3 display semantics. It converts a single-operation OAS3
dictionary into immutable documentation dataclasses.

It owns:

- parameter grouping and display values;
- request and response media types;
- examples;
- schema type expressions;
- schema flattening;
- constraints;
- recursion and depth protection;
- deterministic ordering and Markdown-safe field values.

It must not mutate the supplied OAS3 dictionary.

### `OpenAPIToMarkdownGenerator`

The generator loads the built-in Jinja2 template and renders an
`OperationDocContext`. It does not accept file paths, write temporary files,
start subprocesses, or inspect raw OpenAPI structures.

The environment uses `SandboxedEnvironment`, `StrictUndefined`, no HTML
autoescaping, and a stable trailing-newline policy.

### Jinja2 template

One structural template is stored at:

```text
apigateway/apigateway/templates/resource_doc/openapi/operation.md.j2
```

The template receives only:

```python
template.render(doc=context, labels=DOC_LABELS[language])
```

Language-specific labels are small data mappings. There are no duplicated
Chinese and English structural templates.

The template controls layout only. It must not resolve references, infer schema
types, serialize examples, or navigate raw OAS3 dictionaries.

## Documentation View Model

The view model contains only values needed by the template:

```python
@dataclass(frozen=True)
class OperationDocContext:
    operation_id: str
    method: str
    path: str
    summary: str
    description: str
    deprecated: bool
    tags: list[str]
    parameters: list[ParameterDoc]
    request_body: RequestBodyDoc | None
    responses: list[ResponseDoc]


@dataclass(frozen=True)
class ParameterDoc:
    name: str
    location: str
    type: str
    required: bool
    description: str
    default: str
    example: str
    constraints: str


@dataclass(frozen=True)
class RequestBodyDoc:
    required: bool
    description: str
    contents: list[MediaTypeDoc]


@dataclass(frozen=True)
class ResponseDoc:
    status_code: str
    status_text: str
    description: str
    headers: list[ParameterDoc]
    contents: list[MediaTypeDoc]


@dataclass(frozen=True)
class MediaTypeDoc:
    media_type: str
    schema: SchemaDoc | None
    examples: list[ExampleDoc]


@dataclass(frozen=True)
class ExampleDoc:
    name: str
    summary: str
    value: str


@dataclass(frozen=True)
class SchemaDoc:
    type: str
    description: str
    fields: list[SchemaFieldDoc]
    example: str


@dataclass(frozen=True)
class SchemaFieldDoc:
    path: str
    type: str
    required: bool
    description: str
    constraints: str
    example: str
```

These are presentation models, not a second general OpenAPI object model. No
class hierarchy or pluggable renderer abstraction is introduced.

## Markdown Structure

Generated content starts at heading level three because it is embedded inside
an existing resource-document page:

```text
### API information
### Description
### Request parameters
#### Path parameters
#### Query parameters
### Request body
#### application/json
### Responses
#### 200 - OK
##### application/json
### Data models
```

Rules:

- API information includes HTTP method, path, operation ID, tags, and a visible
  deprecated marker.
- Parameters are grouped by `path`, `query`, `header`, and `cookie`.
- Request bodies and response bodies are grouped by media type.
- Responses first have a status summary table, followed by details only when a
  response has headers, schema, or examples.
- Empty sections are omitted.
- Chinese and English use identical structure and field coverage.

## Schema Presentation

The presenter flattens nested schema properties into field paths, so the Jinja2
template never performs recursive OpenAPI traversal. For example:

```text
user
user.name
user.roles
user.roles[]
```

Type expressions follow these rules:

- `type` plus `format` becomes `integer<int64>`.
- arrays become `array<T>`;
- OAS 3.0 `nullable` and OAS 3.1 null unions become `T | null`;
- `oneOf` and `anyOf` retain their variant types;
- safely mergeable `allOf` properties are displayed and the composition remains
  visible in the type expression;
- `additionalProperties` becomes `map<string, T>`;
- a schema with properties and no explicit type is treated as `object`.

The constraints column may include enum values, defaults, numeric bounds,
string-length bounds, and patterns. Missing optional values do not produce
placeholder text.

Schema traversal has an internal maximum depth of eight. Object identity is
tracked to stop recursive structures. A recursive or truncated field remains
visible with a descriptive marker but is not expanded further. The limit is not
user-configurable.

## Examples

Example selection follows this priority:

1. media-type `examples`;
2. media-type `example`;
3. schema `example`;
4. property `example`;
5. no generated example.

Named examples retain their name and summary. Dictionaries and arrays use
deterministic indented JSON blocks. Scalar values preserve their value. The
renderer does not fabricate sample payloads from schemas.

## Escaping and Determinism

The presenter normalizes values before they reach the template:

- escape Markdown table pipes;
- convert table-cell newlines into HTML line breaks;
- serialize structured examples with stable JSON indentation;
- preserve specification order where it is meaningful;
- apply stable ordering where source ordering is not meaningful;
- produce the same Markdown for identical OAS3, language, and template inputs.

Determinism is required because `BaseParser._enrich_docs()` compares Markdown
MD5 values to decide whether a `ResourceDoc` changed.

## Error Handling

A local `OpenAPIDocGenerationError` replaces exceptions imported from
`bkapi_client_generator`.

- Invalid OpenAPI remains a `SchemaValidationError`.
- Presenter failures and built-in template failures are logged server-side and
  exposed as `OpenAPIDocGenerationError`.
- Web and Open API views continue returning the current internal-error message
  for document-generation failures.
- Responses must not expose templates, OpenAPI payloads, or internal stack
  details.
- Existing `ResourceDocJinja2TemplateError` classes remain dedicated to
  user-supplied archive templates.

The stale `ExpandSwaggerError` catch is removed. The current parser does not
invoke the package's Swagger expansion function.

## Historical Data

There is no database migration or backfill. Existing `ResourceDoc` rows remain
unchanged and naturally adopt the new format on the next preview, import, or
synchronization.

This is required because `source=IMPORT` does not distinguish generated
OpenAPI documentation from user-imported Markdown. A bulk rewrite could
overwrite user-authored content.

## Dependency and Dead-code Removal

After the new path is active:

- remove `bkapi-client-generator` from `pyproject.toml` and regenerate
  `uv.lock`;
- remove `generate_markdown`, `GenerateMarkdownError`, and
  `ExpandSwaggerError` imports;
- remove `convert_operation_v3_to_v2` and its production-dead helper functions;
- remove tests that only cover the deleted OAS3-to-Swagger-2 conversion;
- search production code and tests for all deleted symbols and package names;
- do not retain proxy functions solely for old unit tests.

## Test Strategy

### Presenter tests

Cover operation metadata, all supported parameter locations, request bodies,
multiple media types, response headers, default responses, examples, nested
objects, arrays, maps, required properties, constraints, OAS 3.0 nullable,
OAS 3.1 null unions, compositions, recursion, maximum depth, Markdown escaping,
deterministic output, and input immutability.

### Renderer tests

Use representative OAS3 content to lock complete Chinese and English Markdown
output. Also cover empty sections, unsupported language, missing templates,
template syntax failures, and `StrictUndefined` failures.

### Parser integration tests

Cover Swagger 2 input, OAS 3.0 and 3.1 input, and already validated resource
DTO input. Assert one document per operation, `ANY` skipping, OAS3 content in
`OpenAPIDoc.openapi`, no repeated validation for resource DTOs, resource
matching, change detection, and unchanged persistence behavior.

### API tests

Assert that local generation errors preserve the existing Web and Open API V1
error response contract.

### Edition symmetry

Confirm that none of the new or changed renderer paths appear in edition
metadata or TE/EE override trees. Run the focused common tests under both TE and
EE activation when it is safe to switch editions. Because edition activation
can copy overlay files, use a clean isolated checkout or otherwise preserve and
verify unrelated worktree changes before switching.

## Verification

From `src/dashboard`:

```bash
uv run bash -lc \
  'cd apigateway && set -a && . apigateway/conf/unittest_env && set +a && \
   python -m pytest --nomigrations --ds apigateway.settings -q --tb=short \
   apigateway/tests/biz/resource_doc/impoter'

uv lock --check
uv run make edition-ee
uv run make lint-check
uv run make test
```

Run equivalent focused tests with the TE edition in a clean environment for the
edition-symmetry gate. Then run symbol and dependency scans:

```bash
rg 'bkapi_client_generator|bkapi-client-generator'
rg 'convert_operation_v3_to_v2|GenerateMarkdownError|ExpandSwaggerError'
```

Any remaining match must be either removed or explicitly justified as unrelated
historical documentation. Skipped or blocked verification must be reported.

## Implementation Sequence

1. Add behavior-focused presenter and renderer tests for the approved output.
2. Add documentation dataclasses and the OAS3 presenter.
3. Add the common Jinja2 template and localized label mappings.
4. Replace the subprocess generator with in-memory rendering.
5. Converge both parser input paths on single-operation OAS3 documents.
6. Replace external exceptions at API boundaries.
7. Remove the OAS3-to-Swagger-2 conversion path and dead tests.
8. Remove the dependency and refresh the lockfile.
9. Run focused, edition-symmetry, lint, full-test, and dead-code verification.

## Acceptance Criteria

- No runtime or lockfile dependency on `bkapi-client-generator` remains.
- No Go binary or subprocess is used to generate resource documentation.
- The renderer consumes only single-operation OAS3 data.
- Swagger 2 input still generates documentation through existing normalization.
- OAS 3.0 and 3.1 Dashboard-supported inputs render in Chinese and English.
- Generated Markdown follows the approved structure and deterministic rules.
- Existing import, preview, sync, error, and persistence contracts remain intact.
- Existing database documentation is not rewritten during deployment.
- CE, EE, and TE use the same common renderer, presenter, template, and tests.
- Focused tests, dependency checks, lint, full tests, edition checks, and
  dead-code scans pass or any blockage is explicitly reported.
