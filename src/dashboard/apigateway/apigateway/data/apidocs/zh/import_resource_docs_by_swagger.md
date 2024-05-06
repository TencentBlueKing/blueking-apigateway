### 描述

根据 swagger 描述文件，导入资源文档

### 输入参数

#### 路径参数

| 参数名称 | 参数类型 | 必选 | 描述   |
| -------- | -------- | ---- | ------ |
| api_name | string   | 是   | 网关名 |

#### 请求参数

| 参数名称 | 参数类型 | 必选 | 描述                                       |
| -------- | -------- | ---- | ------------------------------------------ |
| language | string   | 是   | 文档语言，可选值：zh 表示中文，en 表示英文 |
| swagger  | string   | 是   | swagger 描述文件的内容                     |


### 请求参数示例

```json
{
    "language": "zh",
    "swagger": "xxx"
}
```

### SDK 调用示例

```python
from bkapi.bk_apigateway.shortcuts import get_client_by_request

client = get_client_by_request(request)
result = client.api.import_resource_docs_by_swagger(
    {
        "language": "zh",
        "swagger": "xxx"
    }
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