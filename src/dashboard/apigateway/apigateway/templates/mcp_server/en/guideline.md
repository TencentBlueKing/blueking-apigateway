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

```shell
X-Bkapi-Authorization: {"bk_app_code": "x", "bk_app_secret": "y", "access_token": "z"}
```
> We recommend using `access_token` for its longer validity period. For acquisition methods, see [access_token documentation]({{bk_access_token_doc_url}})

## Others
### MCP Proxy Timeout Configuration
In addition to client-side timeout configurations for MCP, we also support configuring timeout settings for the MCP proxy by adding a request header:

```shell
X-Bkapi-Timeout: 300 # Unit: seconds
```

### Request Header Pass-Through
If you need to pass through certain headers from the MCP client to the backend service called by the gateway, you can configure a request header. Different headers can be separated by commas.

```shell
X-Bkapi-Allowed-Headers: "X-Bk-Tenant-Id,X-xxx-Header"
```