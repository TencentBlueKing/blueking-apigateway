### 描述

mcp_server 已申请权限列表


### 输入参数

#### 路径参数

### 请求参数示例

| 参数名称              | 参数类型    | 必选 | 描述                  |
|-------------------|---------|----|---------------------|
| target_app_code   | string  | 是  | 申请权限的应用，应于当前请求的应用一致 |


```json
{
  "target_app_code": ""
}
```


### 响应示例

```json
{
  "data": [
    {
      "id": 1,
      "name": "bk-esb-prod-test",
      "description": "test",
      "tools_count": 1,
      "doc_link": "",
      "permission_status": "owned",
      "permission_action": "",
      "expires_in": null
    }
  ]
}
```

### 响应参数说明

| 字段    | 类型   | 描述                               |
| ------- | ------ | ---------------------------------- |
| data    | array  | 结果数据，详细信息请见下面说明     |

#### data

| 参数名称               | 参数类型   | 描述                |
|--------------------|--------|-------------------|
| id                 | int    | mcp_server ID     |
| name               | string | mcp_server 名称     |
| description        | string | mcp_server 描述     |
| tools_count        | int    | mcp_server 工具数量   |
| expires_in         | int    | 有效期               |
| permission_status  | string | 权限状态              |
| permission_action  | string | 权限操作              |
| doc_link           | string | MCPServer 文档访问地址  |
