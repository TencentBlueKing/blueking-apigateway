### 描述

mcp_server 申请记录详情


### 输入参数

#### 路径参数

### 请求参数示例

| 参数名称            | 参数类型   | 必选 | 描述                  |
|-----------------|--------|----|---------------------|
| target_app_code | string | 是  | 申请权限的应用，应于当前请求的应用一致 |
| record_id       | int    | 是  | 申请记录 ID             |


```json
{
  "target_app_code": "",
  "record_id": 1
}
```


### 响应示例

```json
{
  "data": {
    "id": 1,
    "mcp_server_name": "bk-apigateway-prod-s1",
    "applied_by": "admin",
    "applied_time": "2025-05-23 10:35:36 +0800",
    "handled_by": [
      "admin"
    ],
    "handled_time": "2025-05-26 16:35:00 +0800",
    "apply_status": "rejected",
    "apply_status_display": "驳回",
    "comment": "test",
    "reason": "test",
    "expire_days": 0,
    "tool_names": [
      "v2_inner_get_app_permission_apply_record"
    ]
  }
}
```

### 响应参数说明

| 字段    | 类型     | 描述                               |
| ------- |--------| ---------------------------------- |
| data    | object | 结果数据，详细信息请见下面说明     |

#### data

| 参数名称                  | 参数类型   | 描述            |
|-----------------------|--------|---------------|
| id                    | int    | 申请 ID         |
| mcp_server_name       | string | mcp_server 名称 |
| applied_by            | string | 申请人           |
| applied_time          | string | 申请时间          |
| handled_by            | array  | 审批人           |
| handled_time          | int    | 审批时间          |
| apply_status          | string | 审批状态          |
| apply_status_display  | string | 审批状态描述        |
| comment               | string | 审批内容          |
| reason                | string | 申请理由          |
| expire_days           | int    | 过期时间          |
| tool_names            | array  | 工具名称列表        |
