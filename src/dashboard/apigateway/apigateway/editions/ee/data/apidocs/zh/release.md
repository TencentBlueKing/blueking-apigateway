### 描述

发布版本到网关环境

### 输入参数

#### 路径参数

| 参数名称 | 参数类型 | 必选 | 描述   |
| -------- | -------- | ---- | ------ |
| api_name | string   | 是   | 网关名 |

#### 请求参数

| 参数名称    | 参数类型 | 必选 | 描述               |
| ----------- | -------- | ---- | ------------------ |
| version     | string   | 是   | 待发布版本的版本号 |
| stage_names | array    | 是   | 待发布环境列表     |
| comment     | string   | 是   | 发布日志           |

### 请求参数示例

```json
{
    "version": "1.0.0",
    "stage_names": ["prod", "test", "dev"],
    "comment": "发布"
}
```

### SDK 调用示例

```python
from bkapi.bk_apigateway.shortcuts import get_client_by_request

client = get_client_by_request(request)
result = client.api.release(
    {
        "version": "1.0.0",
        "stage_names": ["prod", "test", "dev"],
        "comment": "发布"
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
        "version": "1.0.0",
        "stage_names": ["prod", "test", "dev"]
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

| 参数名称    | 参数类型 | 描述           |
| ----------- | -------- | -------------- |
| version     | string   | 发布版本号     |
| stage_names | array    | 发布环境名列表 |
