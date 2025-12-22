## 配置

支持 MCP 协议的客户端通过以下配置使用

{% if protocol_type == "streamable_http" %}
```json
{
    "mcpServers": {
      "{{name}}": {
        "type": "streamable-http",
        "url": "{{url}}",
        "description": "{{description}}"
      }
    }
}
```
{% else %}
```json
{
    "mcpServers": {
      "{{name}}": {
        "type": "sse",
        "url": "{{url}}",
        "description": "{{description}}"
      }
    }
}
```
{% endif %}

## 认证

目前 MCP proxy 接入了蓝鲸 API 网关，目前需要进行 `用户认证` 和 `应用认证` 双重认证，在配置 MCP Server 的过程中，还需要额外配置认证请求头，值为 JSON 格式字符串。

```shell
X-Bkapi-Authorization: {"bk_app_code": "x", "bk_app_secret": "y", "{{bk_login_ticket_key}}": "z"}
```

或者：

> 推荐使用 `access_token`, 有效期较长，具体获取方法见 [access_token 说明]({{bk_access_token_doc_url}})

```shell
X-Bkapi-Authorization: {"bk_app_code": "x", "bk_app_secret": "y", "access_token": "z"}
```

## 其他

### MCP proxy 超时配置

当前的调用链路是：`支持mcp agent客户端` --> `bk-apigateway网关`  --> `mcp-proxy` --> `业务网关`
我们支持配置 MCP proxy 的超时配置，需要添加一个请求头即可。

```shell
X-Bkapi-Timeout: 300 # 单位 s
```

### 请求头透传

如果需要在 MCP 客户端想透传某些 header 到调用的网关后端服务，也可以配置一个请求头即可，不同 header 直接用 `,` 分割

```shell
X-Bkapi-Allowed-Headers: "X-Bk-Tenant-Id,X-xxx-Header"
```

{% if enable_multi_tenant_mode and user_tenant_id == "system" %}
### 多租户模式需要配置 X-Bk-Tenant-Id 请求头

在多租户模式下，调用 MCP Server 时，需要透传 `X-Bk-Tenant-Id` 请求头。

```shell
X-Bk-Tenant-Id: ""
```

值为：
- 如果调用的应用是单租户应用，值为应用租户 ID(或者可以不传递，网关会根据调用应用 ID 自动获取)
- 如果调用的应用是全租户应用，值为具体某个租户的租户 ID (必须显式传递，否则会被网关拦截)
{% endif %}

## FAQ

### 1. 使用客户端添加 `MCP Server`过程中出现 `4xx`的错误码，如何排查？

- 需要确认 `MCP Server` url 是否正确。
- `MCP Server` 开启了 `应用认证+用户认证`，需要确认 `X-Bkapi-Authorization` 请求头格式 (例如：cherry-studio 配置请求头使用 `=`)
及对应的认证票据是否正确。
- 确认对应的 `bk_app_code` 是否拥有该 `MCP Server` 的权限。






