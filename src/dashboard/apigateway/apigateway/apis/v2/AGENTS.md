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

Tests mirror `tests/apis/v2/<surface>/`; exercise query bounds and envelopes,
lookup scope/visibility, and the owning surface's permissions when affected.
