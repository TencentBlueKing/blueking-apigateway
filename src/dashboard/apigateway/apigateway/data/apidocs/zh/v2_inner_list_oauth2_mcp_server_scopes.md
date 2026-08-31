### 描述

查询 bkauth 生成个人 Token 或公开客户端 Token 时可选择的 MCP Server 授权范围。结果按网关聚合和分页。

仅返回公开且启用的网关、Stage 和 MCP Server，并根据 `oauth_client_type` 检查对应的 OAuth2 开关。多租户模式下只返回全租户网关和请求租户所属的单租户网关。

### 输入参数

#### query 参数

| 参数名称 | 参数类型 | 必选 | 描述 |
|----------|----------|------|------|
| oauth_client_type | string | 是 | OAuth2 客户端类型：`personal` 或 `public` |
| gateway_name | string | 否 | 网关名称，包含匹配，最长 64 个字符 |
| mcp_server_name | string | 否 | MCP Server 名称，包含匹配，最长 64 个字符 |
| limit | int | 否 | 每页网关数量，范围 1～1000，默认 10 |
| offset | int | 否 | 网关分页偏移量，必须大于或等于 0，默认 0 |

同时传入 `gateway_name` 和 `mcp_server_name` 时，两个过滤条件均须满足。

### 响应示例

```json
{
  "data": {
    "count": 1,
    "results": [
      {
        "id": 1,
        "name": "bk-apigateway",
        "is_official": true,
        "mcp_server_count": 1,
        "mcp_servers": [
          {
            "id": 10,
            "name": "user-tools",
            "title": "用户工具"
          }
        ]
      }
    ]
  }
}
```

### 响应参数说明

| 字段 | 类型 | 描述 |
|------|------|------|
| data.count | int | 过滤后的网关总数，用于网关维度分页 |
| data.results | array | 当前页网关列表，按网关名称、网关 ID 稳定排序 |
| data.results[].id | int | 网关 ID |
| data.results[].name | string | 网关名称 |
| data.results[].is_official | bool | 是否为官方网关 |
| data.results[].mcp_server_count | int | 当前过滤条件下该网关包含的 MCP Server 数量 |
| data.results[].mcp_servers | array | 当前过滤条件下该网关包含的 MCP Server 列表 |
| data.results[].mcp_servers[].id | int | MCP Server ID |
| data.results[].mcp_servers[].name | string | MCP Server 名称 |
| data.results[].mcp_servers[].title | string | MCP Server 标题；标题为空时返回名称 |
