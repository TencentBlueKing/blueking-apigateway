### 描述

mcp_server 申请权限列表

### 输入参数

#### 请求参数

| 参数名称 | 参数类型 | 必选 | 描述 |
|---|---|---|---|
| target_app_code | string | 是 | 申请权限的应用，应与当前请求应用一致 |
| keyword | string | 否 | mcp_server 关键字（同时搜索 name + description） |

### 响应示例

```json
{
  "data": [
    {
      "mcp_server": {
        "id": 1,
        "name": "bk-apigateway-prod-test1",
        "title": "测试服务1",
        "description": "test",
        "tools_count": 1,
        "tool_names": ["tool1", "tool2"],
        "protocol_type": "sse",
        "url": "https://mcp.example.com/bk-apigateway-prod-test1/sse",
        "doc_link": "",
        "categories": [
          {"name": "official", "display_name": "官方"},
          {"name": "ai", "display_name": "AI"}
        ],
        "is_official": true,
        "oauth2_public_client_enabled": false
      },
      "permission": {
        "status": "pending",
        "action": "",
        "expires_in": null,
        "handled_by": ["admin"],
        "approval_url": "https://itsm.example.com/#/ticket/102025092210362600001802"
      }
    },
    {
      "mcp_server": {
        "id": 2,
        "name": "bk-esb-prod-test2",
        "title": "测试服务2",
        "description": "test",
        "tools_count": 1,
        "tool_names": ["tool3"],
        "protocol_type": "sse",
        "url": "https://mcp.example.com/bk-esb-prod-test2/sse",
        "doc_link": "",
        "categories": [],
        "is_official": false,
        "oauth2_public_client_enabled": false
      },
      "permission": {
        "status": "need_apply",
        "action": "apply",
        "expires_in": null,
        "handled_by": ["admin"],
        "approval_url": "http://dashboard.example.com/gateways/1/mcp-servers/2/permissions/"
      }
    }
  ]
}
```

### 响应参数说明

| 字段 | 类型 | 描述 |
|---|---|---|
| data | array | 结果数据，详细信息见下文 |

#### data

| 参数名称 | 参数类型 | 描述 |
|---|---|---|
| mcp_server | object | mcp_server 数据，详细信息见 `data.mcp_server` |
| permission | object | mcp_server 权限数据，详细信息见 `data.permission` |

#### data.mcp_server

| 参数名称            | 参数类型   | 描述                |
|-----------------|--------|-------------------|
| id              | int    | mcp_server ID     |
| name            | string | mcp_server 名称     |
| title           | string | mcp_server 中文名/显示名称 |
| description     | string | mcp_server 描述     |
| tools_count     | int    | mcp_server 工具数量   |
| tool_names      | array  | mcp_server 工具名称列表 |
| protocol_type   | string | MCPServer 协议类型（sse：SSE 协议，streamable_http：Streamable HTTP 协议） |
| url             | string | mcp_server 访问 URL，根据最低权限级别自适应返回普通 URL 或应用态 URL |
| doc_link        | string | mcp_server 文档访问地址 |
| categories      | array  | mcp_server 分类列表，每项包含 name（英文标识）和 display_name（显示名称） |
| is_official     | bool   | 是否为官方 MCPServer |
| oauth2_public_client_enabled | bool | 是否开启 OAuth2 公开客户端模式，开启后将会对 bk_app_code=public 的应用进行授权 |

#### data.permission

| 参数名称 | 参数类型 | 描述 |
|---|---|---|
| expires_in | int | 有效期 |
| status | string | 权限状态 |
| action | string | 权限操作 |
| handled_by | array[string] | 处理人 |
| approval_url | string | 权限审批 URL；当存在 `itsm_ticket_id` 时返回 ITSM 单据中心链接，否则返回 MCPServer 权限审批页 URL |
