# Plugin System Guide (for AI Agents)

This document describes how the plugin subsystem works in the dashboard backend and how to add a new APISIX plugin.

## Architecture Overview

Plugins are APISIX plugins managed through the dashboard. The dashboard stores plugin configs, validates them, and publishes them to APISIX during gateway release.

### Data Flow (new plugins)

```
Frontend (raw YAML) ──POST──▶ PluginConfig.yaml (DB storage, as-is)

PluginConfig.yaml (DB) ──GET──▶ Frontend (raw YAML, as-is)

PluginConfig.yaml (DB) ──publish──▶ Service-layer convertor ──▶ APISIX config
                                    (DefaultPluginConvertor = identity, no conversion)
```

### Data Flow (legacy plugins only: `bk-rate-limit`, `bk-ip-restriction`)

```
Frontend (form) ──POST──▶ PluginConfigYamlConvertor.to_internal_value() ──▶ DB storage
DB storage ──GET──▶ PluginConfigYamlConvertor.to_representation() ──▶ Frontend (form)
DB storage ──publish──▶ PluginConvertorFactory convertor ──▶ APISIX config
```

**`PluginConfigYamlConvertor` is ONLY for these 2 legacy plugins. Do NOT add new entries to it.**

### Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| **PluginTypeCodeEnum** | `apps/plugin/constants.py` | Enum of all plugin type codes |
| **Fixtures** | `fixtures/plugins.yaml` | Schema, PluginType, PluginForm definitions (loaded via `loaddata`) |
| **Checker** | `service/plugin/checker.py` (`PluginConfigYamlChecker`) | Plugin-specific validation with human-readable error messages |
| **Validator** | `service/plugin/validator.py` (`PluginConfigYamlValidator`) | Orchestrates checker + JSON Schema validation |
| **Service-layer convertor** | `service/plugin/convertor.py` (`PluginConvertorFactory`) | Converts DB storage format to APISIX-native config for publishing. New plugins use `DefaultPluginConvertor` (identity) automatically |
| **API-layer convertor (LEGACY)** | `apis/web/plugin/convertor.py` (`PluginConfigYamlConvertor`) | **Legacy only** — used by `bk-rate-limit` and `bk-ip-restriction`. Do NOT add new plugins here |
| **Release mapping** | `controller/release_data.py` (`PluginData`) | Maps plugin type_code to APISIX plugin name (only needed when they differ) |

### Validation Flow (on create/update)

```
PluginConfigYamlValidator.validate(type_code, yaml_payload, schema)
  │
  ├─1─▶ PluginConfigYamlChecker(type_code).check(payload)
  │       └── Dispatches to plugin-specific BaseChecker subclass (if registered)
  │           Raises ValueError with human-readable messages
  │
  └─2─▶ PluginConvertorFactory.get_convertor(type_code).convert(yaml_loads(payload))
          └── jsonschema.validate(converted_config, schema)
              Validates against the JSON Schema from fixtures/plugins.yaml
```

The checker runs **before** schema validation. Its errors are more readable than raw JSON Schema errors.

### Two Convertor Systems

There are two independent convertor layers.

**1. API-layer convertor — LEGACY ONLY, do NOT use for new plugins** (`apis/web/plugin/convertor.py`):
- `PluginConfigYamlConvertor` with `to_internal_value()` / `to_representation()`
- **Only 2 legacy plugins use this: `bk-rate-limit` and `bk-ip-restriction`**
- Do NOT add new entries to `type_code_to_convertor`
- For all other plugins (including new ones), data passes through unchanged

**2. Service-layer convertor** (`service/plugin/convertor.py`):
- `PluginConvertorFactory` with `get_convertor()` returning a `PluginConvertor`
- If no convertor registered, returns `DefaultPluginConvertor` (identity — returns config unchanged)
- Also used in validation: schema validation runs against the **converted** output
- New plugins should NOT register a service-layer convertor either — store data in APISIX-native format so `DefaultPluginConvertor` works

### Rule for New Plugins

> **New plugins must NOT have any convertor (neither API-layer nor service-layer).**
> Store data in APISIX-native format directly.
> The form data = DB storage = APISIX config. `DefaultPluginConvertor` (identity) handles it automatically.
>
> `PluginConfigYamlConvertor` is frozen — it only serves 2 legacy plugins and must not be extended.

## How to Add a New Plugin

### Files to Modify (typically 3 files)

#### 1. `apps/plugin/constants.py` — Add enum

Add a new member to `PluginTypeCodeEnum`:
```python
BK_MY_PLUGIN = EnumField("bk-my-plugin", label=_("插件中文名"))
```

#### 2. `fixtures/plugins.yaml` — Add fixture entries

Append 3 records at the end of the file:

