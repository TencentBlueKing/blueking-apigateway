### 描述

查询网关指定环境下，已发布的资源列表


### 输入参数

#### 路径参数

| 参数名称   | 参数类型 | 必选 | 描述   |
| ---------- | -------- | ---- | ------ |
| api_name   | string   | 是   | 网关名 |
| stage_name | string   | 是   | 环境名 |

### 请求参数示例

```json
{}
```

### SDK 调用示例

```python
from bkapi.bk_apigateway.shortcuts import get_client_by_request

client = get_client_by_request(request)
result = client.api.get_released_resources(
    {},
    path_params={
        "api_name": "demo",
        "stage_name": "prod"
    },
)
```


### 响应示例

```json
{
    "code": 0,
    "message": "OK",
    "data": {
        "count": 2,
        "has_next": false,
        "has_previous": false,
        "results": [
            {
                "id": 3,
                "name": "echo",
                "description": "",
                "method": "GET",
                "url": "https://bkapi.example.com/api/echo/prod/echo/",
                "match_subpath": false,
                "enable_websocket": false,
                "app_verified_required": false,
                "resource_perm_required": false,
                "user_verified_required": false
            }
        ]
    }
}
```

### 响应参数说明

| 字段    | 类型   | 描述                               |
| ------- | ------ | ---------------------------------- |
| code    | int    | 返回码，0 表示成功，其它值表示失败 |
| message | string | 错误信息                           |
| data    | object | 结果数据，详细信息请见下面说明     |

#### data

| 参数名称     | 参数类型 | 描述                                     |
| ------------ | -------- | ---------------------------------------- |
| count        | int      | 资源数量                                 |
| has_next     | boolean  | 分页，后续是否有数据                     |
| has_previous | boolean  | 分页，前面是否有数据                     |
| results      | array    | 本次查询的结果数据，详细信息请见下面说明 |

data.results 中字段说明

| 参数名称               | 参数类型 | 描述                                                                |
| ---------------------- | -------- | ------------------------------------------------------------------- |
| id                     | int      | ID                                                                  |
| name                   | string   | 资源名称                                                            |
| description            | string   | 资源描述                                                            |
| method                 | string   | 资源请求方法                                                        |
| url                    | string   | 资源请求地址                                                        |
| match_subpath          | boolean  | 是否匹配子路径，如果匹配，则路径为 /echo/ 时，支持匹配 /echo/other/ |
| enable_websocket       | boolean  | 是否开启 websocket |
| app_verified_required  | boolean  | 是否认证应用                                                        |
| resource_perm_required | boolean  | 是否校验访问权限，如果校验，则应用需申请资源访问权限                |
| user_verified_required | boolean  | 是否认证用户                                                        |