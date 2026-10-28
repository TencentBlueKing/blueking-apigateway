### 描述

批量根据 MCPServer ID 或名称查询 MCPServer 展示名称、描述和分类

供 BKAuth 等第三方系统根据 ResourceID 中的 mcp_name 批量解析 MCPServer 展示信息。

### 输入参数

#### 请求体参数（JSON）

| 参数名称 | 参数类型 | 必选 | 描述                                                                    |
| -------- | -------- | ---- | ----------------------------------------------------------------------- |
| ids      | array    | 否   | MCPServer ID 列表（ids 和 names 至少提供一个）                           |
| names    | array    | 否   | MCPServer 名称列表（ids 和 names 至少提供一个）                           |
| fields   | string   | 否   | 指定返回的字段列表，逗号分隔，如 `fields=id,name,title`；不传默认返回 `id` 和 `name` |

### 请求示例

```json
{
    "names": ["test-mcp-server", "another-mcp-server"],
    "fields": "id,name,title,categories"
}
```

### 响应示例

#### 默认返回（不传 fields）

```json
{
    "data": [
        {
            "id": 1,
            "name": "test-mcp-server"
        }
    ]
}
```

#### 指定字段（fields=id,name,title,description,categories）

```json
{
    "data": [
        {
            "id": 1,
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
| id          | int      | MCPServer ID               |
| name        | string   | MCPServer 名称             |
| title       | string   | MCPServer 中文名/显示名称  |
| description | string   | MCPServer 描述             |
| categories  | array    | MCPServer 分类列表         |

#### data[].categories[]

| 参数名称     | 参数类型 | 描述         |
| ------------ | -------- | ------------ |
| name         | string   | 分类名称     |
| display_name | string   | 分类显示名称 |
