### 描述

回收蓝鲸应用访问网关资源的权限

### 输入参数

#### 路径参数

| 参数名称 | 参数类型 | 必选 | 描述   |
| -------- | -------- | ---- | ------ |
| api_name | string   | 是   | 网关名 |

#### 请求参数

| 参数名称         | 参数类型 | 必选 | 描述                              |
| ---------------- | -------- | ---- | --------------------------------- |
| target_app_codes | array    | 是   | 待回收权限的应用列表              |
| grant_dimension  | string   | 是   | 授权维度，可选值：api(按网关授权) |

### 请求参数示例

```json
{
    "target_app_codes": ["bk-sops"],
    "grant_dimension": "api"
}
```

### SDK 调用示例

```python
from bkapi.bk_apigateway.shortcuts import get_client_by_request

client = get_client_by_request(request)
result = client.api.revoke_permissions(
    {
        "target_app_codes": ["bk-sops"],
        "grant_dimension": "api"
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
    "data": null
}
```

### 响应参数说明

| 字段    | 类型   | 描述                               |
| ------- | ------ | ---------------------------------- |
| code    | int    | 返回码，0 表示成功，其它值表示失败 |
| message | string | 错误信息                           |
| data    | object | 空                                 |
