### 描述

同步网关，如果网关不存在，创建网关，如果网关已存在，更新网关


### 输入参数

#### 路径参数

| 参数名称 | 参数类型 | 必选 | 描述   |
| -------- | -------- | ---- | ------ |
| api_name | string   | 是   | 网关名 |

#### 请求参数

| 参数名称    | 参数类型 | 必选 | 描述                   |
| ----------- | -------- |----| ---------------------- |
| description | string   | 否  | 网关描述               |
| maintainers | array    | 否  | 网关管理员             |
| is_public   | boolean  | 否  | 网关是否公开，默认公开 |

### 请求参数示例

```json
{
    "description": "just for test",
    "maintainers": ["admin"],
    "is_public": true
}
```

### SDK 调用示例

```python
from bkapi.bk_apigateway.shortcuts import get_client_by_request

client = get_client_by_request(request)
result = client.api.sync_api(
    {
        "description": "just for test",
        "maintainers": ["admin"],
        "is_public": True
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
    "data": {
        "id": 1,
        "name": "demo"
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

| 参数名称 | 参数类型 | 描述     |
| -------- | -------- | -------- |
| id       | int      | 网关ID   |
| name     | string   | 网关名称 |
