### 描述

获取 mcp_server 详情

### 输入参数

#### 路径参数

| 参数名称        | 参数类型 | 必选 | 描述           |
| -------------- | ------- | ---- | -------------- |
| mcp_server_id  | int     | 是   | mcp_server ID  |


### 响应示例

```json
{
  "data": {
    "id": 2,
    "name": "test",
    "title": "测试服务",
    "description": "这是一个测试 MCP Server",
    "is_public": true,
    "labels": ["AI", "工具"],
    "status": 1,
    "protocol_type": "sse",
    "oauth2_enabled": false,
    "url": "https://test.com/api/bk-apigateway/prod/api/v2/mcp-servers/test/sse",
    "guideline": "## 使用指南\n...",
    "tools": [
      {
        "id": 1,
        "name": "tool1",
        "description": "工具1描述",
        "method": "POST",
        "path": "/api/v1/tool1/",
        "verified_user_required": false,
        "verified_app_required": true,
        "resource_perm_required": true,
        "allow_apply_permission": true,
        "labels": ["标签1"]
      }
    ],
    "prompts": [
      {
        "id": 1,
        "name": "prompt1",
        "code": "prompt_code_1",
        "content": "这是 prompt 内容",
        "updated_time": "2025-09-01 00:00:00",
        "updated_by": "admin",
        "labels": ["AI"],
        "is_public": true,
        "space_code": "default",
        "space_name": "默认空间"
      }
    ],
    "prompts_count": 1,
    "maintainers": ["admin"],
    "user_custom_doc": "",
    "updated_time": "2025-09-01 00:00:00 +0800",
    "created_time": "2025-09-01 00:00:00 +0800"
  }
}
```

### 响应参数说明

| 字段    | 类型   | 描述                           |
| ------- | ------ | ------------------------------ |
| data    | object | 结果数据，详细信息请见下面说明 |


#### data

| 参数名称         | 参数类型 | 描述                                                         |
| ---------------- | -------- | ------------------------------------------------------------ |
| id               | int      | mcp_server ID                                                |
| name             | string   | mcp_server 名称                                              |
| title            | string   | mcp_server 中文名/显示名称                                   |
| description      | string   | mcp_server 描述                                              |
| is_public        | boolean  | mcp_server 是否公开                                          |
| labels           | array    | mcp_server 标签                                              |
| status           | int      | mcp_server 状态（0：已停用，1：启用中）                      |
| protocol_type    | string   | MCP 协议类型（sse：SSE 协议，streamable_http：Streamable HTTP 协议） |
| oauth2_enabled   | boolean  | 是否开启 OAuth2 认证                                         |
| url              | string   | mcp_server 访问地址                                          |
| guideline        | string   | mcp_server 使用指南                                          |
| tools            | array    | mcp_server 工具列表                                          |
| prompts          | array    | mcp_server Prompts 列表                                      |
| prompts_count    | int      | mcp_server Prompts 数量                                      |
| maintainers      | array    | mcp_server 维护者                                            |
| user_custom_doc  | string   | 用户自定义文档                                               |
| updated_time     | string   | 更新时间                                                     |
| created_time     | string   | 创建时间                                                     |


#### data.tools

| 参数名称               | 参数类型 | 描述                   |
| ---------------------- | -------- | ---------------------- |
| id                     | int      | 资源 ID                |
| name                   | string   | 资源名称               |
| description            | string   | 资源描述               |
| method                 | string   | 资源前端请求方法       |
| path                   | string   | 资源前端请求路径       |
| verified_user_required | boolean  | 是否需要认证用户       |
| verified_app_required  | boolean  | 是否需要认证应用       |
| resource_perm_required | boolean  | 是否验证应用访问资源的权限 |
| allow_apply_permission | boolean  | 是否需要申请权限       |
| labels                 | array    | 资源标签列表           |


#### data.prompts

| 参数名称     | 参数类型 | 描述                          |
| ------------ | -------- | ----------------------------- |
| id           | int      | Prompt ID（第三方平台的唯一标识） |
| name         | string   | Prompt 名称                   |
| code         | string   | Prompt 标识码                 |
| content      | string   | Prompt 内容（私有 Prompt 不返回内容） |
| updated_time | string   | Prompt 更新时间               |
| updated_by   | string   | Prompt 更新人                 |
| labels       | array    | Prompt 标签列表               |
| is_public    | boolean  | Prompt 是否公开               |
| space_code   | string   | Prompt 所在空间标识           |
| space_name   | string   | Prompt 所在空间名称           |
