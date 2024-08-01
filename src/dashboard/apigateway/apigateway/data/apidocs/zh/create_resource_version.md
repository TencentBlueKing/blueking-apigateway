### 描述

网关生成新版本


### 输入参数

#### 路径参数

| 参数名称 | 参数类型 | 必选 | 描述   |
| -------- | -------- | ---- | ------ |
| api_name | string   | 是   | 网关名 |

#### 请求参数

| 参数名称 | 参数类型 | 必选 | 描述                       |
| -------- | -------- |----| -------------------------- |
| version  | string   | 是  | 版本号，须符合 Semver 规范 |
| title    | string   | 否  | 版本标题                   |
| comment  | string   | 否  | 版本说明                   |

### 请求参数示例

```json
{
    "version": "1.0.0",
    "title": "发布新版本",
    "comment": "这是一个什么样的新版本"
}
```

### SDK 调用示例

```python
from bkapi.bk_apigateway.shortcuts import get_client_by_request

client = get_client_by_request(request)
result = client.api.create_resource_version(
    {
        "version": "1.0.0",
        "title": "发布新版本",
        "comment": "这是一个什么样的新版本"
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
        "version": "1.0.0",
        "title": "发布新版本"
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

| 参数名称 | 参数类型 | 描述       |
| -------- | -------- | ---------- |
| id       | int      | 资源版本ID |
| version  | string   | 版本号     |
| title    | string   | 版本标题   |
