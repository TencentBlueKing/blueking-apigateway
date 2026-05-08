# Gateway Docs Web APIs

These docs-center endpoints now require a logged-in dashboard user. Requests without a valid login session return `401 UNAUTHENTICATED` before checking whether the gateway is public/displayable.

## Common Rules

- Authentication: required, via dashboard session login.
- Gateway visibility: gateway must be active and public, unless `source=api_debug` is used by an authenticated gateway maintainer.
- Common unauthenticated error:

```json
{
  "error": {
    "code": "UNAUTHENTICATED",
    "message": "user is not authenticated",
    "data": {
      "login_url": "/",
      "login_plain_url": "/plain/",
      "width": 700,
      "height": 550
    }
  }
}
```

## Get Gateway Detail

- Method: `GET`
- Path: `/backend/docs/gateways/{gateway_name}/`
- Query parameters: none
- Request body: none
- Response `data` fields: `id`, `name`, `description`, `tenant_mode`, `tenant_id`, `maintainers`, `doc_maintainers`, `is_official`, `is_plugin_gateway`, `is_deprecated`, `deprecated_note`, `api_url`, `sdks`
- Status codes: `200`, `401`, `404`

## List Gateway Stages

- Method: `GET`
- Path: `/backend/docs/gateways/{gateway_name}/stages/`
- Query parameters: none
- Request body: none
- Response `data[]` fields: `id`, `name`, `description`
- Status codes: `200`, `401`, `404`

## List Gateway Resources

- Method: `GET`
- Path: `/backend/docs/gateways/{gateway_name}/resources/`
- Query parameters: `stage_name` string, required
- Request body: none
- Response `data[]` fields: `id`, `name`, `description`, `method`, `path`, `verified_user_required`, `verified_app_required`, `resource_perm_required`, `allow_apply_permission`, `labels`
- Status codes: `200`, `400`, `401`, `404`

## Get Resource Doc

- Method: `GET`
- Path: `/backend/docs/gateways/{gateway_name}/resources/{resource_name}/doc/`
- Query parameters: `stage_name` string, required
- Request body: none
- Response `data` fields: `type`, `content`, `updated_time`
- Status codes: `200`, `400`, `401`, `404`

## List Gateway SDKs

- Method: `GET`
- Path: `/backend/docs/gateways/{gateway_name}/sdks/`
- Query parameters: `language` string, required
- Request body: none
- Response `data[]` fields: `stage`, `resource_version`, `sdk`
- Status codes: `200`, `400`, `401`, `404`

## Get SDK Usage Example

- Method: `GET`
- Path: `/backend/docs/gateways/{gateway_name}/sdks/usage-example/`
- Query parameters: `language` string, required; `stage_name` string, required; `resource_name` string, required; `resource_id` integer, optional
- Request body: none
- Response `data` fields: `content`
- Status codes: `200`, `400`, `401`, `404`
