### 描述

查询网关公钥，公钥可用于解析网关请求后端接口时，请求头 X-Bkapi-Jwt 中内容


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
result = client.api.get_apigw_public_key(
    {},
    path_params={
        "api_name": "demo",
    },
)
```


### 响应示例

```json
{
    "code": 0,
    "message": "OK",
    "data": {
        "issuer": "",
        "public_key": "xxx"
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

| 参数名称   | 参数类型 | 描述                                                                                                                                       |
| ---------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| issuer     | string   | 签发者，非空时，网关请求后端传递的请求头 X-Bkapi-Jwt 的 jwt header 中，会包含 iss 字段表示此值，后端可依据此 issuer 区分不同的网关服务实例 |
| public_key | string   | 网关公钥                                                                                                                                   |
