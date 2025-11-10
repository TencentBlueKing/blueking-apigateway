### 描述

获取网关资源的详细信息，包含资源基本信息、文档内容和 OpenAPI Schema 定义。

- 只返回公开的资源
- 返回指定环境下已发布的资源信息
- 包含完整的资源文档（Markdown 格式）
- 包含 OpenAPI Schema 参数定义

### 输入参数

### 路径参数

| 参数名称          | 参数类型   | 参数位置 | 必须 | 描述    |
|---------------|--------|------|-----|-------|
| gateway_name  | string | path | 是   | 网关名称  |
| resource_name | string | path | 是   | 资源名称  |

### 查询参数

| 参数名称       | 参数类型   | 参数位置  | 必须 | 描述                    |
|------------|--------|-------|-----|-----------------------|
| stage_name | string | query | 是   | 环境名称（如 prod、test 等） |

### 响应示例

```json
{
    "code": 0,
    "message": "OK",
    "data": {
        "id": 1,
        "name": "get_user_info",
        "description": "获取用户信息",
        "description_en": "Get user information",
        "method": "GET",
        "path": "/api/v1/users/{user_id}/",
        "match_subpath": false,
        "enable_websocket": false,
        "is_public": true,
        "allow_apply_permission": true,
        "schema": {
            "parameters": [
                {
                    "name": "user_id",
                    "in": "path",
                    "required": true,
                    "description": "用户 ID",
                    "schema": {
                        "type": "string"
                    }
                }
            ],
            "responses": {
                "200": {
                    "description": "成功",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "user_id": {
                                        "type": "string"
                                    },
                                    "username": {
                                        "type": "string"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "doc": {
            "type": "markdown",
            "content": "# 获取用户信息\n\n这个接口用于获取指定用户的详细信息...",
            "updated_time": "2025-01-10T15:30:00Z"
        },
        "auth_config": {
            "auth_verified_required": true,
            "app_verified_required": true,
            "resource_perm_required": true
        }
    }
}
```

### 响应参数说明

| 字段      | 类型     | 描述                       |
|---------|--------|--------------------------|
| code    | int    | 返回码，0 表示成功，其它值表示失败      |
| message | string | 错误信息                     |
| data    | object | 结果数据，详细信息请见下面说明        |

#### data

| 参数名称                   | 参数类型    | 描述                        |
|------------------------|---------|---------------------------|
| id                     | int     | 资源 ID                     |
| name                   | string  | 资源名称                      |
| description            | string  | 资源描述（中文）                  |
| description_en         | string  | 资源描述（英文）                  |
| method                 | string  | 请求方法（GET、POST 等）          |
| path                   | string  | 资源路径                      |
| match_subpath          | boolean | 是否匹配子路径                   |
| enable_websocket       | boolean | 是否启用 WebSocket            |
| is_public              | boolean | 是否公开                      |
| allow_apply_permission | boolean | 是否允许申请权限                  |
| schema                 | object  | OpenAPI Schema 定义，详见下面说明  |
| doc                    | object  | 资源文档信息，详见 doc 说明（可能为 null） |
| auth_config            | object  | 认证配置，详见 auth_config 说明   |

#### schema

OpenAPI 3.0 格式的 Schema 定义，包含以下常见字段：

| 参数名称       | 参数类型   | 描述              |
|------------|--------|-----------------|
| parameters | array  | 请求参数列表          |
| requestBody | object | 请求体定义           |
| responses  | object | 响应定义（按状态码分组）    |

**参数示例：**
- `parameters`: 包含 path、query、header 等参数的定义
- `responses`: 包含各状态码的响应结构定义

详细格式请参考 [OpenAPI 3.0 规范](https://swagger.io/specification/)

#### doc

| 参数名称         | 参数类型   | 描述                          |
|--------------|--------|------------------------------|
| type         | string | 文档类型（通常为 markdown）         |
| content      | string | 文档内容（Markdown 格式）          |
| updated_time | string | 文档更新时间（ISO 8601 格式）        |

**注意：** 如果资源没有文档，此字段为 `null`

#### auth_config

| 参数名称                     | 参数类型    | 描述       |
|--------------------------|---------|----------|
| auth_verified_required   | boolean | 是否需要用户认证 |
| app_verified_required    | boolean | 是否需要应用认证 |
| resource_perm_required   | boolean | 是否需要资源权限 |

### 错误说明

- `404 Not Found`: 资源不存在、未公开或该环境未发布
- 需要确保指定的 `stage_name` 已经发布过版本

