# API Resource OAuth2 Public and Personal Client Support Design

Status: design discussion approved; written specification awaiting review

Date: 2026-07-28

Target: `upstream/master`

## 1. Purpose

API resources currently support the legacy `X-Bkapi-Authorization` authentication
path. The APISIX runtime also has a complete Bearer OAuth2 path and an
`bk-oauth2-appcode-validate` plugin that can independently allow the built-in
`public` and `personal` client app codes.

This change lets each API resource opt into OAuth2 public and personal clients.
The resource configuration is versioned, publication generates the required
system-managed APISIX plugins, and Dashboard maintains the built-in resource
permissions required by resources that also enable application permission
checks.

The admission decision and the permission decision remain separate:

- `bk-oauth2-appcode-validate` is authoritative for whether a released Route
  accepts a built-in OAuth2 client type.
- `bk-permission` remains authoritative for resource permission when the
  resource enables application permission checks.
- Permission synchronization provisions the records required by
  `bk-permission`; it is not the OAuth2 client admission control.

## 2. Current State

MCP Server already exposes similarly named public and personal client switches,
but its permission flow has an additional proxy boundary:

1. The MCP gateway entry validates the OAuth2 token and audience.
2. mcp-proxy authorizes the real app code against the MCP Server.
3. mcp-proxy calls the target API with
   `v_mcp_{mcp_server_id}_{app_code}`, and the target API checks that virtual
   app code's resource permission.

Direct API OAuth2 calls do not have the mcp-proxy boundary. The token's literal
`public` or `personal` app code reaches the API Route, so any automatically
managed direct-API permission must use that literal app code. This design does
not change MCP Server permissions or `v_mcp_*` permissions.

The APISIX runtime behavior needed by this feature already exists:

- `bk-oauth2-protected-resource` prefers `X-Bkapi-Authorization` and otherwise
  selects the Bearer flow.
- `bk-oauth2-verify` verifies the token and populates the app, user, app code,
  and audience.
- `bk-oauth2-appcode-validate` independently supports `public` and `personal`.
- `bk-oauth2-audience-validate` validates the gateway API audience.
- `bk-auth-validate` enforces the released resource's user and application
  authentication requirements.
- `bk-permission` checks resource permissions only when the released resource
  requires them.

These runtime plugins are dependencies and regression boundaries, not
implementation targets for the first phase.

## 3. Goals

- Add independent resource-level switches for OAuth2 public and personal
  clients.
- Require user authentication whenever either OAuth2 client switch is enabled.
- Version the switches with the resource and allow different released versions
  in different environments.
- Apply the same behavior to `STANDARD` and `AI` resources.
- Generate the complete OAuth2 plugin bundle as system-managed Route
  configuration.
- Preserve the existing legacy authentication path.
- Automatically maintain literal `public` and `personal` resource permissions
  only when the released resource requires application permission checks.
- Reconcile permissions safely across multiple environments, versions, and
  data planes.
- Preserve a straightforward future extension point for ordinary SaaS Bearer
  clients without exposing that unsupported option in the first phase.

## 4. Non-goals

- Supporting ordinary SaaS app codes through Bearer OAuth2 tokens in the first
  phase.
- Changing the existing `X-Bkapi-Authorization` behavior.
- Changing APISIX OAuth2, authentication, audience, or permission plugin
  implementations.
- Changing mcp-proxy or MCP Server permission behavior.
- Adding an environment dimension to the existing permission tables.
- Changing the core-api permission query protocol.
- Adding a periodic permission reconciliation scheduler.
- Allowing users to bind, configure, or override the four system-managed OAuth2
  plugins.

## 5. Terminology and Field Mapping

The existing user-authentication field has different names at different
protocol layers. This change preserves those names instead of attempting a
cross-layer rename.

| Layer | User authentication field |
| --- | --- |
| Editing resource context and internal auth config | `auth_verified_required` |
| Some read-only response DTOs | `user_verified_required` |
| OpenAPI `authConfig` | `userVerifiedRequired` |
| APISIX `bk-resource-context` config | `verified_user_required` |

The new fields use the MCP Server internal naming convention:

```text
oauth2_public_client_enabled
oauth2_personal_client_enabled
```

OpenAPI `authConfig` uses the existing camelCase convention:

```text
oauth2PublicClientEnabled
oauth2PersonalClientEnabled
```

## 6. Resource Configuration Contract

