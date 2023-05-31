### 描述

根据 tar/zip 归档文件，导入资源文档

资源文档 tar/zip 归档文件的准备，请参考网关使用指南：网关 API -> 操作指南 -> 导入网关 API 文档。

### 输入参数

#### 路径参数

| 参数名称 | 参数类型 | 必选 | 描述   |
| -------- | -------- | ---- | ------ |
| api_name | string   | 是   | 网关名 |

#### 请求参数

| 参数名称 | 参数类型 | 必选 | 描述                                                                |
| -------- | -------- | ---- | ------------------------------------------------------------------- |
| file     | object   | 是   | 资源文档的归档文件对象，请使用 multipart/form-data 类型传递文件内容 |


### SDK 调用示例

```python
from bkapi.bk_apigateway.shortcuts import get_client_by_request

client = get_client_by_request(request)
result = client.api.import_resource_docs_by_archive({}, files={"file": open("apidocs.tar.gz", "rb")})
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