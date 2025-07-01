## Configuration

Clients supporting the MCP protocol can be configured using the following settings:

```json
{
    "mcpServers": {
      "{{name}}": {
        "type": "sse",
        "url": "{{sse_url}}",
        "description": "{{description}}"
      }
    }
}
```

## Authentication

The MCP proxy currently integrates with BlueKing API Gateway, requiring both `user authentication` and `app authentication`. When configuring MCP Server, additional authentication headers must be configured as JSON-formatted strings.

```shell
X-Bkapi-Authorization: {"bk_app_code": "x", "bk_app_secret": "y", "{{bk_login_ticket_key}}": "z"}
```

or:

> We recommend using `access_token` for its longer validity period. For acquisition methods, see [access_token documentation]({{bk_access_token_doc_url}})

```shell
X-Bkapi-Authorization: {"bk_app_code": "x", "bk_app_secret": "y", "access_token": "z"}
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

## FAQ

### 1. How to troubleshoot 4xx error codes when adding MCP Server via client?

- Verify the MCP Server URL is correct.
- If MCP Server has enabled "application authentication + user authentication", confirm the format of the X-Bkapi-Authorization header (e.g., cherry-studio uses "=" for header configuration) and check whether the authentication credentials are valid.
- Ensure the corresponding bk_app_code has permission to access this MCP Server.sions for this `MCP Server`.