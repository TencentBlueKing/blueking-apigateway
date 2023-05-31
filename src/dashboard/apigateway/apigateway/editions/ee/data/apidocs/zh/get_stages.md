### 描述

查询网关环境列表


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
result = client.api.get_stages(
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
    "data": [
        {
            "id": 1,
            "name": "prod",
            "description": "正式环境"
        }
    ]
}
```

### 响应参数说明

| 字段    | 类型   | 描述                               |
| ------- | ------ | ---------------------------------- |
| code    | int    | 返回码，0 表示成功，其它值表示失败 |
| message | string | 错误信息                           |
| data    | array  | 结果数据，详细信息请见下面说明     |

#### data

| 参数名称    | 参数类型 | 描述     |
| ----------- | -------- | -------- |
| id          | int      | 环境ID   |
| name        | string   | 环境名称 |
| description | string   | 环境描述 |
