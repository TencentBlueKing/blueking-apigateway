# API Resource OAuth2 Public and Personal Client Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add backend support for versioned API-resource OAuth2 public/personal clients, system-managed APISIX Route plugins, and safe built-in resource-permission reconciliation.

**Architecture:** The resource auth context is the configuration source of truth and is copied into `ResourceVersion.data`. Route conversion derives the four OAuth2 plugins from that immutable snapshot. A Dashboard domain reconciler derives literal `public`/`personal` resource permissions from the union of released version snapshots, adds permissions before publication, and deletes only after per-data-plane publish histories prove that the whole gateway is converged.

**Tech Stack:** Python 3.14, Django, Django REST Framework, Pydantic v2, Celery, Redis locks, pytest, Ruff, mypy, import-linter.

## Global Constraints

- Scope is `src/dashboard` only. Do not modify `src/dashboard-front`.
- The current request does not authorize subagents. Execute in the current
  agent unless the user explicitly authorizes delegation later.
- Do not modify APISIX, mcp-proxy, MCP Server permissions, or core-api.
- Phase one accepts Bearer OAuth2 app codes `public` and `personal` only. Do not add a dormant SaaS switch.
- Preserve the existing user-auth field names at each boundary:
  - editing context: `auth_verified_required`
  - read DTOs: `user_verified_required`
  - OpenAPI: `userVerifiedRequired`
  - APISIX resource context: `verified_user_required`
- Both `STANDARD` and `AI` resources get identical OAuth2 behavior.
- A resource may enable either OAuth2 client only when `auth_verified_required` is true.
- The four OAuth2 Route plugins are system-managed and must win over any historical same-name resource binding.
- Direct API built-in permissions use literal `public` and `personal`; never create or alter `v_mcp_*`.
- Permission calculations read resource IDs and auth configuration from `ResourceVersion.data`, not the editing `Resource` table.
- Permission preparation is add/update-only. Deletion is allowed only after every active data-plane binding for every environment is in a known successful state.
- A shared `Release` row is not proof of convergence; use the latest `ReleaseHistory` and `PublishEvent` for each stage/data-plane pair.
- Keep unrelated worktree changes untouched.

## Repository Context

- Repository root: `/root/workspace/tx/wklken/blueking-apigateway`
- Dashboard command root: `/root/workspace/tx/wklken/blueking-apigateway/src/dashboard`
- Controlling rules:
  - `/root/workspace/tx/wklken/blueking-apigateway/AGENTS.md`
  - `/root/workspace/tx/wklken/blueking-apigateway/src/dashboard/AGENTS.md`
  - nearest `AGENTS.md` files under `apigateway/apigateway/biz`, `controller`, `service`, and `apis`
- Full gates:

```bash
cd /root/workspace/tx/wklken/blueking-apigateway/src/dashboard
uv run make edition-ee
uv run make lint-check
uv run make test
```

---

### Task 1: Add the resource authentication contract

**Files:**

- Modify: `src/dashboard/apigateway/apigateway/biz/resource/models.py`
- Modify: `src/dashboard/apigateway/apigateway/apis/web/resource/serializers.py`
- Modify: `src/dashboard/apigateway/apigateway/biz/resource/resource.py`
- Test: `src/dashboard/apigateway/apigateway/tests/biz/resource/test_models.py`
- Test: `src/dashboard/apigateway/apigateway/tests/apis/web/resource/test_serializers.py`
- Test: `src/dashboard/apigateway/apigateway/tests/apis/web/resource/test_views.py`

- [ ] **Step 1: Write failing model and serializer tests**

Add tests for:

- both fields defaulting to false;
- public-only, personal-only, and both-enabled valid states;
- either OAuth2 field with `auth_verified_required=false` being rejected;
- Web create/update responses preserving both values;
- historical input without either field remaining valid and reading as disabled.

Use this expected contract in the tests:

```python
expected_auth_config = {
    "auth_verified_required": True,
    "app_verified_required": True,
    "resource_perm_required": True,
    "oauth2_public_client_enabled": False,
    "oauth2_personal_client_enabled": False,
}
```

- [ ] **Step 2: Run the focused tests and confirm failure**

```bash
cd /root/workspace/tx/wklken/blueking-apigateway/src/dashboard
uv run bash -lc 'cd apigateway && set -a && . apigateway/conf/unittest_env && set +a && python -m pytest --nomigrations --ds apigateway.settings -q --tb=short apigateway/tests/biz/resource/test_models.py apigateway/tests/apis/web/resource/test_serializers.py apigateway/tests/apis/web/resource/test_views.py'
```

Expected: FAIL because the resource auth model and serializer do not expose or retain the two OAuth2 fields.

- [ ] **Step 3: Implement the Pydantic contract**

Extend `ResourceAuthConfig` with the exact fields and invariant:

```python
class ResourceAuthConfig(BaseModel):
    auth_verified_required: bool = Field(default=True)
    app_verified_required: bool = Field(default=True)
    resource_perm_required: bool = Field(default=True)
    oauth2_public_client_enabled: bool = Field(default=False)
    oauth2_personal_client_enabled: bool = Field(default=False)

    @model_validator(mode="after")
    def validate_oauth2_requires_user_auth(self):
        oauth2_enabled = self.oauth2_public_client_enabled or self.oauth2_personal_client_enabled
        if oauth2_enabled and not self.auth_verified_required:
            raise ValueError("OAuth2 public/personal clients require user authentication")
        return self
```

- [ ] **Step 4: Expose and validate the fields in DRF**

Add the two boolean fields to `ResourceAuthConfigSLZ`, both `required=False` with `default=False`. Validate through the same Pydantic contract so invalid Web input returns a DRF 400 instead of leaking a later Pydantic exception:

```python
def validate(self, attrs):
    try:
        return ResourceAuthConfig.model_validate(attrs).model_dump()
    except PydanticValidationError as err:
        raise serializers.ValidationError(str(err)) from err
```

Import Pydantic's exception with an unambiguous alias:

```python
from pydantic import ValidationError as PydanticValidationError
```

Update `ResourceHandler.get_default_auth_config()` to return both fields as false.

- [ ] **Step 5: Run the focused tests and confirm success**

Run the command from Step 2.

Expected: PASS.

- [ ] **Step 6: Commit the task**

