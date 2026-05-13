### 描述

mcp_server 已申请权限列表


### 输入参数

#### 请求参数

| 参数名称              | 参数类型    | 必选 | 描述                  |
|-------------------|---------|----|---------------------|
| target_app_code   | string  | 是  | 申请权限的应用，应于当前请求的应用一致 |


### 响应示例

```json
{
  "data": [
    {
      "mcp_server": {
        "id": 1,
        "name": "bk-apigateway-prod-test",
        "title": "测试服务",
        "description": "test",
        "tools_count": 1,
        "tool_names": ["tool1", "tool2"],
        "protocol_type": "sse",
        "url": "https://mcp.example.com/bk-apigateway-prod-test/sse",
        "doc_link": "",
        "categories": [
          {"name": "official", "display_name": "官方"},
          {"name": "ai", "display_name": "AI"}
        ]
      },
      "permission": {
        "status": "owned",
        "action": "",
        "expires_in": null
      }
    }
  ]
}
```

### 响应参数说明

| 字段    | 类型   | 描述                               |
| ------- | ------ | ---------------------------------- |
| data    | array  | 结果数据，详细信息请见下面说明     |

#### data

| 参数名称             | 参数类型   | 描述                           |
|------------------|--------|------------------------------|
| mcp_server       | object | mcp_server 数据，详细信息请见下面说明     |
| permission       | object | mcp_server 权限数据，详细信息请见下面说明   |


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


#### data.permission

| 参数名称           | 参数类型     | 描述                                                                        |
|----------------|----------|---------------------------------------------------------------------------|
| expires_in     | int      | 有效期                                                                       |
| status         | string   | 权限状态（approved：已审批，rejected：已拒绝，pending：申请中，need_apply：待申请，owned：已申请，且未过期） |
| action         | string   | 权限操作                                                                      |