Both fields belong to the resource authentication configuration:

```yaml
auth_config:
  auth_verified_required: true
  app_verified_required: true
  resource_perm_required: true
  oauth2_public_client_enabled: false
  oauth2_personal_client_enabled: false
```

Rules:

1. Both OAuth2 fields are independent booleans with a default of `false`.
2. If either OAuth2 field is `true`, `auth_verified_required` must be `true`.
3. Turning off user authentication in the frontend also turns off both OAuth2
   switches before saving.
4. Backend APIs validate the resulting desired state and reject an invalid
   combination. They do not silently publish OAuth2 with user authentication
   disabled.
5. Historical resource versions that do not contain the fields behave as
   though both values are `false`.
6. `app_verified_required` and `resource_perm_required` do not control whether
   OAuth2 is available. They only determine whether the accepted OAuth2 app
   code subsequently needs a synchronized resource permission.

The fields must survive every resource lifecycle path:

- Web create, update, detail, list, and batch operations.
- Automated resource synchronization.
- OpenAPI import.
- Resource version snapshot creation and reading.
- OpenAPI export and re-import.
- Released resource display.

## 7. System-managed Plugin Generation

If either OAuth2 switch is enabled, publication generates the following Route
plugins for both `STANDARD` and `AI` resources:

```yaml
bk-oauth2-protected-resource: {}
bk-oauth2-verify: {}
bk-oauth2-appcode-validate:
  support_public: <oauth2_public_client_enabled>
  support_personal: <oauth2_personal_client_enabled>
bk-oauth2-audience-validate: {}
```

If both switches are disabled, publication does not inject any of these plugins
for the resource.

The four plugins are controller-managed:

- They remain hidden from the public plugin catalog.
- Web, sync, and OpenAPI inputs cannot create or update their bindings.
- Publication writes their final configuration after loading user bindings, so
  a historical same-name binding cannot override the system configuration.
- Existing historical bindings are ignored or replaced at the publish
  boundary and are reported for cleanup; they do not block a safe publication.
- The same generation helper is used by standard and AI Route conversion so
  their behavior cannot drift.

The publication validator fails closed when any target data plane does not
support the complete plugin bundle. The error identifies the incompatible data
plane. Publication never silently omits an OAuth2 plugin or downgrades the
resource to legacy-only authentication.

## 8. Runtime Authentication Dependency

No APISIX runtime code changes are required.

When `X-Bkapi-Authorization` is present, the existing protected-resource plugin
selects the legacy path. The OAuth2 verify, app-code validation, and audience
plugins skip their Bearer-specific work. A request containing both
authentication headers continues to prefer `X-Bkapi-Authorization`.

When a request uses Bearer OAuth2, the existing plugins validate the token,
user, client type, audience, and optional resource permission. In the first
phase, an OAuth2 token whose app code is neither `public` nor `personal` is
rejected by the existing app-code validation plugin. Ordinary SaaS callers
remain supported through the legacy authentication header.

This flow is covered by generated-configuration and regression tests, but this
feature does not modify:

- `bk-oauth2-protected-resource`
- `bk-oauth2-verify`
- `bk-oauth2-appcode-validate`
- `bk-oauth2-audience-validate`
- `bk-auth-verify`
- `bk-auth-validate`
- `bk-permission`

## 9. Built-in Permission Ownership

For direct API permissions, literal `public` and `personal` are reserved,
system-managed app codes.

User-facing authorization, permission application, renewal, and deletion
operations reject both app codes. This includes Web APIs, open APIs, automated
APIs, and bulk operations. The rejection is based on the reserved app-code set,
not on the current grant type, so a caller cannot take over a system permission
by changing its operation path.

This restriction applies to gateway and resource permission surfaces. MCP
Server permission surfaces keep their existing, separate built-in-client
policy.

Automatically created resource permissions use a dedicated grant type:

```text
GrantTypeEnum.OAUTH2_BUILTIN = "oauth2_builtin"
```

The grant type provides auditability. The ownership contract is stronger than
the label: every literal `public` or `personal` resource permission is system
owned. MCP virtual app codes and ordinary SaaS app codes remain outside this
reconciler.

Permissions are non-expiring while required by a released OAuth2 resource.

## 10. Desired Permission Set

For one released environment, a resource requires a built-in permission for a
client type only when all conditions are true:

