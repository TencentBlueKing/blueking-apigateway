### 描述

添加网关关联应用，网关的关联应用，将有权限管理网关数据


### 输入参数

#### 路径参数

| 参数名称 | 参数类型 | 必选 | 描述   |
| -------- | -------- | ---- | ------ |
| api_name | string   | 是   | 网关名 |

#### 请求参数

| 参数名称         | 参数类型 | 必选 | 描述         |
| ---------------- | -------- | ---- | ------------ |
| target_app_codes | array    | 是   | 目标应用列表 |

### 请求参数示例

```json
{
    "target_app_codes": ["my-app"]
}
```

### SDK 调用示例

```python
from bkapi.bk_apigateway.shortcuts import get_client_by_request

client = get_client_by_request(request)
result = client.api.add_related_apps(
    {
        "target_app_codes": ["my-app"]
    },
    path_params={
        "api_name": "demo",
    },
    headers={"Content-Type": "application/json"},
)
```


### 响应示例

```json
{
    "code": 0,
    "message": "OK",
    "data": {}
}
```

### 响应参数说明

| 字段    | 类型   | 描述                               |
| ------- | ------ | ---------------------------------- |
| code    | int    | 返回码，0 表示成功，其它值表示失败 |
| message | string | 错误信息                           |
| data    | object | 空                                 |