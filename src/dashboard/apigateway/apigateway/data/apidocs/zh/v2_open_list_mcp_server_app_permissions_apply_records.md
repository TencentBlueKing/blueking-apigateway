### 描述

获取指定应用的 mcp_server 权限申请记录列表

### 输入参数

#### 请求参数

| 参数名称          | 参数类型   | 必选 | 描述                    |
|---------------|--------|----|-----------------------|
| bk_app_code   | string | 是  | 蓝鲸应用编码                |
| mcp_server_id | int    | 否  | mcp_server ID         |
| record_id     | int    | 否  | 申请记录 ID               |
| limit         | int    | 否  | 最大返回条目数量，默认为 10       |
| offset        | int    | 否  | 相对于完整未分页数据的起始位置，默认为 0 |


### 响应示例

```json
{
  "data": [
    {
      "mcp_server": {
        "id": 1,
        "name": "test",
        "title": "测试服务",
        "description": null
      },
      "id": 1,
      "bk_app_code": "bk-001",
      "applied_by": "admin",
      "applied_time": "2025-06-09 11:13:26 +0800",
      "handled_by": "admin",
      "handled_time": "2025-07-02 14:29:04 +0800",
      "status": "approved",
      "status_display": "通过",
      "comment": "",
      "reason": "",
      "expire_days": 0
    }
  ]
}
```

### 响应参数说明

| 字段    | 类型   | 描述                               |
| ------- | ------ | ---------------------------------- |
| data    | object | 结果数据，详细信息请见下面说明     |


#### data

| 参数名称           | 参数类型   | 描述            |
|----------------|--------|---------------|
| id             | int    | 申请记录 ID       |
| bk_app_code    | string | 蓝鲸应用编码        |
| applied_by     | string | 申请人           |
| applied_time   | string | 申请时间          |
| handled_by     | string | 审批人           |
| handled_time   | string | 审批时间          |
| status         | string | 审批状态          |
| status_display | string | 审批状态描述        |
| comment        | string | 审批内容          |
| reason         | string | 申请理由          |
| expire_days    | int    | 过期时间          |
| mcp_server     | object | mcp_server 信息 |


#### data.mcp_server

| 参数名称          | 参数类型    | 描述                   |
|---------------|---------|----------------------|
| id            | int     | mcp_server ID        |
| name          | string  | mcp_server 名称        |
| title         | string  | mcp_server 中文名/显示名称  |
| description   | string  | mcp_server 描述        |
