# OAuth2 Client Scope List Design

## Status

Approved in design discussion on 2026-08-03. This document covers the Dashboard inner APIs consumed by the bkauth personal/public token generation page. It does not implement the APIs.

## 1. Purpose

bkauth needs two read-only lists for choosing token authorization scope:

- MCP Servers that enable the requested OAuth2 client type.
- API resources that enable the requested OAuth2 client type in at least one currently released resource version.

Both lists are grouped and paginated by gateway. The design targets approximately 10,000 gateways, 100,000 API resources, 3,000 MCP Servers, and a peak of 20-30 requests per second.

## 2. Goals

- Support the fixed client types `personal` and `public`.
- Return only externally visible gateways and child objects.
- Merge API resources across every resource version currently referenced by `Release`.
- Paginate gateways rather than child objects.
- Keep query count fixed and avoid per-gateway or per-child queries.
- Avoid parsing nested resource-version JSON during every list request.
- Preserve multi-tenant gateway visibility rules.

## 3. Non-goals

- No token creation or authorization mutation.
- No change to existing permission-application APIs.
- No `disabled_stages` handling.
- No Redis or application-level response cache in the first implementation.
- No full-text or external search index in the first implementation.
- No changes to mcp-proxy, operator, or APISIX.

## 4. Existing Data Semantics

### 4.1 API resources

`ReleasedResource` stores one row per `(gateway_id, resource_version_id, resource_id)`. It has no stage or environment column. A current release maps a stage to a resource version through `Release.resource_version_id`.

The list must not treat every `ReleasedResource` row as current. A successful publication normally deletes rows no longer referenced by a release, and explicit resource-version deletion also deletes the corresponding rows. Stage deletion can remove `Release` without immediately deleting the now-orphaned `ReleasedResource` rows. Therefore current `Release` references, not cleanup state, define the query boundary.

The effective API set is:

```text
all ReleasedResource rows whose (gateway_id, resource_version_id)
is still referenced by Release
```

The same resource may occur in more than one referenced version. It is included once when at least one referenced snapshot simultaneously has:

```text
is_public = true
AND requested OAuth2 client switch = true
```

The two conditions must be true in the same snapshot. It is not valid to combine `is_public=true` from one version with an OAuth2 switch from another version.

### 4.2 MCP Servers

MCP Server OAuth2 switches are stored directly on `MCPServer` and are not versioned. MCP visibility is evaluated from the current MCP Server, gateway, and stage rows.

## 5. API Contract

### 5.1 MCP Server scopes

```http
GET /api/v2/inner/oauth2/client-scopes/mcp-servers/
```

Query parameters:

| Field | Required | Validation | Meaning |
| --- | --- | --- | --- |
| `oauth_client_type` | yes | `personal` or `public` | Selects the fixed OAuth2 switch. |
| `gateway_name` | no | maximum 64 characters | Gateway name contains match. |
| `mcp_server_name` | no | maximum 64 characters | MCP Server name contains match. |
| `limit` | no | 1-20, default 10 | Number of gateways in the page. |
| `offset` | no | non-negative, default 0 | Gateway offset. |

The two name filters have AND semantics. Omitting a name filter disables only that filter.

Response:

```json
{
  "data": {
    "count": 52,
    "results": [
      {
        "id": 1,
        "name": "gateway-name",
        "is_official": true,
        "mcp_server_count": 2,
        "mcp_servers": [
          {
            "id": 201,
            "name": "mcp-name",
            "title": "MCP title"
          }
        ]
      }
    ]
  }
}
```

### 5.2 API resource scopes

```http
GET /api/v2/inner/oauth2/client-scopes/resources/
```

Query parameters:

| Field | Required | Validation | Meaning |
| --- | --- | --- | --- |
| `oauth_client_type` | yes | `personal` or `public` | Selects the fixed OAuth2 switch. |
| `gateway_name` | no | maximum 64 characters | Gateway name contains match. |
| `resource_name` | no | maximum 256 characters | Resource name contains match. |
| `limit` | no | 1-20, default 10 | Number of gateways in the page. |
| `offset` | no | non-negative, default 0 | Gateway offset. |

The two name filters have AND semantics. Omitting a name filter disables only that filter.

When an MCP Server has no title, `title` falls back to its name, matching the existing inner MCP serializers.

Response:

