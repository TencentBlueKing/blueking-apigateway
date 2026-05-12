### 描述

MCPServer 申请权限/批量申请权限

### 输入参数

#### 请求参数

| 参数名称 | 参数类型 | 必选 | 描述 |
|---|---|---|---|
| target_app_code | string | 是 | 申请权限的应用，应与当前请求应用一致 |
| mcp_server_ids | array[int] | 是 | MCPServer ID 列表 |
| applied_by | string | 是 | 申请人 |
| reason | string | 是 | 申请理由 |

### 请求参数示例

```json
{
  "target_app_code": "test-app",
  "mcp_server_ids": [1, 2],
  "applied_by": "admin",
  "reason": "test"
}
```

### 响应示例

```json
{
  "data": [
    {
      "record_id": 101,
      "bk_app_code": "test-app",
      "mcp_server_id": 1,
      "itsm_ticket_id": "102025092210362600001802",
      "approval_url": "https://itsm.example.com/#/ticket/102025092210362600001802"
    }
  ]
}
```

### 响应参数说明

| 字段 | 类型 | 描述 |
|---|---|---|
| data | array | 结果数据 |

#### data[]

| 参数名称 | 参数类型 | 描述 |
|---|---|---|
| record_id | int | 申请记录 ID |
| bk_app_code | string | 蓝鲸应用 ID |
| mcp_server_id | int | MCPServer ID |
| itsm_ticket_id | string | 关联的 ITSM 工单 ID |
| approval_url | string | 权限审批 URL；当存在 ITSM 工单时返回 ITSM 单据中心链接，否则返回 MCPServer 权限审批页 URL |