**a) `schema.schema`** — JSON Schema for validating the plugin config (matches the Lua plugin's schema):
```yaml
- model: schema.schema
  fields:
    created_time: 2025-01-01 00:00:00.000000+00:00
    updated_time: 2025-01-01 00:00:00.000000+00:00
    name: bk-my-plugin       # must match the plugin code
    type: plugin
    version: '0'
    _schema: |-
      { ... JSON Schema ... }
    description: '-'
    example: '-'
```

Set `schema: null` in the plugintype entry if no schema validation is needed.

**b) `plugin.plugintype`** — Plugin type catalog entry:
```yaml
- model: plugin.plugintype
  fields:
    code: bk-my-plugin        # APISIX plugin name
    name: 中文名
    name_en: English Name
    is_public: true            # false = hidden from normal users
    scope: stage_and_resource  # or: stage, resource
    priority: 17460            # match the Lua plugin's priority
    _tags: "流量,Traffic"       # comma-separated zh,en tag pairs
    schema:                    # FK to schema.schema (or null)
    - bk-my-plugin
    - plugin
    - '0'
```

**c) `plugin.pluginform`** — Form definition for the frontend:
```yaml
- model: plugin.pluginform
  fields:
    language: ''               # '' = default/zh-cn
    type:
      - bk-my-plugin
    notes: Description of what the plugin does.
    style: raw                 # raw = YAML textarea, dynamic = form-driven
    default_value: |-          # pre-filled YAML for new configs
      key: value
    config: ''                 # JSON form schema (for style: dynamic), empty for raw
    example: |-                # usage examples shown in the UI
      key: value
```

Form styles:
- `raw` — user edits YAML directly in a textarea; best for complex/nested configs
- `dynamic` — rendered from JSON schema in `config` field; best for simple flat configs

#### 3. `service/plugin/checker.py` — Add checker (optional but recommended)

Create a `BaseChecker` subclass and register it:

```python
class MyPluginChecker(BaseChecker):
    def check(self, payload: str):
        loaded_data = yaml_loads(payload)
        if not loaded_data:
            raise ValueError("YAML cannot be empty")
        # ... plugin-specific validation ...

# Register in PluginConfigYamlChecker.type_code_to_checker:
PluginTypeCodeEnum.BK_MY_PLUGIN.value: MyPluginChecker(),
```

The checker validates things that JSON Schema cannot express well (e.g., cross-field dependencies, semantic rules, better error messages).

If no checker is registered, `PluginConfigYamlChecker.check()` is a no-op for that plugin type.

### Files You Usually Do NOT Modify

| File | Why not |
|------|---------|
| `apis/web/plugin/convertor.py` | **FROZEN.** `PluginConfigYamlConvertor` is legacy-only (serves `bk-rate-limit` and `bk-ip-restriction`). Never add new entries |
| `service/plugin/convertor.py` | `DefaultPluginConvertor` (identity) is used automatically for new plugins. Do not register new convertors |
| `controller/release_data.py` | Only needed if APISIX plugin name differs by scope (e.g., `bk-header-rewrite` → `bk-stage-header-rewrite` / `bk-resource-header-rewrite`) |
| `apis/web/plugin/views.py` | Generic CRUD views handle all plugins |
| `apis/web/plugin/serializers.py` | Generic serializers handle all plugins |
| `apis/web/plugin/urls.py` | URL routing is plugin-agnostic |

### Testing

Add tests in `tests/service/plugin/test_checkers.py` following the existing pattern:

```python
class TestMyPluginChecker:
    @pytest.mark.parametrize(
        "data, ctx",
        [
            (valid_data, does_not_raise()),
            (invalid_data, pytest.raises(ValueError)),
        ],
    )
    def test_check(self, data, ctx):
        checker = MyPluginChecker()
        with ctx:
            checker.check(yaml_dumps(data))
```

Run tests:
```bash
cd src/dashboard/apigateway && \
  set -a; . apigateway/conf/unittest_env; set +a; \
  python3 -m pytest --nomigrations --ds apigateway.settings -x -q --tb=short \
  apigateway/tests/service/plugin/test_checkers.py
```

### Checklist

- [ ] Add enum to `PluginTypeCodeEnum` in `apps/plugin/constants.py`
- [ ] Add `schema.schema` entry in `fixtures/plugins.yaml` (derive from the Lua plugin's schema)
- [ ] Add `plugin.plugintype` entry in `fixtures/plugins.yaml`
- [ ] Add `plugin.pluginform` entry in `fixtures/plugins.yaml`
- [ ] Add checker in `service/plugin/checker.py` and register in `type_code_to_checker`
- [ ] Add tests for the checker in `tests/service/plugin/test_checkers.py`
- [ ] Verify: no API-layer convertor needed (new plugin rule)
- [ ] Verify: no service-layer convertor needed (store APISIX-native format)
- [ ] Verify: no `release_data.py` mapping needed (plugin name = APISIX name)

### Reference: Lua Plugin Schema

The APISIX plugin Lua files live in the `blueking-apigateway-apisix` repo under `src/apisix/plugins/`. The `schema` table in the Lua file defines the JSON Schema that the dashboard's `_schema` fixture entry should match. The `priority` field in the Lua file should match the `priority` in the plugintype fixture.
