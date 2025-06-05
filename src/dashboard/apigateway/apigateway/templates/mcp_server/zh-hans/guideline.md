## 配置

支持 MCP 协议的客户端通过以下配置使用

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

## 认证
目前 MCP proxy  接入了蓝鲸API网关，目前需要进行`用户认证`和`应用认证`双重认证, 在配置 MCP Server的过程中，还需要额外配置认证请求头,值为 JSON 格式字符串.

```shell
X-Bkapi-Authorization: {"bk_app_code": "x", "bk_app_secret": "y", "{{bk_login_ticket_key}}": "z"}
```
或者：

```shell
X-Bkapi-Authorization: {"bk_app_code": "x", "bk_app_secret": "y", "access_token": "z"}
```
> 推荐使用 `access_token`, 有效期较长, 具体获取方法见：{{bk_access_token_doc_url}}

## 其他
### MCP proxy 超时配置
除了支持 MCP 的客户端超时配置，我们也支持配置 MCP proxy的超时配置，需要配置同样添加一个请求头即可.

```shell
X-Bkapi-Timeout: 300 # 单位 s
```

### 请求头透传
如果需要在 MCP 客户端想透传某些 header 到调用的网关后端服务，也可以配置一个请求头即可,值为 JSON 格式字符串.

```shell
X-Bkapi-Headers-Allowed: ["X-Bk-Tenant-Id"]
```