```bash
git add src/dashboard/apigateway/apigateway/biz/resource/models.py \
  src/dashboard/apigateway/apigateway/apis/web/resource/serializers.py \
  src/dashboard/apigateway/apigateway/biz/resource/resource.py \
  src/dashboard/apigateway/apigateway/tests/biz/resource/test_models.py \
  src/dashboard/apigateway/apigateway/tests/apis/web/resource/test_serializers.py \
  src/dashboard/apigateway/apigateway/tests/apis/web/resource/test_views.py
git commit -m "feat(resource): add OAuth2 client auth settings"
```

---

### Task 2: Preserve the fields through OpenAPI import and export

**Files:**

- Modify: `src/dashboard/apigateway/apigateway/biz/openapi/parser.py`
- Modify: `src/dashboard/apigateway/apigateway/service/resource_version/openapi_export.py`
- Modify: `src/dashboard/apigateway/apigateway/biz/openapi/schemas/openapi_2.0_schema.json`
- Modify: `src/dashboard/apigateway/apigateway/biz/openapi/schemas/openapi_3.0_schema.json`
- Modify: `src/dashboard/apigateway/apigateway/biz/openapi/schemas/openapi_3.1_schema.json`
- Test: `src/dashboard/apigateway/apigateway/tests/biz/resource/importer/test_parser.py`
- Test: `src/dashboard/apigateway/apigateway/tests/biz/resource/importer/test_openapi.py`
- Test: `src/dashboard/apigateway/apigateway/tests/biz/resource_version/test_resource_version.py`

- [ ] **Step 1: Write failing round-trip and schema tests**

Cover OpenAPI 2.0, 3.0, and 3.1 with:

```yaml
authConfig:
  userVerifiedRequired: true
  appVerifiedRequired: true
  resourcePermissionRequired: true
  oauth2PublicClientEnabled: true
  oauth2PersonalClientEnabled: false
```

Assert:

- import maps camelCase to the internal snake_case fields;
- missing fields import as false;
- non-boolean values fail schema validation;
- `userVerifiedRequired=false` plus either OAuth2 field true fails resource validation;
- export includes both fields explicitly, including false values;
- export followed by import preserves both values;
- resource-version data created from editing contexts retains both values.

- [ ] **Step 2: Run the focused tests and confirm failure**

```bash
cd /root/workspace/tx/wklken/blueking-apigateway/src/dashboard
uv run bash -lc 'cd apigateway && set -a && . apigateway/conf/unittest_env && set +a && python -m pytest --nomigrations --ds apigateway.settings -q --tb=short apigateway/tests/biz/resource/importer/test_parser.py apigateway/tests/biz/resource/importer/test_openapi.py apigateway/tests/biz/resource_version/test_resource_version.py'
```

Expected: FAIL because the JSON schemas reject the new keys and the adapters omit them.

- [ ] **Step 3: Add parser and exporter mappings**

Parser:

```python
config = {
    "auth_verified_required": auth_config.get("userVerifiedRequired", True),
    "app_verified_required": auth_config.get("appVerifiedRequired", True),
    "resource_perm_required": auth_config.get("resourcePermissionRequired", True),
    "oauth2_public_client_enabled": auth_config.get("oauth2PublicClientEnabled", False),
    "oauth2_personal_client_enabled": auth_config.get("oauth2PersonalClientEnabled", False),
}
```

Exporter:

```python
config = {
    "userVerifiedRequired": auth_config.get("auth_verified_required", True),
    "appVerifiedRequired": auth_config.get("app_verified_required", True),
    "resourcePermissionRequired": auth_config.get("resource_perm_required", True),
    "oauth2PublicClientEnabled": auth_config.get("oauth2_public_client_enabled", False),
    "oauth2PersonalClientEnabled": auth_config.get("oauth2_personal_client_enabled", False),
}
```

Keep the existing rule that disables resource permission when application authentication is false.

- [ ] **Step 4: Extend all three OpenAPI extension schemas**

Add these properties under every `authConfig` definition:

```json
"oauth2PublicClientEnabled": {
  "type": "boolean"
},
"oauth2PersonalClientEnabled": {
  "type": "boolean"
}
```

Do not loosen `additionalProperties: false`.

- [ ] **Step 5: Run the focused tests and confirm success**

Run the command from Step 2.

Expected: PASS.

- [ ] **Step 6: Commit the task**

```bash
git add src/dashboard/apigateway/apigateway/biz/openapi/parser.py \
  src/dashboard/apigateway/apigateway/service/resource_version/openapi_export.py \
  src/dashboard/apigateway/apigateway/biz/openapi/schemas/openapi_2.0_schema.json \
  src/dashboard/apigateway/apigateway/biz/openapi/schemas/openapi_3.0_schema.json \
  src/dashboard/apigateway/apigateway/biz/openapi/schemas/openapi_3.1_schema.json \
  src/dashboard/apigateway/apigateway/tests/biz/resource/importer/test_parser.py \
  src/dashboard/apigateway/apigateway/tests/biz/resource/importer/test_openapi.py \
  src/dashboard/apigateway/apigateway/tests/biz/resource_version/test_resource_version.py
git commit -m "feat(openapi): preserve resource OAuth2 settings"
```

---

### Task 3: Make OAuth2 plugins system-managed and inject them into Routes

**Files:**

- Modify: `src/dashboard/apigateway/apigateway/apps/plugin/constants.py`
- Modify: `src/dashboard/apigateway/apigateway/service/plugin/compatibility.py`
- Modify: `src/dashboard/apigateway/apigateway/biz/openapi/validate.py`
- Modify: `src/dashboard/apigateway/apigateway/controller/convertor/route.py`
- Test: `src/dashboard/apigateway/apigateway/tests/service/plugin/test_compatibility.py`
- Test: `src/dashboard/apigateway/apigateway/tests/apis/web/plugin/test_views.py`
- Test: `src/dashboard/apigateway/apigateway/tests/biz/resource/importer/test_openapi.py`
- Test: `src/dashboard/apigateway/apigateway/tests/controller/convertor/test_route.py`

- [ ] **Step 1: Write failing ownership and Route tests**

Test:

- Web create/update rejects all four OAuth2 plugin codes for resource bindings;
- non-official OpenAPI/sync input rejects all four codes;
- official built-in definition import can retain its historical YAML-managed OAuth2 bindings;
- standard and AI resources each cover neither, public-only, personal-only, and both;
- enabling either flag injects all four plugins;
- the app-code plugin contains the exact `support_public` and `support_personal` values;
- both false injects none;
- a historical same-name resource binding is overwritten by generated system configuration.

Expected plugin map for public-only:

