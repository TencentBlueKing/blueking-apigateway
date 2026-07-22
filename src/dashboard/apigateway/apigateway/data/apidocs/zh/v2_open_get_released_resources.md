### 描述

查询网关指定环境下已发布的资源列表（released 语义）。

### 输入参数

#### 路径参数

| 参数名称       | 参数类型 | 必选 | 描述     |
|----------------|----------|------|----------|
| gateway_name   | string   | 是   | 网关名称 |
| stage_name     | string   | 是   | 环境名称 |

### 响应示例

```json
{
  "data": {
    "count": 1,
    "has_next": false,
    "has_previous": false,
    "results": [
      {
        "id": 3,
        "name": "echo",
        "kind": "standard",
        "description": "",
        "method": "GET",
        "url": "https://bkapi.example.com/api/bk-apigateway/prod/echo/",
        "match_subpath": false,
        "enable_websocket": false,
        "app_verified_required": true,
        "resource_perm_required": true,
        "user_verified_required": false
      }
    ]
  }
}
```

### 响应参数说明

| 字段 | 类型 | 描述     |
|------|------|----------|
| data | object | 分页数据 |

#### data

| 参数名称     | 参数类型 | 描述                                     |
|--------------|----------|------------------------------------------|
| count        | int      | 资源数量                                 |
| has_next     | boolean  | 分页，后续是否有数据                     |
| has_previous | boolean  | 分页，前面是否有数据                     |
| results      | array    | 本次查询结果数据                         |

#### data.results[]

| 参数名称               | 参数类型 | 描述                             |
|------------------------|----------|----------------------------------|
| id                     | int      | 资源 ID                          |
| name                   | string   | 资源名称                         |
| kind                   | string   | 资源类型，`standard`：普通 API，`ai`：模型代理 API |
| description            | string   | 资源描述                         |
| method                 | string   | 资源请求方法                     |
| url                    | string   | 资源请求地址                     |
| match_subpath          | boolean  | 是否匹配子路径                   |
| enable_websocket       | boolean  | 是否开启 websocket               |
| app_verified_required  | boolean  | 是否认证应用                     |
| resource_perm_required | boolean  | 是否校验访问权限                 |
| user_verified_required | boolean  | 是否认证用户                     |
