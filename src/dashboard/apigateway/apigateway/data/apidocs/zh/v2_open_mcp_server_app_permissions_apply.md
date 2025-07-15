### 描述

指定应用发起 mcp_server 权限申请

### 输入参数

#### 请求参数

| 参数名称               | 参数类型       | 必选 | 描述               |
|--------------------|------------|----|------------------|
| bk_app_code        | string     | 是  | 蓝鲸应用编码           |
| mcp_server_ids     | array[int] | 是  | mcp_server ID 列表 |
| applied_by         | string     | 是  | 申请人              |
| reason             | string     | 是  | 申请原因             |

### 请求参数示例

```json
{
  "app_code": "string",
  "mcp_server_ids": [],
  "applied_by": "string",
  "reason": "string"
}
```


### 响应示例

```json
{
  "data": [
    {
      "record_id": 10,
      "bk_app_code": "bk-001",
      "mcp_server_id": 1
    },
    {
      "record_id": 11,
      "bk_app_code": "bk-001",
      "mcp_server_id": 2
    },
    {
      "record_id": 12,
      "bk_app_code": "bk-001",
      "mcp_server_id": 3
    }
  ]
}
```

#### data

| 参数名称          | 参数类型   | 描述                  |
|---------------|--------|---------------------|
| record_id     | int    | 申请记录 ID             |
| bk_app_code   | string | 蓝鲸应用编码              |
| mcp_server_id | string | mcp_server ID       |