```python
expected = {
    "bk-oauth2-protected-resource": {},
    "bk-oauth2-verify": {},
    "bk-oauth2-appcode-validate": {
        "support_public": True,
        "support_personal": False,
    },
    "bk-oauth2-audience-validate": {},
}
```

- [ ] **Step 2: Run the focused tests and confirm failure**

```bash
cd /root/workspace/tx/wklken/blueking-apigateway/src/dashboard
uv run bash -lc 'cd apigateway && set -a && . apigateway/conf/unittest_env && set +a && python -m pytest --nomigrations --ds apigateway.settings -q --tb=short apigateway/tests/service/plugin/test_compatibility.py apigateway/tests/apis/web/plugin/test_views.py apigateway/tests/biz/resource/importer/test_openapi.py apigateway/tests/controller/convertor/test_route.py'
```

Expected: FAIL because the app-code enum is missing, the plugins are user-configurable by code, and Route conversion does not derive them from auth config.

- [ ] **Step 3: Define the complete system-managed set**

Add the missing enum:

```python
BK_OAUTH2_APPCODE_VALIDATE = EnumField(
    "bk-oauth2-appcode-validate",
    label=_("OAuth2 应用编码验证"),
)
```

Define the set from enum values:

```python
OAUTH2_SYSTEM_MANAGED_PLUGIN_CODES = frozenset(
    {
        PluginTypeCodeEnum.BK_OAUTH2_PROTECTED_RESOURCE.value,
        PluginTypeCodeEnum.BK_OAUTH2_VERIFY.value,
        PluginTypeCodeEnum.BK_OAUTH2_APPCODE_VALIDATE.value,
        PluginTypeCodeEnum.BK_OAUTH2_AUDIENCE_VALIDATE.value,
    }
)

CONTROLLER_MANAGED_PLUGIN_CODES = (
    frozenset({"ai-proxy", "ai-proxy-multi"})
    | OAUTH2_SYSTEM_MANAGED_PLUGIN_CODES
)
```

Add the app-code plugin to `AI_COMPATIBLE_PLUGIN_CODES`.

Preserve official built-in YAML imports with an explicit opt-in parameter:

```python
def is_plugin_compatible_with_resource_kind(
    plugin_code: str,
    resource_kind: str | None,
    *,
    allow_controller_managed: bool = False,
) -> bool:
    if plugin_code in CONTROLLER_MANAGED_PLUGIN_CODES:
        return allow_controller_managed

    if plugin_code in AI_ONLY_PLUGIN_CODES:
        return resource_kind == ResourceKindEnum.AI.value

    if resource_kind == ResourceKindEnum.AI.value:
        return plugin_code in AI_COMPATIBLE_PLUGIN_CODES

    return True
```

Web callers keep the default false. OpenAPI validation passes
`allow_controller_managed=self.gateway.is_official` so the existing official
`bk-apigateway-resources.yaml` entries remain importable.

- [ ] **Step 4: Generate the Route plugin bundle after user bindings**

Add one helper used by both Route kinds:

```python
def _build_oauth2_plugins(self, resource: Dict[str, Any]) -> Dict[str, Plugin]:
    auth_config = json.loads(resource["contexts"]["resource_auth"]["config"])
    support_public = auth_config.get("oauth2_public_client_enabled", False)
    support_personal = auth_config.get("oauth2_personal_client_enabled", False)
    if not support_public and not support_personal:
        return {}

    return {
        "bk-oauth2-protected-resource": Plugin(),
        "bk-oauth2-verify": Plugin(),
        "bk-oauth2-appcode-validate": Plugin(
            support_public=support_public,
            support_personal=support_personal,
        ),
        "bk-oauth2-audience-validate": Plugin(),
    }
```

In `_convert_standard_route` and `_convert_ai_route`, call:

```python
plugins.update(self._build_oauth2_plugins(resource))
```

Place this after loading snapshot plugin bindings so system configuration wins.

- [ ] **Step 5: Run the focused tests and confirm success**

Run the command from Step 2.

Expected: PASS.

- [ ] **Step 6: Commit the task**

```bash
git add src/dashboard/apigateway/apigateway/apps/plugin/constants.py \
  src/dashboard/apigateway/apigateway/service/plugin/compatibility.py \
  src/dashboard/apigateway/apigateway/biz/openapi/validate.py \
  src/dashboard/apigateway/apigateway/controller/convertor/route.py \
  src/dashboard/apigateway/apigateway/tests/service/plugin/test_compatibility.py \
  src/dashboard/apigateway/apigateway/tests/apis/web/plugin/test_views.py \
  src/dashboard/apigateway/apigateway/tests/biz/resource/importer/test_openapi.py \
  src/dashboard/apigateway/apigateway/tests/controller/convertor/test_route.py
git commit -m "feat(controller): inject resource OAuth2 plugins"
```

---

### Task 4: Reject publication to incompatible data planes

**Files:**

- Modify: `src/dashboard/apigateway/apigateway/apps/data_plane/constants.py`
- Modify: `src/dashboard/apigateway/apigateway/biz/release/gateway_releaser.py`
- Modify: `src/dashboard/apigateway/apigateway/controller/publisher/publish.py`
- Add: `src/dashboard/apigateway/apigateway/tests/apps/data_plane/test_constants.py`
- Test: `src/dashboard/apigateway/apigateway/tests/biz/release/test_release.py`
- Test: `src/dashboard/apigateway/apigateway/tests/controller/publisher/test_publish.py`

- [ ] **Step 1: Write failing compatibility tests**

Cover:

- versions below 3.16 are incompatible;
- 3.16 and later are compatible;
- invalid version strings fail closed;
- a candidate with any OAuth2-enabled resource rejects a mixed 3.13/3.16 target set and names the 3.13 data plane;
- a candidate with both fields false adds no new restriction;
- rolling update/re-enable of an existing OAuth2 release performs the same per-data-plane check.

- [ ] **Step 2: Run the focused tests and confirm failure**

```bash
cd /root/workspace/tx/wklken/blueking-apigateway/src/dashboard
uv run bash -lc 'cd apigateway && set -a && . apigateway/conf/unittest_env && set +a && python -m pytest --nomigrations --ds apigateway.settings -q --tb=short apigateway/tests/apps/data_plane/test_constants.py apigateway/tests/biz/release/test_release.py apigateway/tests/controller/publisher/test_publish.py'
```

Expected: FAIL because only AI gateway compatibility is currently checked.

- [ ] **Step 3: Add an OAuth2 data-plane compatibility helper**