```text
the resource is not disabled in the environment
AND app_verified_required = true
AND resource_perm_required = true
AND the corresponding oauth2 client switch = true
```

The resource ID comes from the released `ResourceVersion` snapshot, not the
editing-area `Resource` table. This preserves permissions for a resource that
has been removed from the editing area but remains live in an older released
version.

For a gateway, the final desired set is the union of the required permissions
from every environment's current successfully released version:

```text
desired = union(
    required_permissions(release.resource_version, release.stage)
    for release in current_successful_releases(gateway)
)
```

Environment differences are safe because each environment's Route plugin
remains the admission authority. A permission retained for another environment
does not allow a client through a Route whose app-code plugin disables that
client type.

Editing-area state and failed release candidates never enter the final desired
set.

## 11. Two-phase Publication Coordination

Permission additions and removals have different safety properties, so
publication uses two phases.

### 11.1 Prepare before publication

Before sending the candidate configuration to any data plane:

1. Calculate the union of all current successful releases.
2. Replace the target environment's contribution with the candidate version's
   contribution.
3. Add any missing built-in permissions.
4. Do not delete any existing built-in permission.

The operation is idempotent. A failure to add required permissions aborts the
publication before a new OAuth2 Route can become active.

A failed publication may leave an extra permission row. That row is harmless:
the old live Route configuration remains authoritative and will not accept a
new client type merely because the permission exists.

### 11.2 Reconcile after publication

Deletion is allowed only when every currently active data plane for the target
environment has successfully published the target version and no other
environment in the gateway has an unresolved multi-data-plane publication.

After that condition is satisfied:

1. Treat the target version as the environment's current successful release.
2. Recompute the gateway-wide desired set from all current releases.
3. Add missing desired permissions defensively.
4. Delete system-owned permissions outside the desired set.

The reconciler must not treat the shared `Release` row as sufficient convergence
evidence. That row can point to the candidate after the first data plane
succeeds. It checks per-data-plane publish histories for all active bindings
before allowing gateway-wide deletion.

If any data plane in the gateway failed, timed out, is still publishing, or has
an unknown state, reconciliation is add-only. A data plane still running an
older Route may still need the older permission.

Environment revoke, gateway unbinding, and successful retry use the same final
reconciliation entry point after their data-plane state has converged.

## 12. Permission Reconciler Boundary

Dashboard owns one idempotent domain service with two public operations:

```text
prepare_publish(gateway, stage, candidate_version)
reconcile_gateway(gateway)
```

`prepare_publish` only adds. `reconcile_gateway` calculates and applies the
complete successful-release set when the gateway is converged. When any
environment is not converged, it may add known required permissions but must
not delete.

The service:

- Acquires a gateway-scoped lock before calculating and mutating permissions.
- Reads resource IDs and auth config from version snapshots.
- Applies additions and deletions in explicit database transactions.
- Uses bulk operations without modifying unrelated permission rows.
- Is safe to retry after task delivery or process failure.
- Logs the gateway, triggering stage and version, desired count, added count,
  deleted count, and reason without logging credentials or tokens.

Publication, revoke, retry, and the repair command call this service rather than
implementing independent permission calculations.

## 13. Failure and Recovery Semantics

- Invalid resource configuration fails before resource version publication.
- An incompatible data plane fails publication validation.
- A permission preparation failure aborts publication.
- A post-publication reconciliation failure does not roll back a successfully
  deployed Route. It leaves a safe permission superset and records a retryable
  failure.
- Deletion runs in one transaction. A deletion failure rolls back that
  reconciliation attempt instead of leaving a partially reduced set.
- An incomplete multi-data-plane publication never triggers deletion.
- An unresolved publication in any environment blocks deletion for the whole
  gateway; this prevents another environment's successful callback from
  deleting permissions still needed by the unresolved environment.
- Concurrent publication and retry tasks serialize through the gateway-scoped
  lock and then recalculate from current state.

The first phase includes an operator-facing Dashboard management command that:

- Reconciles one explicitly named gateway.
- Defaults to dry-run.
- Reports desired, missing, extra, and unchanged permission counts.
- Reports whether deletion is blocked by an unresolved data-plane state and
  identifies the affected environment and publication.
- Applies the same lock and reconciler when execution is requested.
- Supports controlled initialization and repair after rollout.

The first phase does not add a periodic task. Publish hooks, existing task
retries, and the repair command provide recovery.

## 14. Data-plane Compatibility

