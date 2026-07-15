### 描述

mcp_server 申请记录列表

### 输入参数

#### 请求参数

| 参数名称 | 参数类型 | 必选 | 描述 |
|---|---|---|---|
| target_app_code | string | 是 | 申请权限的应用，应与当前请求应用一致 |
| applied_by | string | 否 | 申请人 |
| applied_time_start | int | 否 | 申请开始时间 |
| applied_time_end | int | 否 | 申请截止时间 |
| apply_status | string | 否 | 申请状态，approved：全部通过，rejected：全部驳回，pending：待审批 |
| query | string | 否 | 查询条件 |

### 响应示例

```json
{
  "data": [
    {
      "mcp_server": {
        "id": 1,
        "name": "bk-apigateway-prod-s1",
        "title": "测试服务",
        "description": "test",
        "tools_count": 1,
        "tool_names": ["tool1", "tool2"],
        "protocol_type": "sse",
        "url": "https://mcp.example.com/bk-apigateway-prod-s1/sse",
        "doc_link": "",
        "categories": [
          {"name": "official", "display_name": "官方"},
          {"name": "ai", "display_name": "AI"}
        ],
        "is_official": true
      },
      "record": {
        "id": 1,
        "applied_by": "admin",
        "applied_time": "2025-01-01 00:00:00 +0800",
        "handled_by": ["admin"],
        "handled_time": null,
        "apply_status": "pending",
        "apply_status_display": "待审批",
        "comment": "",
        "reason": "",
        "expire_days": 0,
        "itsm_ticket_id": "102025092210362600001802",
        "approval_url": "https://itsm.example.com/#/ticket/102025092210362600001802"
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
| record | object | mcp_server 申请记录数据，详细信息见 `data.record` |

#### data.mcp_server

| 参数名称            | 参数类型   | 描述                   |
|-----------------|--------|----------------------|
| id              | int    | mcp_server ID        |
| name            | string | mcp_server 名称        |
| title           | string | mcp_server 中文名/显示名称  |
| description     | string | mcp_server 描述        |
| tools_count     | int    | mcp_server 工具数量      |
| tool_names      | array  | mcp_server 工具名称列表    |
| protocol_type   | string | MCPServer 协议类型（sse：SSE 协议，streamable_http：Streamable HTTP 协议） |
| url             | string | mcp_server 访问 URL，根据最低权限级别自适应返回普通 URL 或应用态 URL |
| doc_link        | string | mcp_server 文档访问地址    |
| categories      | array  | mcp_server 分类列表，每项包含 name（英文标识）和 display_name（显示名称） |
| is_official     | bool   | 是否为官方 MCPServer |

#### data.record

| 参数名称 | 参数类型 | 描述 |
|---|---|---|
| id | int | 申请记录 ID |
| applied_by | string | 申请人 |
| applied_time | string | 申请时间 |
| handled_by | array | 审批人 |
| handled_time | int | 审批时间 |
| apply_status | string | 审批状态（approved：通过，rejected：驳回，pending：待审批） |
| apply_status_display | string | 审批状态描述 |
| comment | string | 审批内容 |
| reason | string | 申请理由 |
| expire_days | int | 过期时间 |
| itsm_ticket_id | string | 关联的 ITSM 工单 ID |
| approval_url | string | 权限审批 URL；当存在 ITSM 工单时返回 ITSM 单据中心链接，否则返回 MCPServer 权限审批页 URL |