The runtime evidence is:

- `blueking-apigateway-apisix` release 1.22 uses APISIX 3.13 and does not contain `bk-oauth2-appcode-validate`;
- release 1.23 uses APISIX 3.16 and contains all four plugins.

Implement:

```python
OAUTH2_RESOURCE_MIN_APISIX_VERSION = DataPlaneApisixVersionEnum.V3_16.value
OAUTH2_RESOURCE_APISIX_VERSION_ERROR = (
    f"OAuth2 public/personal resource clients require APISIX "
    f"{OAUTH2_RESOURCE_MIN_APISIX_VERSION} or later"
)


def is_apisix_version_supported_for_oauth2_resource(apisix_version: str) -> bool:
    try:
        return Version(apisix_version) >= Version(OAUTH2_RESOURCE_MIN_APISIX_VERSION)
    except (InvalidVersion, TypeError):
        return False


def get_oauth2_resource_data_planes_compatibility_error(
    data_planes: Iterable[tuple[str, str]],
) -> str | None:
    incompatible = [
        f"{name} ({apisix_version})"
        for name, apisix_version in data_planes
        if not is_apisix_version_supported_for_oauth2_resource(apisix_version)
    ]
    if not incompatible:
        return None
    return f"{OAUTH2_RESOURCE_APISIX_VERSION_ERROR}; incompatible data planes: {', '.join(incompatible)}"
```

- [ ] **Step 4: Detect OAuth2 use from version snapshots and validate all targets**

Use a local helper that defaults missing fields to false:

```python
def _resource_version_uses_oauth2(resource_version: ResourceVersion) -> bool:
    for resource in resource_version.data:
        auth_config = json.loads(resource["contexts"]["resource_auth"]["config"])
        if auth_config.get("oauth2_public_client_enabled", False):
            return True
        if auth_config.get("oauth2_personal_client_enabled", False):
            return True
    return False
```

Call the compatibility helper:

- in `GatewayReleaser._pre_release()` before permission preparation and task creation;
- in rolling-update publication for each existing `Release` before distribution.

Raise the existing publication error type with the actionable message.

- [ ] **Step 5: Run the focused tests and confirm success**

Run the command from Step 2.

Expected: PASS.

- [ ] **Step 6: Commit the task**

```bash
git add src/dashboard/apigateway/apigateway/apps/data_plane/constants.py \
  src/dashboard/apigateway/apigateway/biz/release/gateway_releaser.py \
  src/dashboard/apigateway/apigateway/controller/publisher/publish.py \
  src/dashboard/apigateway/apigateway/tests/apps/data_plane/test_constants.py \
  src/dashboard/apigateway/apigateway/tests/biz/release/test_release.py \
  src/dashboard/apigateway/apigateway/tests/controller/publisher/test_publish.py
git commit -m "feat(release): validate OAuth2 data plane support"
```

---

### Task 5: Reserve built-in app codes across ordinary permission APIs

**Files:**

- Modify: `src/dashboard/apigateway/apigateway/apps/permission/constants.py`
- Add: `src/dashboard/apigateway/apigateway/apps/permission/migrations/0014_add_oauth2_builtin_grant_type.py`
- Modify: `src/dashboard/apigateway/apigateway/biz/validators.py`
- Modify: `src/dashboard/apigateway/apigateway/biz/permission/permission.py`
- Modify: `src/dashboard/apigateway/apigateway/biz/permission/manager.py`
- Modify: `src/dashboard/apigateway/apigateway/apis/web/permission/serializers.py`
- Modify: `src/dashboard/apigateway/apigateway/apis/web/permission/views.py`
- Modify: `src/dashboard/apigateway/apigateway/apis/open/permission/serializers.py`
- Modify: `src/dashboard/apigateway/apigateway/apis/v2/open/serializers.py`
- Modify: `src/dashboard/apigateway/apigateway/apis/v2/inner/serializers.py`
- Modify: `src/dashboard/apigateway/apigateway/apis/v2/sync/serializers.py`
- Test: `src/dashboard/apigateway/apigateway/tests/apis/web/permission/test_serializers.py`
- Test: `src/dashboard/apigateway/apigateway/tests/apis/web/permission/test_views.py`
- Test: `src/dashboard/apigateway/apigateway/tests/apis/open/permission/test_serializers.py`
- Add: `src/dashboard/apigateway/apigateway/tests/apis/v2/open/test_serializers.py`
- Add: `src/dashboard/apigateway/apigateway/tests/apis/v2/inner/test_serializers.py`
- Test: `src/dashboard/apigateway/apigateway/tests/apis/v2/sync/test_views.py`

- [ ] **Step 1: Write failing reserved-code tests**

For both `public` and `personal`, assert rejection by ordinary direct-API:

- permission application;
- active grant;
- renewal;
- revoke/delete;
- bulk renewal/delete containing a reserved permission ID;
- Web, v1 open, v2 open, v2 inner, and v2 sync inputs.

Also assert:

- ordinary SaaS app codes are unchanged;
- MCP Server permission serializers and views are not affected;
- a reserved row cannot be deleted or renewed based only on a caller-provided permission ID.
- an older pending application for a reserved app code cannot be approved into
  a permission.

- [ ] **Step 2: Run the focused tests and confirm failure**

```bash
cd /root/workspace/tx/wklken/blueking-apigateway/src/dashboard
uv run bash -lc 'cd apigateway && set -a && . apigateway/conf/unittest_env && set +a && python -m pytest --nomigrations --ds apigateway.settings -q --tb=short apigateway/tests/apis/web/permission apigateway/tests/apis/open/permission apigateway/tests/apis/v2/open/test_serializers.py apigateway/tests/apis/v2/inner/test_serializers.py apigateway/tests/apis/v2/sync/test_views.py'
```

Expected: FAIL because direct permission APIs currently accept arbitrary valid app codes and IDs.

- [ ] **Step 3: Add the ownership constants and grant type**

```python
OAUTH2_BUILTIN_APP_CODES = frozenset({"public", "personal"})


class GrantTypeEnum(StructuredEnum):
    INITIALIZE = EnumField("initialize", label=_("主动授权"))
    APPLY = EnumField("apply", label=_("申请审批"))
    RENEW = EnumField("renew", label=_("续期"))
    AUTO_RENEW = EnumField("auto_renew", label=_("自动续期"))
    SYNC = EnumField("sync", label=_("按网关授权同步"))
    OAUTH2_BUILTIN = EnumField("oauth2_builtin", label=_("OAuth2 内置应用授权"))
```

