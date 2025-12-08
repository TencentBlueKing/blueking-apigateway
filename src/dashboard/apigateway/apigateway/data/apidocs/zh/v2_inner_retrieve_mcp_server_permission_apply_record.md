### 描述

mcp_server 申请记录详情


### 输入参数

#### 路径参数

| 参数名称            | 参数类型   | 必选 | 描述                  |
|-----------------|--------|----|---------------------|
| record_id       | int    | 是  | 申请记录 ID             |

#### 请求参数

| 参数名称            | 参数类型   | 必选 | 描述                  |
|-----------------|--------|----|---------------------|
| target_app_code | string | 是  | 申请权限的应用，应于当前请求的应用一致 |

### 响应示例

```json
{
  "data": {
    "mcp_server": {
      "id": 1,
      "name": "bk-apigateway-prod-s1",
      "title": "测试服务",
      "description": "test",
      "tools_count": "1",
      "doc_link": ""
    },
    "record": {
      "applied_by": "admin",
      "applied_time": "2025-01-01 00:00:00 +0800",
      "handled_by": ["admin"],
      "handled_time": "2025-01-01 00:00:00 +0800",
      "apply_status": "rejected",
      "apply_status_display": "驳回",
      "comment": "test",
      "reason": "test",
      "expire_days": 0
    },
    "tool_names": [
      "v2_inner_get_app_permission_apply_record"
    ]
  }
}
```

### 响应参数说明

| 字段    | 类型   | 描述                |
| -------| ------ |-------------------|
| data   | array  | 结果数据，详细信息请见下面说明   |

#### data

| 参数名称         | 参数类型    | 描述                           |
|--------------|---------|------------------------------|
| mcp_server   | object  | mcp_server 数据，详细信息请见下面说明     |
| record       | object  | mcp_server 申请记录数据，详细信息请见下面说明 |
| tool_names   | array   | mcp_server 工具名称列表            |


#### data.mcp_server

| 参数名称            | 参数类型   | 描述                   |
|-----------------|--------|----------------------|
| id              | int    | mcp_server ID        |
| name            | string | mcp_server 名称        |
| title           | string | mcp_server 中文名/显示名称  |
| description     | string | mcp_server 描述        |
| tools_count     | int    | mcp_server 工具数量      |
| doc_link        | string | mcp_server 文档访问地址    |


#### data.record

| 参数名称                 | 参数类型   | 描述      |
|----------------------|--------|---------|
| id                   | int    | 申请记录 ID |
| applied_by           | string | 申请人     |
| applied_time         | string | 申请时间    |
| handled_by           | array  | 审批人     |
| handled_time         | int    | 审批时间    |
| apply_status         | string | 审批状态    |
| apply_status_display | string | 审批状态描述  |
| comment              | string | 审批内容    |
| reason               | string | 申请理由    |
| expire_days          | int    | 过期时间    |
