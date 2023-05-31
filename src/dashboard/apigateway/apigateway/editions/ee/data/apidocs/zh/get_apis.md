### 描述

查询网关列表


### 输入参数

### 请求参数示例

```json
{}
```

### SDK 调用示例

```python
from bkapi.bk_apigateway.shortcuts import get_client_by_request

client = get_client_by_request(request)
result = client.api.get_apis({})
```


### 响应示例

```json
{
    "code": 0,
    "message": "OK",
    "data": [
        {
            "id": 1,
            "name": "bk-apigateway",
            "description": "",
            "maintainers": [
                "admin"
            ],
            "api_type": 10,
            "user_auth_type": "default"
        }
    ]
}
```

### 响应参数说明

| 字段    | 类型   | 描述                               |
| ------- | ------ | ---------------------------------- |
| code    | int    | 返回码，0 表示成功，其它值表示失败 |
| message | string | 错误信息                           |
| data    | array  | 结果数据，详细信息请见下面说明     |

#### data

| 参数名称       | 参数类型 | 描述                                |
| -------------- | -------- | ----------------------------------- |
| id             | int      | 网关ID                              |
| name           | string   | 网关名称                            |
| description    | string   | 网关描述                            |
| maintainers    | array    | 网关管理员                          |
| api_type       | int      | 网关类型，可选值: 10(普通网关)      |
| user_auth_type | string   | 用户类型，可选值：default(蓝鲸用户) |