Generate and inspect the migration:

```bash
cd /root/workspace/tx/wklken/blueking-apigateway/src/dashboard
uv run bash -lc 'cd apigateway && python manage.py makemigrations permission --name add_oauth2_builtin_grant_type'
```

The migration may alter Django field metadata/choices but must not add a new table or column.

- [ ] **Step 4: Implement reusable app-code and permission-ID guards**

Add a field validator:

```python
class UserManagedBKAppCodeValidator:
    requires_context = False

    def __call__(self, value: str):
        if value in OAUTH2_BUILTIN_APP_CODES:
            raise serializers.ValidationError(
                _("应用 {app_code} 的 API 权限由系统管理。").format(app_code=value)
            )
```

Add a list validator for revoke payloads:

```python
class UserManagedBKAppCodeListValidator:
    requires_context = False

    def __call__(self, values: List[str]):
        reserved = sorted(set(values) & OAUTH2_BUILTIN_APP_CODES)
        if reserved:
            raise serializers.ValidationError(
                _("应用 {app_codes} 的 API 权限由系统管理。").format(
                    app_codes=", ".join(reserved)
                )
            )
```

Add a handler guard for ID-based mutation:

```python
@staticmethod
def validate_user_managed_permissions(queryset) -> None:
    reserved = sorted(
        set(
            queryset.filter(
                bk_app_code__in=OAUTH2_BUILTIN_APP_CODES
            ).values_list("bk_app_code", flat=True)
        )
    )
    if reserved:
        raise serializers.ValidationError(
            _("应用 {app_codes} 的 API 权限由系统管理。").format(
                app_codes=", ".join(reserved)
            )
        )
```

Call the guard before every ID-based renew/delete mutation. Do not put this
restriction in the model manager because the system reconciler must be able to
mutate its own rows.

Call the app-code guard from both permission-dimension
`handle_permission_apply()` implementations before approving an existing
application record. This closes the legacy-pending-record path even when the
current serializer is bypassed.

- [ ] **Step 5: Apply the field/list validator to every ordinary permission serializer**

Attach the validator to all direct API `target_app_code`, `bk_app_code`, and
`target_app_codes` mutation inputs. Do not attach it to list/read filters or
MCP Server permission serializers.

For example:

```python
target_app_code = serializers.CharField(
    max_length=32,
    required=True,
    validators=[BKAppCodeValidator(), UserManagedBKAppCodeValidator()],
)
```

- [ ] **Step 6: Run tests and migration drift check**

Run the command from Step 2, then:

```bash
cd /root/workspace/tx/wklken/blueking-apigateway/src/dashboard
uv run bash -lc 'cd apigateway && python manage.py makemigrations --check'
```

Expected: tests PASS; migration check exits 0 with no new changes.

- [ ] **Step 7: Commit the task**

Stage only the files actually changed after the serializer call-site audit:

```bash
git add src/dashboard/apigateway/apigateway/apps/permission/constants.py \
  src/dashboard/apigateway/apigateway/apps/permission/migrations/0014_add_oauth2_builtin_grant_type.py \
  src/dashboard/apigateway/apigateway/biz/validators.py \
  src/dashboard/apigateway/apigateway/biz/permission/permission.py \
  src/dashboard/apigateway/apigateway/biz/permission/manager.py \
  src/dashboard/apigateway/apigateway/apis/web/permission \
  src/dashboard/apigateway/apigateway/apis/open/permission \
  src/dashboard/apigateway/apigateway/apis/v2/open/serializers.py \
  src/dashboard/apigateway/apigateway/apis/v2/inner/serializers.py \
  src/dashboard/apigateway/apigateway/apis/v2/sync/serializers.py \
  src/dashboard/apigateway/apigateway/tests/apis/web/permission \
  src/dashboard/apigateway/apigateway/tests/apis/open/permission \
  src/dashboard/apigateway/apigateway/tests/apis/v2/open/test_serializers.py \
  src/dashboard/apigateway/apigateway/tests/apis/v2/inner/test_serializers.py \
  src/dashboard/apigateway/apigateway/tests/apis/v2/sync/test_views.py
git commit -m "feat(permission): reserve OAuth2 built-in app codes"
```

---

### Task 6: Implement the gateway-scoped permission reconciler

**Files:**

- Add: `src/dashboard/apigateway/apigateway/biz/permission/oauth2_builtin.py`
- Modify: `src/dashboard/apigateway/apigateway/biz/permission/__init__.py`
- Add: `src/dashboard/apigateway/apigateway/tests/biz/permission/test_oauth2_builtin.py`

- [ ] **Step 1: Write failing desired-set tests**

Construct real `Gateway`, `Stage`, `ResourceVersion`, `Release`,
`ReleaseHistory`, `PublishEvent`, `DataPlane`, and binding rows. Cover:

- public-only, personal-only, both, and neither;
- `app_verified_required=false` contributes nothing;
- `resource_perm_required=false` contributes nothing;
- a resource disabled in one stage contributes nothing for that stage;
- multiple stages and different versions produce a union;
- a resource deleted from editing still contributes from an older released snapshot;
- inactive stages do not contribute to the final desired set;
- prepare replaces only the target stage contribution with the candidate and never deletes;
- existing desired reserved rows are normalized to non-expiring `oauth2_builtin`;
- unrelated SaaS and `v_mcp_*` permissions are unchanged;
- partial/failed/unknown per-data-plane state sets `deletion_blocked=true`;
- all latest stage/data-plane histories successful allows deletion;
- repeated calls are idempotent.

Use a snapshot factory with the real storage shape:

```python
def make_resource_snapshot(
    resource_id: int,
    *,
    stage_name: str,
    support_public: bool,
    support_personal: bool,
    app_verified_required: bool = True,
    resource_perm_required: bool = True,
    disabled: bool = False,
) -> dict:
    return {
        "id": resource_id,
        "name": f"resource-{resource_id}",
        "disabled_stages": [stage_name] if disabled else [],
        "contexts": {
            "resource_auth": {
                "config": json.dumps(
                    {
                        "auth_verified_required": True,
                        "app_verified_required": app_verified_required,
                        "resource_perm_required": resource_perm_required,
                        "oauth2_public_client_enabled": support_public,
                        "oauth2_personal_client_enabled": support_personal,
                    }
                )
            }
        },
    }
```

- [ ] **Step 2: Run the new tests and confirm failure**

