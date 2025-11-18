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
            "labels": [
                {
                    "id": 1,
                    "name": "用户管理"
                }
            ],
            "auth_config": {
                "user_verified_required": true,
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
| labels                | array   | 标签列表，详见 labels[] 说明     |
| auth_config           | object  | 认证配置，详见 auth_config 说明  |



#### labels[]

| 参数名称  | 参数类型   | 描述    |
|-------|--------|-------|
| id    | int    | 标签 ID |
| name  | string | 标签名称  |


#### auth_config

| 参数名称                     | 参数类型    | 描述                                                                                                                                   |
|--------------------------|---------|--------------------------------------------------------------------------------------------------------------------------------------|
| user_verified_required   | boolean | 是否需要用户认证; True: 那么调用接口需要提供用户身份bk_ticket; 认证请求头：X-Bkapi-Authorization: {"bk_ticket": "x"}                                             |
| app_verified_required    | boolean | 是否需要应用认证; True: 那么调用接口需要提供应用身份：bk_app_code+bk_app_secret; 认证请求头: . X-Bkapi-Authorization: {"bk_app_code": "x", "bk_app_secret": "y"} |
| resource_perm_required   | boolean | 是否需要资源权限; True: 则需要申请该资源权限才可以调用                                                                                                      |