```json
{
  "data": {
    "count": 52,
    "results": [
      {
        "id": 1,
        "name": "gateway-name",
        "is_official": true,
        "resource_count": 3,
        "resources": [
          {
            "id": 101,
            "name": "resource-name",
            "description": "Resource description"
          }
        ]
      }
    ]
  }
}
```

### 5.3 Common response semantics

- `count` is the number of matching gateways, not the number of child objects.
- Child counts are calculated after every name and visibility filter and equal the number of distinct child objects returned for that gateway.
- Gateways are ordered by `(name, id)` ascending.
- Child objects are ordered by `(name, id)` ascending.
- A resource returned from multiple referenced versions is deduplicated by `(gateway_id, resource_id)`.
- When several qualifying snapshots remain after filtering, API display fields come from the qualifying row with the greatest `resource_version_id`.
- API `description` follows the existing inner serializer language behavior: use the translated description for the request language when present, otherwise use the default snapshot description.
- An empty result returns `count=0` and `results=[]`.

## 6. Visibility Rules

### 6.1 Gateways

Both endpoints require:

```text
Gateway.status = active
Gateway.is_public = true
```

In multi-tenant mode, apply the same visibility rule as the existing inner gateway list:

```text
Gateway.tenant_mode = global
OR
(Gateway.tenant_mode = single AND Gateway.tenant_id = request.tenant_id)
```

Missing `request.tenant_id` in multi-tenant mode is a validation error.

### 6.2 API resources

An API resource qualifies when:

```text
its ReleasedResource row is referenced by a current Release
AND ReleasedResource.is_public = true
AND the projected switch selected by oauth_client_type = true
```

`allow_apply_permission` is irrelevant because these APIs expose OAuth2 token scopes, not permission-application candidates.

### 6.3 MCP Servers

An MCP Server qualifies when:

```text
MCPServer.status = active
MCPServer.is_public = true
Stage.status = active
the switch selected by oauth_client_type = true
```

## 7. ReleasedResource Query Projections

Add three non-authoritative boolean projection fields to `ReleasedResource`:

```text
is_public
oauth2_public_client_enabled
oauth2_personal_client_enabled
```

`ReleasedResource.data` remains the source of truth. Projection values are extracted from the same resource snapshot whenever `ReleasedResourceManager.save_released_resource()` creates rows:

- `is_public` comes from the top-level snapshot field.
- OAuth2 switches come from `contexts.resource_auth.config` after decoding its JSON string.

Missing or malformed values project to `false`. This fails closed and prevents an invalid snapshot from becoming visible through bkauth.

The current Python `ReleasedResource.is_public` property is replaced by the database field while preserving its public attribute behavior.

## 8. Query Design

Keep the multi-model read logic in a focused service module rather than adding it to a single-model manager. The inner API views remain responsible for transport validation and response serialization.

### 8.1 API resource query

Build a reusable eligible-resource queryset with these predicates:

```text
EXISTS Release WHERE
    Release.gateway_id = ReleasedResource.gateway_id
    AND Release.resource_version_id = ReleasedResource.resource_version_id

Gateway.status = active
Gateway.is_public = true
tenant visibility matches the request
ReleasedResource.is_public = true
selected projected OAuth2 field = true
gateway_name contains filter, if supplied
resource_name contains filter, if supplied
```

Do not join or filter Stage for this query. Current `Release` references define the required union, matching the existing external permission-list concept.

Execute three main SQL queries:

1. Count the grouped eligible gateway rows.
2. Fetch the requested gateway page and annotate `COUNT(DISTINCT resource_id)`.
3. Fetch qualifying snapshots only for gateway IDs in the page.

Group the third result in memory by `(gateway_id, resource_id)`, keeping the greatest qualifying `resource_version_id`. With a maximum page of 20 gateways and roughly 100 enabled resources per gateway, the bounded result remains practical even when a few current versions contain the same resource.

### 8.2 MCP Server query

Apply the gateway, tenant, MCP Server, stage, client-type, and contains filters directly to `MCPServer`. Use the same three-query structure:

1. Count matching gateway groups.
2. Fetch the gateway page with `COUNT(DISTINCT mcp_server.id)`.
3. Fetch matching MCP Servers for the current page gateway IDs.

The target MCP table size is approximately 3,000 rows, so no additional MCP-specific index is required initially.

### 8.3 Client type mapping

Map the validated enum with a fixed in-code mapping:

