### 描述

按申请记录 ID 批量查询指定应用的 MCPServer 权限申请记录。接口不分页，只返回 `bk_app_code` 对应应用下匹配的记录，未匹配或属于其他应用的记录不会出现在结果中。

### 输入参数

| 参数名称 | 参数类型 | 必选 | 描述 |
|---|---|---|---|
| bk_app_code | string | 是 | 蓝鲸应用编码 |
| ids | string | 是 | 申请记录 ID 列表，多个以逗号分隔，最多 50 个 |

### 响应示例

```json
{
  "data": [
    {
      "id": 1,
      "bk_app_code": "bk-001",
      "status": "pending",
      "mcp_server": {
        "id": 1,
        "name": "demo-mcp-server"
      }
    }
  ]
}
```

### 响应参数说明

| 字段 | 类型 | 描述 |
|---|---|---|
| data | array | 匹配的申请记录列表，无分页包装 |
| data[].id | int | 申请记录 ID |
| data[].bk_app_code | string | 蓝鲸应用编码 |
| data[].status | string | 审批状态 |
| data[].mcp_server | object | MCPServer 信息 |
