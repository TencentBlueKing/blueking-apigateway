# Web Plugin Guide

Source paths below start at `apigateway/apigateway/`. This API module is the
entrypoint for plugin catalog/configuration work across the owning lower layers.

## Data flow

These diagrams show payload storage, representation, and publishing. Validation
and scope-specific plugin names follow the rules below.

### Data Flow (new plugins)

```text
Frontend (raw YAML) ──POST──▶ PluginConfig.yaml (DB storage, as-is)

PluginConfig.yaml (DB) ──GET──▶ Frontend (raw YAML, as-is)

PluginConfig.yaml (DB) ──publish──▶ Service-layer convertor ──▶ APISIX config
                                    (DefaultPluginConvertor = identity, no conversion)
```

### Data Flow (legacy plugins only: `bk-rate-limit`, `bk-ip-restriction`)

```text
Frontend (form) ──POST──▶ PluginConfigYamlConvertor.to_internal_value() ──▶ DB storage
DB storage ──GET──▶ PluginConfigYamlConvertor.to_representation() ──▶ Frontend (form)
DB storage ──publish──▶ PluginConvertorFactory convertor ──▶ APISIX config
```

## Stored YAML and conversion

Web CRUD stores YAML in `PluginConfig.yaml`. `PluginConfigYamlConvertor` in
`apis/web/plugin/convertor.py` handles the existing `bk-rate-limit` and
`bk-ip-restriction` compatibility formats; other Web payloads pass through.
Keep that map limited to the two existing formats.

`PluginConvertorFactory` (`service/plugin/convertor.py`) has several existing
converters, including `AIProxyConvertor`; unknown enum values are not a generic
extension mechanism. Unregistered known plugin codes use identity conversion.
For new plugins, store APISIX-native YAML and use identity conversion rather than
adding another representation.

## Validation flow

`PluginConfigYamlValidator.validate` checks the stored-format YAML:

```text
payload → PluginConfigYamlChecker.check
  nonempty schema → yaml_loads → PluginConvertorFactory convertor → JSON Schema validation
  no/empty schema → checker-only validation
```

## Key components

| Component | Source | Role |
| --- | --- | --- |
| `PluginTypeCodeEnum` | `apps/plugin/constants.py` | Control-plane plugin codes |
| Catalog/schema fixtures | `fixtures/plugins.yaml` | Metadata, scope, visibility, schema references |
| `PluginConfigYamlChecker` | `service/plugin/checker.py` | Registered semantic checks |
| `PluginConfigYamlValidator` | `service/plugin/validator.py` | Checker and conditional schema validation |
| `PluginConfigYamlConvertor` | `apis/web/plugin/convertor.py` | Two legacy Web compatibility formats |
| `PluginConvertorFactory` | `service/plugin/convertor.py` | Stored config to APISIX representation |
| `PluginData` | `controller/release_data.py` | Scope-specific APISIX plugin-name mapping |

## Catalog and compatibility

- Add the code in `apps/plugin/constants.py` and metadata in
  `fixtures/plugins.yaml`. Match the supported APISIX Lua schema and priority
  from `blueking-apigateway-apisix/src/apisix/plugins/`.
- Fixture records are `schema.schema` and `plugin.plugintype`; link a schema by
  natural key `[plugin-code, plugin, '0']`, or use `schema: null` when absent.
  Preserve name translations, `_tags`, scope and intended `is_public` visibility.
- Add a `BaseChecker` and its registration in `service/plugin/checker.py` only
  for semantic validation or clearer errors that the schema does not provide.
  A missing registered checker is a no-op, not a reason to create an empty one.
- `controller/release_data.py:PluginData` maps names when scope-specific APISIX
  names differ, such as header rewrite. Generic CRUD/URL code needs no change
  for a catalog-only addition.
- Fixture visibility and resource compatibility are separate. Policy is in
  `service/plugin/compatibility.py`: AI-only plugins require AI resources;
  AI resources use the compatible set; controller-managed AI and OAuth2 codes
  cannot be resource-bound. Reuse `is_plugin_compatible_with_resource_kind()`
  at create, update and import boundaries.
- Stage validation remains permissive; AI Service filtering at publication is
  owned by the controller guide. Change compatibility sets only with an explicit
  product classification and corresponding tests.

## Coverage

Relevant focused targets are `tests/apis/web/plugin/`,
`tests/service/plugin/test_checkers.py`, `test_validators.py`, `test_convertors.py`,
`test_compatibility.py` in that service test directory, and controller tests when
publishing behavior changes. Inspect actual fixture records and their schema
references for catalog-only edits; do not require a checker/test when no custom
validation was added. Use the inherited Dashboard wrapper and gates.
