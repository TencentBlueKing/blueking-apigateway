### 描述

主动授权，给应用添加访问网关资源的权限


### 输入参数

#### 路径参数

| 参数名称 | 参数类型 | 必选 | 描述   |
| -------- | -------- | ---- | ------ |
| api_name | string   | 是   | 网关名 |

#### 请求参数

| 参数名称        | 参数类型 | 必选 | 描述                                                      |
| --------------- | -------- | ---- | --------------------------------------------------------- |
| target_app_code | string   | 是   | 待授权应用                                                |
| expire_days     | int      | 否   | 过期时间，单位天                                          |
| grant_dimension | string   | 是   | 授权维度，可选值：api(按网关授权)，resource（按资源授权） |
| resource_names  | array    | 否   | 按资源授权时，需指定待授权的资源名列表                    |

### 请求参数示例

```json
{
    "target_app_code": "bk-sops",
    "grant_dimension": "api"
}
```

### SDK 调用示例

```python
from bkapi.bk_apigateway.shortcuts import get_client_by_request

client = get_client_by_request(request)
result = client.api.grant_permissions(
    {
        "target_app_code": "bk-sops",
        "grant_dimension": "resource",
        "resource_names": ["get_color", "create_color"]
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
