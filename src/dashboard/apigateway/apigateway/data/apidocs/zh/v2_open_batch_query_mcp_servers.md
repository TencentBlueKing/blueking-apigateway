### 描述

批量根据 MCPServer 名称查询 MCPServer 展示名称、描述和分类

供 BKAuth 等第三方系统根据 ResourceID 中的 mcp_name 批量解析 MCPServer 展示信息。

### 输入参数

#### 请求体参数（JSON）

| 参数名称 | 参数类型 | 必选 | 描述                |
| -------- | -------- | ---- | ------------------- |
| names    | array    | 是   | MCPServer 名称列表  |

### 请求示例

```json
{
    "names": ["test-mcp-server", "another-mcp-server"]
}
```

### 响应示例

```json
{
    "data": [
        {
            "name": "test-mcp-server",
            "title": "测试 MCP Server",
            "description": "这是一个测试的 MCP Server",
            "categories": [
                {
                    "name": "official",
                    "display_name": "官方"
                }
            ]
        }
    ]
}
```

### 响应参数说明

| 字段 | 类型  | 描述                           |
| ---- | ----- | ------------------------------ |
| data | array | 结果数据，详细信息请见下面说明 |

#### data[]

| 参数名称    | 参数类型 | 描述                       |
| ----------- | -------- | -------------------------- |
| name        | string   | MCPServer 名称             |
| title       | string   | MCPServer 中文名/显示名称  |
| description | string   | MCPServer 描述             |
| categories  | array    | MCPServer 分类列表         |

#### data[].categories[]

| 参数名称     | 参数类型 | 描述         |
| ------------ | -------- | ------------ |
| name         | string   | 分类名称     |
| display_name | string   | 分类显示名称 |
