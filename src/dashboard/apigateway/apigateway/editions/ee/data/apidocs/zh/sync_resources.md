### 描述

同步资源


### 输入参数

#### 路径参数

| 参数名称 | 参数类型 | 必选 | 描述   |
| -------- | -------- | ---- | ------ |
| api_name | string   | 是   | 网关名 |

#### 请求参数

| 参数名称 | 参数类型 | 必选 | 描述                                                                                                                  |
| -------- | -------- | ---- | --------------------------------------------------------------------------------------------------------------------- |
| content  | string   | 是   | 网关资源 swagger 描述，可为 yaml 格式文本，具体参考网关资源导出的资源配置                                             |
| delete   | boolean  | 否   | 是否删除未指定的资源，如果为 true，则删除网关中未在 content 中指定的资源，以确保网关中资源和 content 中描述的资源一致 |

### 请求参数示例

```json
{
    "content": "xxx",
    "delete": false
}
```

### SDK 调用示例

```python
from bkapi.bk_apigateway.shortcuts import get_client_by_request

client = get_client_by_request(request)
result = client.api.sync_resources(
    {
        "content": "xxx",
        "delete": False
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
        "added": [{"id": 1}],
        "updated": [{"id": 2}],
        "deleted": [{"id": 3}]
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

| 参数名称 | 参数类型 | 描述                                |
| -------- | -------- | ----------------------------------- |
| added    | array    | 新增的资源，其中数据，id 表示资源ID |
| updated  | array    | 更新的资源，其中数据，id 表示资源ID |
| deleted  | array    | 删除的资源，其中数据，id 表示资源ID |