The publish validator checks every target data plane before permission
preparation and configuration distribution.

When any resource in the candidate version enables an OAuth2 client, each
target data plane must support:

- `bk-oauth2-protected-resource`
- `bk-oauth2-verify`
- `bk-oauth2-appcode-validate`
- `bk-oauth2-audience-validate`

The check applies equally to standard and AI resources. A mixed data-plane set
is rejected if any target is incompatible. Resources with both OAuth2 fields
disabled do not add a new compatibility requirement.

## 15. API and UI Behavior

The resource form displays public and personal OAuth2 switches only as part of
the authentication settings. The switches are configurable only while user
authentication is enabled.

When the user disables user authentication:

- The UI immediately turns both OAuth2 switches off.
- The submitted desired state includes both values as `false`.
- Backend validation still rejects any caller that explicitly submits an
  inconsistent combination.

Resource detail, version detail, and released resource views display the two
values using the terminology already used by MCP Server.

OpenAPI import and export map:

```text
oauth2PublicClientEnabled   <-> oauth2_public_client_enabled
oauth2PersonalClientEnabled <-> oauth2_personal_client_enabled
```

Exports include both values explicitly. Imports default missing values to
`false` and validate the user-authentication dependency.

## 16. Verification

### 16.1 Configuration contract

- Both fields default to `false`.
- Web, sync, and OpenAPI inputs accept valid combinations.
- All backend inputs reject OAuth2 enabled with user authentication disabled.
- Frontend user-authentication disablement resets both switches.
- Web, snapshot, version, export, and re-import round trips preserve both
  values.
- Tests cover the existing internal, response, OpenAPI, and APISIX user-field
  name mappings.
- Historical snapshots without either field behave as disabled.

### 16.2 Route publication

- Standard and AI resources each cover public-only, personal-only, both, and
  neither.
- Enabling either option produces all four plugins.
- The app-code plugin config exactly matches the resource fields.
- Disabling both options produces no system OAuth2 plugins.
- A historical same-name binding cannot override system configuration.
- Unsupported data-plane versions fail with an actionable error.

### 16.3 Permission coordination

- Only literal `public` and `personal` rows are managed.
- MCP `v_mcp_*` and ordinary SaaS permissions remain unchanged.
- The desired set covers multiple environments and different released
  versions.
- Disabled resources do not contribute permissions for that environment.
- Deleted editing-area resources still contribute while an old version is
  released.
- Application authentication and resource permission conditions are enforced.
- Preparation only adds.
- Failed and partial multi-data-plane publications never delete.
- Full success converges to the gateway-wide union.
- Repeated and concurrent reconciliation is idempotent and does not over-delete.
- Revoke and the management command converge the final set.
- All user permission mutation surfaces reject reserved app codes.

### 16.4 Regression gates

No APISIX runtime implementation test is added as product code in this
repository. Dashboard tests assert that generated Route configurations conform
to the existing plugin schemas and preserve the legacy path.

After implementation:

- Run focused Dashboard tests first.
- Run Dashboard edition setup, lint check, and the full test gate.
- Run dashboard-front type checking, lint, and focused unit tests.
- Report any integration or full gate that could not be run.

## 17. Rollout

1. Deploy data-plane versions containing the existing four OAuth2 plugins.
2. Deploy Dashboard fixture and compatibility metadata that treats the plugins
   as system managed.
3. Deploy the resource contract, publish conversion, permission reconciler, and
   UI.
4. Run the management command in dry-run mode for selected gateways and inspect
   literal `public` and `personal` permissions.
5. Apply reconciliation in a controlled rollout.
6. Publish new resource versions to opt resources into public or personal
   OAuth2 clients.

Pre-feature resource versions lack both fields and therefore contribute no
built-in permissions. Existing literal `public` or `personal` resource
permissions are considered reserved system state and are reported by dry-run
before controlled reconciliation removes or adopts them.

## 18. Future Ordinary SaaS Bearer Support

The first phase does not add a dormant `support_saas` option.

A future phase can add a third resource field and extend
`bk-oauth2-appcode-validate` so an OAuth2 app code other than `public` or
`personal` is accepted only when that field is enabled. Existing resources will
default the new field to `false`.

Ordinary SaaS applications will continue to use their own existing resource
permissions. They will not receive automatic built-in permissions from this
reconciler. The plugin remains the client-type admission gate, while
`bk-permission` remains the resource authorization gate.
