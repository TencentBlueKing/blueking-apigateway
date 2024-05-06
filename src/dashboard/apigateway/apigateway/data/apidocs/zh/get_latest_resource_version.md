### 描述

获取网关最新的资源版本

### 输入参数

#### 路径参数

| 参数名称 | 参数类型 | 必选 | 描述   |
| -------- | -------- | ---- | ------ |
| api_name | string   | 是   | 网关名 |


### 请求参数示例

```json
{}
```

### SDK 调用示例

```python
from bkapi.bk_apigateway.shortcuts import get_client_by_request

client = get_client_by_request(request)
result = client.api.get_latest_resource_version({})
```


### 响应示例

```json
{
    "code": 0,
    "message": "OK",
    "data": {
        "version": "1.0.1"
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

| 名称    | 类型   | 说明             |
| ------- | ------ | ---------------- |
| version | string | 资源版本的版本号 |