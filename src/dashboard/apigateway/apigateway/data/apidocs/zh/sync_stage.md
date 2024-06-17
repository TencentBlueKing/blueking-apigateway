### 描述

同步网关环境，如果环境不存在，创建环境，如果已存在，则更新


### 输入参数

#### 路径参数

| 参数名称 | 参数类型 | 必选 | 描述   |
| -------- | -------- | ---- | ------ |
| api_name | string   | 是   | 网关名 |

#### 请求参数

| 参数名称    | 参数类型 | 必选 | 描述                                               |
| ----------- | -------- | ---- | -------------------------------------------------- |
| name        | string   | 是   | 环境名称                                           |
| description | string   | 否   | 描述                                               |
| vars        | object   | 否   | 环境变量，包含变量名、值，变量名、值均为字符串类型 |
| proxy_http  | object   | 是   | 代理配置，具体内容参考下面描述                     |

proxy_http 说明

| 参数名称          | 参数类型 | 必选 | 描述                               |
| ----------------- | -------- | ---- | ---------------------------------- |
| timeout           | integer  | 是   | 超时时间，单位秒，取值范围 1 ~ 300 |
| upstreams         | object   | 是   | 后端服务地址，具体参考下面描述     |
| transform_headers | object   | 否   | Header 转换配置，具体参考下面描述  |

upstreams 说明

| 参数名称    | 参数类型 | 必选 | 描述                             |
| ----------- | -------- | ---- | -------------------------------- |
| loadbalance | string   | 是   | 负载均衡类型，可选值：roundrobin |
| hosts       | array    | 是   | 后端服务 Hosts，具体参考下面描述 |

transform_headers 说明

| 参数名称 | 参数类型 | 必选 | 描述                                                      |
| -------- | -------- | ---- | --------------------------------------------------------- |
| set      | object   | 否   | 设置 Header，网关请求后端接口时，将默认传递这些请求头     |
| delete   | array    | 否   | 删除 Header，网关请求后端接口时，将删除请求中的这些请求头 |

hosts 说明

| 参数名称 | 参数类型 | 必选 | 描述                    |
| -------- | -------- | ---- | ----------------------- |
| host     | string   | 是   | 后端服务域名、IP + 端口 |
| weight   | integer  | 否   | 权重，可选值 1 ~ 10000  |


### 请求参数示例

```json
{
    "name": "prod",
    "description": "正式环境",
    "vars": {
        "foo": "bar"
    },
    "proxy_http": {
        "timeout": 60,
        "upstreams": {
            "loadbalance": "roundrobin",
            "hosts": [
                {
                    "host": "http://api.example.com",
                    "weight": "100"
                }
            ]
        },
        "transform_headers": {
            "set": {
                "X-Token": "foo"
            },
            "delete": ["X-Test"]
        }
    }
}
```

### SDK 调用示例

```python
from bkapi.bk_apigateway.shortcuts import get_client_by_request

client = get_client_by_request(request)
result = client.api.sync_stage(
    {
        "name": "prod",
        "description": "正式环境",
        "proxy_http": {
            "timeout": 60,
            "upstreams": {
                "loadbalance": "roundrobin",
                "hosts": [
                    {
                        "host": "http://api.example.com"
                    }
                ]
            }
        }
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
| id       | integer  | 环境ID   |
| name     | string   | 环境名称 |
