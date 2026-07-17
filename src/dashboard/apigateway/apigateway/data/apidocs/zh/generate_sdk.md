### 描述

异步生成资源版本对应的 SDK。请求受理后，构建完成的包将发布到已配置的软件仓库。

### 输入参数

#### 路径参数

| 参数名称 | 参数类型 | 必选 | 描述   |
| -------- | -------- | ---- | ------ |
| api_name | string   | 是   | 网关名 |

#### 请求参数

| 参数名称         | 参数类型      | 必选 | 描述                                                     |
| ---------------- | ------------- | ---- | -------------------------------------------------------- |
| resource_version | string        | 是   | 资源版本的版本号                                         |
| languages        | array[string] | 否   | 需要生成 SDK 的语言列表，可选值：python、java、go、javascript、rust，默认为 python |

### 请求参数示例

```json
{
    "resource_version": "1.0.1",
    "languages": ["python", "go"]
}
```

### SDK 调用示例

```python
from bkapi.bk_apigateway.shortcuts import get_client_by_request

client = get_client_by_request(request)
result = client.api.generate_sdk(
    {
        "resource_version": "1.0.1",
        "languages": ["python", "go"]
    }
)
```


### 响应示例

```json
{
    "code": 0,
    "message": "SDK generation started",
    "data": []
}
```

### 响应参数说明

| 字段    | 类型   | 描述                               |
| ------- | ------ | ---------------------------------- |
| code    | int    | 返回码，0 表示成功，其它值表示失败 |
| message | string | 受理结果                           |
| data    | array  | 为兼容 V1 客户端固定返回空数组     |
