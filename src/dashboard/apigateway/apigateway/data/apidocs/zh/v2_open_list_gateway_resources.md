### 描述

获取网关下的所有资源列表，返回完整的资源信息（包括后端服务、标签、文档、认证配置等）。

- 只返回公开的资源

### 输入参数

### 路径参数

| 参数名称         | 参数类型     | 参数位置  | 必须  | 描述    |
|--------------|----------|-------|-----|-------|
| gateway_name | string   | path  | 是   | 网关名称  |


### 响应示例


```json
{
    "code": 0,
    "message": "OK",
    "data": [
        {
            "id": 1,
            "name": "get_user_info",
            "description": "获取用户信息",
            "method": "GET",
            "path": "/api/v1/users/{user_id}/",
            "match_subpath": false,
            "enable_websocket": false,
            "is_public": true,
            "allow_apply_permission": true,
            "backend": {
                "id": 1,
                "name": "default"
            },
            "labels": [
                {
                    "id": 1,
                    "name": "用户管理"
                }
            ],
            "docs": [
                {
                    "id": 1,
                    "language": "zh"
                }
            ],
            "auth_config": {
                "auth_verified_required": true,
                "app_verified_required": true,
                "resource_perm_required": true
            }
        }
    ]
}
```


### 响应参数说明

| 字段      | 类型            | 描述                                   |
|---------|---------------|--------------------------------------|
| code    | int           | 返回码，0 表示成功，其它值表示失败                  |
| message | string        | 错误信息                                 |
| data    | array | 结果数据 |

#### data（不分页时为数组）

| 参数名称                  | 参数类型    | 描述                      |
|-----------------------|---------|-------------------------|
| id                    | int     | 资源 ID                   |
| name                  | string  | 资源名称                    |
| description           | string  | 资源描述                    |
| method                | string  | 请求方法（GET、POST 等）        |
| path                  | string  | 资源路径                    |
| match_subpath         | boolean | 是否匹配子路径                 |
| enable_websocket      | boolean | 是否启用 WebSocket          |
| is_public             | boolean | 是否公开                    |
| allow_apply_permission | boolean | 是否允许申请权限                |
| backend               | object  | 后端服务信息，详见 backend 说明    |
| labels                | array   | 标签列表，详见 labels[] 说明     |
| docs                  | array   | 资源文档列表，详见 docs[] 说明     |
| auth_config           | object  | 认证配置，详见 auth_config 说明  |


#### backend

| 参数名称  | 参数类型   | 描述      |
|-------|--------|---------|
| id    | int    | 后端服务 ID |
| name  | string | 后端服务名称  |

#### labels[]

| 参数名称  | 参数类型   | 描述    |
|-------|--------|-------|
| id    | int    | 标签 ID |
| name  | string | 标签名称  |

#### docs[]

| 参数名称     | 参数类型   | 描述              |
|----------|--------|-----------------|
| id       | int    | 文档 ID           |
| language | string | 文档语言（zh、en 等） |

#### auth_config

| 参数名称                    | 参数类型    | 描述       |
|-------------------------|---------|----------|
| auth_verified_required  | boolean | 是否需要用户认证 |
| app_verified_required   | boolean | 是否需要应用认证 |
| resource_perm_required  | boolean | 是否需要资源权限 |

