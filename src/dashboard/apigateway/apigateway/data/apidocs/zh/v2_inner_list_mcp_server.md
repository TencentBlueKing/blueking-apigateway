### 描述

获取全量的 MCPServer 列表（应用态接口）


### 输入参数

#### 请求参数

| 参数名称    | 参数类型   | 必选 | 描述                                      |
|---------|--------|----|-----------------------------------------|
| keyword | string | 否  | MCPServer 筛选条件，支持模糊匹配 MCPServer 名称或描述 |
| order_by | string | 否  | 排序字段，支持 id, name, updated_time, created_time，前缀 - 表示降序，默认 -updated_time |


### 响应示例

```json
{
  "data": {
    "count": 2,
    "has_next": false,
    "has_previous": false,
    "results": [
      {
        "id": 1,
        "name": "test-mcp-server",
        "title": "测试 MCP Server",
        "description": "这是一个测试的 MCP Server",
        "is_public": true,
        "labels": ["label1", "label2"],
        "resource_names": ["resource1", "resource2"],
        "status": "active",
        "protocol_type": "sse",
        "stage": {
          "id": 1,
          "name": "prod"
        },
        "gateway": {
          "id": 1,
          "name": "bk-apigateway",
          "maintainers": ["admin"],
          "is_official": true
        },
        "tools_count": 5,
        "prompts_count": 2,
        "url": "https://mcp.example.com/test-mcp-server/sse",
        "detail_url": "https://apigateway.example.com/mcp-server/1",
        "updated_by": "admin",
        "created_by": "admin",
        "updated_time": "2025-01-01T12:00:00Z",
        "created_time": "2025-01-01T10:00:00Z"
      }
    ]
  }
}
```

### 响应参数说明

| 字段 | 类型   | 描述                           |
|----|------|------------------------------|
| data | object | 结果数据，详细信息请见下面说明 |

#### data

| 参数名称       | 参数类型  | 描述         |
|------------|-------|------------|
| count      | int   | 总数         |
| has_next   | bool  | 是否有下一页     |
| has_previous | bool  | 是否有上一页     |
| results    | array | MCPServer 列表 |

#### data.results

| 参数名称         | 参数类型   | 描述                    |
|--------------|--------|-----------------------|
| id           | int    | MCPServer ID          |
| name         | string | MCPServer 名称          |
| title        | string | MCPServer 中文名/显示名称    |
| description  | string | MCPServer 描述          |
| is_public    | bool   | MCPServer 是否公开        |
| labels       | array  | MCPServer 标签列表        |
| resource_names | array  | MCPServer 资源名称列表      |
| status       | string | MCPServer 状态          |
| protocol_type | string | MCPServer 协议类型        |
| stage        | object | MCPServer 环境信息        |
| gateway      | object | MCPServer 网关信息        |
| tools_count  | int    | MCPServer 工具数量        |
| prompts_count | int    | MCPServer Prompts 数量  |
| url          | string | MCPServer 访问 URL      |
| detail_url   | string | MCPServer 网关站点详情 URL  |
| updated_by   | string | 更新人                   |
| created_by   | string | 创建人                   |
| updated_time | string | 更新时间                  |
| created_time | string | 创建时间                  |

#### data.results.stage

| 参数名称 | 参数类型   | 描述    |
|------|--------|-------|
| id   | int    | 环境 ID |
| name | string | 环境名称  |

#### data.results.gateway

| 参数名称        | 参数类型   | 描述       |
|-------------|--------|----------|
| id          | int    | 网关 ID    |
| name        | string | 网关名称     |
| maintainers | array  | 网关维护者列表  |
| is_official | bool   | 是否为官方网关  |
