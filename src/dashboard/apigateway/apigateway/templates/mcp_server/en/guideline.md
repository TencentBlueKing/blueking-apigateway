## Authentication

{% if oauth2_public_client_enabled %}
### OAuth2 Public Client Mode

This MCP Server has **OAuth2 Public Client Mode** enabled. The `X-Bkapi-Authorization` header is not required in the client configuration — after the user completes OAuth2 authorization in the browser, authentication will be handled automatically.

{% endif %}
{% if oauth2_personal_client_enabled %}
### Personal Token

This MCP Server has **Personal Token** (OAuth2 Personal Client) enabled. Users can call this MCP Server with a personal token without manually configuring app credentials. Add the following header in the MCP client:

```shell
Authorization: Bearer <your_personal_token>
```

> For acquisition methods, see [personal token documentation]({{bk_personal_token_doc_url}})

{% endif %}
### X-Bkapi-Authorization

{% if oauth2_public_client_enabled or oauth2_personal_client_enabled %}
> **Note**: The `X-Bkapi-Authorization` header is always valid. If provided, the system will process the authentication as usual.

{% endif %}
The MCP proxy currently integrates with BlueKing API Gateway, requiring both `user authentication` and `app authentication`. When configuring MCP Server, additional authentication headers must be configured as JSON-formatted strings.

```shell
X-Bkapi-Authorization: {"bk_app_code": "x", "bk_app_secret": "y", "{{bk_login_ticket_key}}": "z"}
```

or:

> We recommend using `access_token` for its longer validity period. For acquisition methods, see [access_token documentation]({{bk_access_token_doc_url}})

```shell
X-Bkapi-Authorization: {"access_token": "z"}
```

## Others

### MCP Proxy Timeout Configuration

The current invocation chain is: `MCP Agent Client` --> `BK-APIGateway` --> `MCP-Proxy` --> `Business Gateway`. We support configuring timeout settings for MCP Proxy by simply adding a request header.

```shell
X-Bkapi-Timeout: 300 # Unit: seconds
```

### Request Header Pass-Through

If you need to pass through certain headers from the MCP client to the backend service called by the gateway, you can configure a request header. Different headers can be separated by commas.

```shell
X-Bkapi-Allowed-Headers: "X-Bk-Tenant-Id,X-xxx-Header"
```

{% if enable_multi_tenant_mode and user_tenant_id == "system" %}
### Multi-tenant mode requires configuring the X-Bk-Tenant-Id request header

In multi-tenant mode, when calling MCP Server, the `X-Bk-Tenant-Id` request header must be passed through.

```shell
X-Bk-Tenant-Id: ""
```

The value is:
- If the application is a single-tenant application, the value is the application tenant ID (or can be omitted, the gateway will automatically obtain the tenant ID based on the application ID)
- If the application is a full-tenant application, the value is the tenant ID of a specific tenant (must be explicitly passed, otherwise it will be intercepted by the gateway)
{% endif %}

## FAQ

### 1. How to troubleshoot 4xx error codes when adding MCP Server via client?

- Verify the MCP Server URL is correct.
- If MCP Server has enabled "application authentication + user authentication", confirm the format of the X-Bkapi-Authorization header (e.g., cherry-studio uses "=" for header configuration) and check whether the authentication credentials are valid.
- Ensure the corresponding bk_app_code has permission to access this MCP Server.sions for this `MCP Server`.