```text
public   -> oauth2_public_client_enabled
personal -> oauth2_personal_client_enabled
```

Do not accept arbitrary model field names and do not make these fixed identities configurable through settings or environment variables.

## 9. Indexes

Add two composite indexes to `ReleasedResource`:

```text
(oauth2_public_client_enabled, is_public, gateway_id, resource_version_id, resource_id)
(oauth2_personal_client_enabled, is_public, gateway_id, resource_version_id, resource_id)
```

These indexes narrow low-frequency enabled rows and cover grouping fields when no resource-name filter is present. Existing indexing on `Release.resource_version_id` supports the correlated existence check.

The contains filters use `%value%`; ordinary B-tree name indexes do not accelerate them. At the target scale, first narrow by release reference, visibility, and projected booleans, then apply the name filter. Full-text or external search is deferred until production-like evidence shows that resource-name contains matching is the bottleneck.

## 10. Migration and Repair

1. Add the three projection columns with a fail-closed default of `false`.
2. Backfill existing `ReleasedResource` rows in bounded batches by parsing `data`.
3. Update `save_released_resource()` to populate all projections for new rows.
4. Keep `sync_released_resource --force` as the repair path for currently released versions.

Queries continue to use the `Release` existence boundary after backfill. Orphan cleanup is an optimization and storage concern, not a correctness dependency.

## 11. Authentication and Errors

- Both endpoints use `OpenAPIV2Permission`.
- Their gateway resource definitions remain hidden and disallow permission application, following other `/api/v2/inner/` APIs.
- An unsupported `oauth_client_type`, negative offset, zero or excessive limit, or overlong name returns HTTP 400 through serializer validation.
- These endpoints are read-only and have no partial-success or compensation behavior.

## 12. Testing

### 12.1 Projection and migration tests

- Project every public/personal switch combination.
- Preserve `is_public` behavior after replacing the property with a field.
- Treat missing and malformed snapshot values as `false`.
- Verify batched migration backfill for representative old rows.
- Verify forced ReleasedResource reconstruction writes the same projections.

### 12.2 API resource query tests

- Include only versions referenced by `Release`.
- Exclude orphan `ReleasedResource` rows.
- Include a resource when any referenced snapshot simultaneously has `is_public=true` and the requested switch enabled.
- Exclude the cross-version false positive where one version is public and another version only has the switch enabled.
- Deduplicate resource IDs and select the greatest qualifying resource version for display.
- Cover gateway status, gateway visibility, tenant visibility, and both contains filters.
- Verify gateway count, child count, stable ordering, offset, and limit.
- Assert a fixed query count at the query-service boundary to prevent N+1 regressions.

### 12.3 MCP Server query tests

- Cover both client types.
- Cover gateway, stage, MCP status, and public filters.
- Cover tenant visibility and both contains filters.
- Verify gateway count, child count, stable ordering, offset, and limit.
- Assert a fixed query count at the query-service boundary.

### 12.4 API contract verification

- Add focused inner API view and serializer tests.
- Keep the v2 inner gateway YAML and Markdown API documentation synchronized.
- Run the focused pytest targets, inner API consistency checks, Dashboard lint gate, and full Dashboard test gate required by the component instructions.

## 13. Performance Validation

Use production-like data rather than a 100,000-row unit test fixture:

- 10,000 gateways.
- 100,000 API resources.
- 3,000 MCP Servers.
- Up to 1,000 total API resources and approximately 100 enabled resources in a single gateway.
- 20-30 requests per second.

Capture `EXPLAIN ANALYZE` and latency for:

- no name filters;
- `gateway_name` contains filtering;
- `resource_name` contains filtering;
- `mcp_server_name` contains filtering;
- both name filters together;
- first and deep gateway pages.

The first implementation is acceptable when it keeps the three-query structure, has no N+1 behavior, and sustains the target request rate without database saturation. If resource-name contains matching is the measured bottleneck, evaluate a dedicated search index as a separate change.

## 14. Implementation Scope

The implementation is expected to touch only Dashboard concerns required by this contract:

- `ReleasedResource` model, migration, manager projection, and migration tests.
- A focused read-query service.
- v2 inner URLs, views, serializers, and tests.
- v2 inner gateway YAML and Markdown API documentation.

No frontend, bkauth, mcp-proxy, operator, or APISIX changes are part of this repository change.