```bash
cd /root/workspace/tx/wklken/blueking-apigateway/src/dashboard
uv run bash -lc 'cd apigateway && set -a && . apigateway/conf/unittest_env && set +a && python -m pytest --nomigrations --ds apigateway.settings -q --tb=short apigateway/tests/biz/permission/test_oauth2_builtin.py'
```

Expected: FAIL because the module does not exist.

- [ ] **Step 3: Define the result and blocker contracts**

```python
BuiltinPermission = tuple[str, int]


@dataclass(frozen=True)
class ReconciliationBlocker:
    stage_id: int
    stage_name: str
    data_plane_id: int
    data_plane_name: str
    release_history_id: int | None
    status: str


@dataclass(frozen=True)
class OAuth2BuiltinPermissionResult:
    desired: frozenset[BuiltinPermission]
    missing: frozenset[BuiltinPermission]
    extra: frozenset[BuiltinPermission]
    unchanged: frozenset[BuiltinPermission]
    normalized: frozenset[BuiltinPermission]
    deletion_blocked: bool
    blockers: tuple[ReconciliationBlocker, ...]
    applied: bool
```

- [ ] **Step 4: Implement snapshot contribution calculation**

```python
def required_permissions(resource_version: ResourceVersion, stage: Stage) -> set[BuiltinPermission]:
    required: set[BuiltinPermission] = set()
    for resource in resource_version.data:
        if stage.name in resource.get("disabled_stages", []):
            continue

        auth_config = json.loads(resource["contexts"]["resource_auth"]["config"])
        if not auth_config.get("app_verified_required", True):
            continue
        if not auth_config.get("resource_perm_required", True):
            continue

        resource_id = resource["id"]
        if auth_config.get("oauth2_public_client_enabled", False):
            required.add(("public", resource_id))
        if auth_config.get("oauth2_personal_client_enabled", False):
            required.add(("personal", resource_id))
    return required
```

Final desired state uses active stages only. If the gateway is inactive, the
final desired set is empty. `prepare_publish` starts from current active stage
contributions, removes the target stage's current contribution, and adds the
candidate contribution even when the stage has not yet become active.

- [ ] **Step 5: Implement per-data-plane convergence detection**

For every existing `Release` row and every currently active data-plane binding:

1. select the newest `ReleaseHistory` for `(gateway, stage, data_plane)`;
2. require it to exist;
3. read its latest `PublishEvent`;
4. require status `success`;
5. for an active stage, require the history version to equal the shared
   `Release.resource_version_id`.

Return an explicit blocker for missing, doing, failure, timeout-derived failure,
unknown, or version mismatch states. Include inactive stages because a
multi-data-plane revoke must converge before their permissions can be deleted.

The latest status lookup must use the existing method:

```python
latest_event_map = (
    PublishEvent.objects.get_release_history_id_to_latest_publish_event_map(
        release_history_ids
    )
)
status = latest_event.get_release_history_status()
```

- [ ] **Step 6: Implement dry-run planning and transactional application**

Use one gateway-scoped Redis lock:

```python
with Lock(
    f"oauth2_builtin_permission:{gateway.id}",
    timeout=settings.REDIS_PUBLISH_LOCK_TIMEOUT,
    try_get_times=settings.REDIS_PUBLISH_LOCK_RETRY_GET_TIMES,
):
    return self._reconcile_locked(gateway, apply=apply)
```

Inside the lock:

- select only literal `public`/`personal` resource permissions for the gateway;
- calculate missing, extra, unchanged, and rows needing normalization;
- on apply, use one `transaction.atomic()` block;
- `bulk_create(..., ignore_conflicts=True)` missing rows;
- update desired rows to:

```python
{
    "expires": NeverExpiresTime.time,
    "grant_type": GrantTypeEnum.OAUTH2_BUILTIN.value,
    "handled_by": "system",
}
```

- delete extras only when there are no blockers;
- never touch ordinary app codes or MCP virtual app codes.

Expose exactly:

```python
class OAuth2BuiltinPermissionReconciler:
    def prepare_publish(
        self,
        gateway: Gateway,
        stage: Stage,
        candidate_version: ResourceVersion,
    ) -> OAuth2BuiltinPermissionResult:
        return self._run(
            gateway,
            candidate=(stage, candidate_version),
            allow_delete=False,
            apply=True,
        )

    def reconcile_gateway(
        self,
        gateway: Gateway,
        *,
        apply: bool = True,
    ) -> OAuth2BuiltinPermissionResult:
        return self._run(
            gateway,
            candidate=None,
            allow_delete=True,
            apply=apply,
        )
```

- [ ] **Step 7: Run the focused tests and confirm success**

Run the command from Step 2.

Expected: PASS.

- [ ] **Step 8: Commit the task**

```bash
git add src/dashboard/apigateway/apigateway/biz/permission/oauth2_builtin.py \
  src/dashboard/apigateway/apigateway/biz/permission/__init__.py \
  src/dashboard/apigateway/apigateway/tests/biz/permission/test_oauth2_builtin.py
git commit -m "feat(permission): reconcile OAuth2 built-in grants"
```

---

### Task 7: Integrate preparation and reconciliation with publication lifecycle

**Files:**

- Modify: `src/dashboard/apigateway/apigateway/biz/release/gateway_releaser.py`
- Modify: `src/dashboard/apigateway/apigateway/controller/tasks/release.py`
- Modify: `src/dashboard/apigateway/apigateway/controller/tasks/syncing.py`
- Modify: `src/dashboard/apigateway/apigateway/controller/publisher/publish.py`
- Modify: `src/dashboard/apigateway/apigateway/biz/stage/stage.py`
- Modify: `src/dashboard/apigateway/apigateway/apps/data_plane/management/commands/bind_gateways_to_data_plane.py`
- Modify: `src/dashboard/apigateway/apigateway/apps/data_plane/management/commands/unbind_gateways_from_data_plane.py`
- Test: `src/dashboard/apigateway/apigateway/tests/biz/release/test_release.py`
- Add: `src/dashboard/apigateway/apigateway/tests/controller/tasks/test_release.py`
- Test: `src/dashboard/apigateway/apigateway/tests/controller/tasks/test_syncing.py`
- Test: `src/dashboard/apigateway/apigateway/tests/controller/publisher/test_publish.py`
- Test: `src/dashboard/apigateway/apigateway/tests/biz/stage/test_stage.py`
- Test: `src/dashboard/apigateway/apigateway/tests/apps/data_plane/test_management_commands.py`

