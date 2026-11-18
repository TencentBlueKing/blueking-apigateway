# V2 API Contracts

## Collections and lookup

- Collections retain discovery, filtering, visibility and pagination semantics.
  Exact batch retrieval by identifiers uses a separate non-paginated `-/lookup/`
  route returning `data: [...]`.
- Lists use `limit`/`offset` with `data: {"count": <int>, "results": [...]}`.
  Use configured `StandardLimitOffsetPagination` through
  `paginate_queryset()` / `get_paginated_response()` for new or changed v2
  endpoints, rather than `utils.paginator.LimitOffsetPaginator`.
- If a downstream source already paginates and provides a total, retain this
  envelope without paginating the returned page again.

`urls.py` registers Open, Inner and Sync separately. Keep their existing
authentication/permission entrypoints: public application access, internal
callers and related-app gateway automation have different contracts. Do not
infer authorization from sharing a gateway-shaped URL.

## Inner OAuth2 contracts (bkauth and developer center)

Design: [resource-oauth2-app-access-design.md](../../../../../../docs/resource-oauth2-app-access-design.md)
sections 5.5 and 5.6.

- Resource scope `oauth_client_type` accepts `public`, `personal`,
  `app_delegated` and `app_only`. The `app_*` types filter on the
  `ReleasedResource` projection column and on the current
  `Gateway.oauth2_app_enabled`. The MCP scope accepts only `public`, `personal`
  and `app_delegated`, and `app_delegated` returns every visible MCP Server
  without checking any switch. Keep the resource and MCP client-type sets
  separate (`service/oauth2_client_scope.py`).
- Released-resource lookup/list output `oauth2_app_*_enabled` as projection
  column AND current gateway switch, the same semantics as scope.
- The projection already excludes resources bound with
  `bk-access-token-source(source=bearer)` (see `core/AGENTS.md`).
- Scope is the union over every stage's current release: if one resource is
  delegated in one stage and app-only in another, it appears under both types,
  and lookup shows the mode of the version it reads. The target stage's route
  decides what a call gets. Scope and lookup may also list resources whose
  routes have not yet been republished. They are not proof that a call works.
- `inner` permission-resources list (`_is_listed_permission_resource`):
  resources with `resource_perm_required` need `allow_apply_permission` and
  `app_verified_required`. Every other public resource, including ones that
  need no authentication, is listed with `permission_level=unlimited`, even if
  `allow_apply_permission=false`. The developer center uses this list for search,
  so do not narrow it back to "appliable only". The v1 open list deliberately
  keeps filtering on `allow_apply_permission`.

Tests mirror `tests/apis/v2/<surface>/`; exercise query bounds and envelopes,
lookup scope/visibility, and the owning surface's permissions when affected.
