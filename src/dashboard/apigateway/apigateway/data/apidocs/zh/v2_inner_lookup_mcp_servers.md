### 描述

按 ID 或名称批量查询活跃的 MCPServer（应用态接口）。接口不分页，只返回 MCPServer、所属网关和环境均为启用状态的记录；未匹配的 ID 或名称不会出现在结果中。同时传入 ID 和名称时，返回两组条件的交集。


### 输入参数

#### 请求参数

| 参数名称 | 参数类型 | 必选 | 描述 |
|---|---|---|---|
| ids | string | 否 | MCPServer ID 列表，多个以逗号分割，最多 50 个；与 `names` 不能同时为空 |
| names | string | 否 | MCPServer 名称列表，精确匹配，多个以逗号分割，最多 50 个；与 `ids` 不能同时为空 |
| fields | string | 否 | 指定返回的字段列表，多个以逗号分割，例如 `fields=id,name`；支持的字段见 `data`；不传时返回全部字段，包含不支持的字段时返回参数校验错误 |


### 响应示例

以下示例对应 `fields=id,name,title`。

```json
{
  "data": [
    {
      "id": 1,
      "name": "test-mcp-server",
      "title": "测试 MCP Server"
    }
  ]
}
```

### 响应参数说明

| 字段 | 类型 | 描述 |
|---|---|---|
| data | array | 匹配的 MCPServer 列表，无分页包装 |
| data[].id | int | MCPServer ID |
| data[].name | string | MCPServer 名称 |
| data[].title | string | MCPServer 中文名/显示名称 |
| data[].description | string | MCPServer 描述 |
| data[].is_public | bool | MCPServer 是否公开 |
| data[].labels | array | MCPServer 标签列表 |
| data[].resource_names | array | MCPServer 资源名称列表 |
| data[].tool_names | array | MCPServer 工具名称列表 |
| data[].status | string | MCPServer 状态 |
| data[].protocol_type | string | MCPServer 协议类型 |
| data[].oauth2_public_client_enabled | bool | 是否开启 OAuth2 公开客户端模式 |
| data[].oauth2_personal_client_enabled | bool | 是否开启 OAuth2 个人客户端模式 |
| data[].categories | array | MCPServer 分类列表 |
| data[].stage | object | MCPServer 环境信息 |
| data[].gateway | object | MCPServer 网关信息 |
| data[].tools_count | int | MCPServer 工具数量 |
| data[].prompts_count | int | MCPServer Prompts 数量 |
| data[].url | string | MCPServer 访问 URL |
| data[].detail_url | string | MCPServer 网关站点详情 URL |
| data[].updated_by | string | 更新人 |
| data[].created_by | string | 创建人 |
| data[].updated_time | string | 更新时间 |
| data[].created_time | string | 创建时间 |