- [ ] **Step 1: Write failing lifecycle tests**

Test:

- version publication calls `prepare_publish` after ordinary validation and
  distributor connection checks but before any release task is queued;
- preparation failure aborts publication and records a validation failure;
- first successful data-plane callback reconciles add-only because another
  data plane is doing;
- last successful callback permits full reconciliation;
- failed/timed-out data plane never causes deletion;
- rolling update and gateway re-enable prepare current released permissions
  before distribution;
- successful rolling update reconciles;
- successful stage disable/revoke reconciles only after per-data-plane state
  allows it;
- stage delete reconciles after synchronous revoke and `Release` deletion;
- successful data-plane unbind reconciles against the remaining active
  bindings;
- retries remain idempotent.

- [ ] **Step 2: Run focused lifecycle tests and confirm failure**

```bash
cd /root/workspace/tx/wklken/blueking-apigateway/src/dashboard
uv run bash -lc 'cd apigateway && set -a && . apigateway/conf/unittest_env && set +a && python -m pytest --nomigrations --ds apigateway.settings -q --tb=short apigateway/tests/biz/release/test_release.py apigateway/tests/controller/tasks/test_release.py apigateway/tests/controller/tasks/test_syncing.py apigateway/tests/controller/publisher/test_publish.py apigateway/tests/biz/stage/test_stage.py apigateway/tests/apps/data_plane/test_management_commands.py'
```

Expected: FAIL because lifecycle code does not call the reconciler.

- [ ] **Step 3: Prepare permissions before version publication**

In `GatewayReleaser._pre_release()`, after all candidate validation and data-plane
connection checks succeed:

```python
try:
    OAuth2BuiltinPermissionReconciler().prepare_publish(
        self.gateway,
        self.stage,
        self.resource_version,
    )
except Exception as err:
    message = f"prepare OAuth2 built-in permissions failed: {err}"
    history = self._save_release_history(data_plane=data_planes[0])
    PublishEventReporter.report_config_validate_failure(history, message)
    raise ReleaseError(message) from err
```

No release task may be queued after this failure.

- [ ] **Step 4: Reconcile after successful version-publish callbacks**

At the end of `update_release_data_after_success`, after updating `Release`,
stage status, released resources, docs, and MCP-related resource names:

```python
try:
    OAuth2BuiltinPermissionReconciler().reconcile_gateway(release.gateway)
except Exception:
    logger.exception(
        "reconcile OAuth2 built-in permissions failed after release success: "
        "gateway_id=%s, publish_id=%s",
        release.gateway_id,
        publish_id,
    )
```

Do not re-raise: a post-publication reconciliation failure must not make a
successfully distributed Route look unpublished.

- [ ] **Step 5: Cover rolling update, enable, and revoke**

Before distributing a rolling update for each `Release`, call
`prepare_publish(release.gateway, release.stage, release.resource_version)`.
Treat preparation failure as a publish failure and do not enqueue that release.

After a successful `rolling_update_release`:

```python
OAuth2BuiltinPermissionReconciler().reconcile_gateway(release.gateway)
```

After a successful non-delete `revoke_release`, call reconciliation after the
stage has been marked inactive. Catch/log post-distribution reconciliation
errors without reversing the successful revoke.

- [ ] **Step 6: Cover stage deletion and data-plane unbinding**

After synchronous stage revoke, `Release` deletion, and stage deletion commit,
call:

```python
OAuth2BuiltinPermissionReconciler().reconcile_gateway(gateway)
```

Retain the gateway instance before deleting the stage.

In both explicit data-plane unbind commands, reconcile every successfully
unbound gateway after the binding is removed. Dry-run command modes must not
invoke reconciliation.

- [ ] **Step 7: Run the focused tests and confirm success**

Run the command from Step 2.

Expected: PASS.

- [ ] **Step 8: Commit the task**

```bash
git add src/dashboard/apigateway/apigateway/biz/release/gateway_releaser.py \
  src/dashboard/apigateway/apigateway/controller/tasks/release.py \
  src/dashboard/apigateway/apigateway/controller/tasks/syncing.py \
  src/dashboard/apigateway/apigateway/controller/publisher/publish.py \
  src/dashboard/apigateway/apigateway/biz/stage/stage.py \
  src/dashboard/apigateway/apigateway/apps/data_plane/management/commands/bind_gateways_to_data_plane.py \
  src/dashboard/apigateway/apigateway/apps/data_plane/management/commands/unbind_gateways_from_data_plane.py \
  src/dashboard/apigateway/apigateway/tests/biz/release/test_release.py \
  src/dashboard/apigateway/apigateway/tests/controller/tasks/test_release.py \
  src/dashboard/apigateway/apigateway/tests/controller/tasks/test_syncing.py \
  src/dashboard/apigateway/apigateway/tests/controller/publisher/test_publish.py \
  src/dashboard/apigateway/apigateway/tests/biz/stage/test_stage.py \
  src/dashboard/apigateway/apigateway/tests/apps/data_plane/test_management_commands.py
git commit -m "feat(release): coordinate OAuth2 built-in permissions"
```

---

### Task 8: Add a dry-run-first repair command

**Files:**

- Add: `src/dashboard/apigateway/apigateway/apps/permission/management/commands/reconcile_oauth2_builtin_permissions.py`
- Add: `src/dashboard/apigateway/apigateway/tests/apps/permission/management/__init__.py`
- Add: `src/dashboard/apigateway/apigateway/tests/apps/permission/management/commands/__init__.py`
- Add: `src/dashboard/apigateway/apigateway/tests/apps/permission/management/commands/test_reconcile_oauth2_builtin_permissions.py`

- [ ] **Step 1: Write failing command tests**

Cover:

- `--gateway` is required and resolves one exact gateway name;
- default invocation is dry-run and changes no rows;
- `--apply` performs reconciliation;
- output includes desired, missing, extra, unchanged, normalized, and applied;
- blocked deletion reports stage, data plane, release history ID, and status;
- unknown gateway raises `CommandError`;
- repeated apply is idempotent.

- [ ] **Step 2: Run the command tests and confirm failure**

```bash
cd /root/workspace/tx/wklken/blueking-apigateway/src/dashboard
uv run bash -lc 'cd apigateway && set -a && . apigateway/conf/unittest_env && set +a && python -m pytest --nomigrations --ds apigateway.settings -q --tb=short apigateway/tests/apps/permission/management/commands/test_reconcile_oauth2_builtin_permissions.py'
```

Expected: FAIL because the command does not exist.

- [ ] **Step 3: Implement the command**

Use an explicit apply flag:

```python
def add_arguments(self, parser):
    parser.add_argument("--gateway", required=True, help="Gateway name")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes; without this flag the command is dry-run",
    )
```

Run the shared reconciler:

```python
gateway = Gateway.objects.filter(name=options["gateway"]).first()
if gateway is None:
    raise CommandError(f"gateway not found: {options['gateway']}")

result = OAuth2BuiltinPermissionReconciler().reconcile_gateway(
    gateway,
    apply=options["apply"],
)
```

Print deterministic sorted rows/counts. For every blocker, use this exact
formatting code:

```python
self.stdout.write(
    "blocked "
    f"stage={blocker.stage_name}({blocker.stage_id}) "
    f"data_plane={blocker.data_plane_name}({blocker.data_plane_id}) "
    f"release_history={blocker.release_history_id} "
    f"status={blocker.status}"
)
```

- [ ] **Step 4: Run the command tests and confirm success**

Run the command from Step 2.

Expected: PASS.

- [ ] **Step 5: Commit the task**

```bash
git add src/dashboard/apigateway/apigateway/apps/permission/management/commands/reconcile_oauth2_builtin_permissions.py \
  src/dashboard/apigateway/apigateway/tests/apps/permission/management
git commit -m "feat(permission): add OAuth2 grant repair command"
```

---

### Task 9: Run cross-module verification and perform the final scope audit

**Files:**

- Verify all files changed by Tasks 1-8.
- Do not add product changes unless a verification failure directly proves they are required.

- [ ] **Step 1: Run all focused feature tests together**

```bash
cd /root/workspace/tx/wklken/blueking-apigateway/src/dashboard
uv run bash -lc 'cd apigateway && set -a && . apigateway/conf/unittest_env && set +a && python -m pytest --nomigrations --ds apigateway.settings -q --tb=short \
apigateway/tests/biz/resource/test_models.py \
apigateway/tests/apis/web/resource/test_serializers.py \
apigateway/tests/apis/web/resource/test_views.py \
apigateway/tests/biz/resource/importer/test_parser.py \
apigateway/tests/biz/resource/importer/test_openapi.py \
apigateway/tests/biz/resource_version/test_resource_version.py \
apigateway/tests/service/plugin/test_compatibility.py \
apigateway/tests/apis/web/plugin/test_views.py \
apigateway/tests/controller/convertor/test_route.py \
apigateway/tests/apps/data_plane/test_constants.py \
apigateway/tests/biz/release/test_release.py \
apigateway/tests/biz/permission/test_oauth2_builtin.py \
apigateway/tests/apis/web/permission \
apigateway/tests/apis/open/permission \
apigateway/tests/apis/v2/open/test_serializers.py \
apigateway/tests/apis/v2/inner/test_serializers.py \
apigateway/tests/apis/v2/sync/test_views.py \
apigateway/tests/controller/tasks/test_release.py \
apigateway/tests/controller/tasks/test_syncing.py \
apigateway/tests/controller/publisher/test_publish.py \
apigateway/tests/biz/stage/test_stage.py \
apigateway/tests/apps/data_plane/test_management_commands.py \
apigateway/tests/apps/permission/management/commands/test_reconcile_oauth2_builtin_permissions.py'
```

Expected: PASS with no skipped feature tests.

- [ ] **Step 2: Run migration and OpenAPI drift checks**

```bash
cd /root/workspace/tx/wklken/blueking-apigateway/src/dashboard
uv run bash -lc 'cd apigateway && python manage.py makemigrations --check'
uv run make edition-ee
uv run make lint-check
```

Expected: all commands exit 0.

- [ ] **Step 3: Run the full Dashboard test gate**

```bash
cd /root/workspace/tx/wklken/blueking-apigateway/src/dashboard
uv run make edition-ee
uv run make test
```

Expected: PASS. If an unrelated pre-existing failure occurs, preserve the full
command output and prove whether the focused feature tests still pass.

- [ ] **Step 4: Audit exact scope and forbidden changes**

```bash
cd /root/workspace/tx/wklken/blueking-apigateway
git status --short
git diff --check upstream/master...HEAD
git diff --stat upstream/master...HEAD
git diff --name-only upstream/master...HEAD
git diff --name-only upstream/master...HEAD | rg '^src/dashboard-front/'
git diff -U0 upstream/master...HEAD -- src/dashboard | rg '^\+.*support_saas'
rg -n "v_mcp_" \
  src/dashboard/apigateway/apigateway/biz/permission/oauth2_builtin.py
```

Confirm:

- no `src/dashboard-front` file changed;
- no APISIX, mcp-proxy, or core-api file changed;
- no SaaS Bearer switch exists;
- no reconciler code manages `v_mcp_*`;
- all new system permissions are literal `public`/`personal`, non-expiring, and
  use `oauth2_builtin`;
- every Route injection uses version snapshot auth config;
- both standard and AI paths use the same helper;
- every user mutation entry found by the final `rg` call is guarded.

- [ ] **Step 5: Commit only verification-driven fixes, if any**

If verification required no fixes, do not create an empty commit. If a direct
fix was required, list the literal changed paths with `git status --short`,
stage only the proven fix and its regression test, inspect `git diff --cached`,
then commit with `fix(oauth2): address integration verification`. Do not use a
broad `git add`.

## Final Self-Review Checklist

- [ ] Every approved design requirement is mapped to at least one task and test.
- [ ] `src/dashboard-front` is explicitly excluded.
- [ ] No task modifies an out-of-scope runtime component.
- [ ] No code snippet contains a speculative SaaS option.
- [ ] Internal, OpenAPI, and APISIX user-auth field names remain distinct.
- [ ] Historical resource versions default both new values to false.
- [ ] Route plugin generation is system-owned and occurs after snapshot bindings.
- [ ] Data-plane compatibility is checked for both version publish and rolling update.
- [ ] Reserved-code guards cover app-code inputs and permission-ID mutations.
- [ ] Permission desired state comes only from released/candidate snapshots.
- [ ] Prepare never deletes.
- [ ] Reconcile never deletes while any stage/data-plane state is unresolved.
- [ ] Shared `Release` state is never used alone as convergence proof.
- [ ] Stage disable, stage delete, rolling update, enable, retry, and unbind paths converge through one service.
- [ ] The repair command is dry-run by default.
- [ ] Focused tests, migration check, lint, and full Dashboard tests have explicit commands and expected outcomes.
