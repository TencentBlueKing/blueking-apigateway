### 描述

同步网关环境，如果环境不存在，创建环境，如果已存在，则更新。

普通网关可使用 `proxy_http` 或 `backends`；AI 网关可同时配置 `backends` 和 `modelBackends`，形成“环境 × 服务”的配置矩阵。创建环境时必须至少提供一种后端配置；更新时未传的列表保持不变，显式空列表不合法。`modelBackends` 仅允许 AI 网关使用。


### 输入参数

#### 路径参数

| 参数名称 | 参数类型 | 必选 | 描述   |
| -------- | -------- | ---- | ------ |
| api_name | string   | 是   | 网关名 |

#### 请求参数

| 参数名称    | 参数类型 | 必选 | 描述                                               |
| ----------- | -------- | ---- | -------------------------------------------------- |
| name        | string   | 是   | 环境名称                                           |
| description | string   | 否   | 中文描述                                           |
| description_en | string | 否 | 英文描述                                           |
| vars        | object   | 否   | 环境变量，包含变量名、值，变量名、值均为字符串类型 |
| proxy_http  | object   | 否   | 兼容的默认代理配置                                 |
| backends    | array    | 否   | 普通后端服务配置                                   |
| modelBackends | array  | 否   | 模型服务配置，仅 AI 网关支持                       |
| plugin_configs | array | 否   | 环境插件配置                                       |

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
| host     | string   | 是   | 以 http:// 或 https:// 开头的合法域名、service 地址或 ip:port |
| weight   | integer  | 否   | 权重，可选值 1 ~ 10000  |

backends 说明

| 参数名称 | 参数类型 | 必选 | 描述 |
| -------- | -------- | ---- | ---- |
| name | string | 是 | 普通后端服务名称 |
| config | object | 是 | 后端配置，包含秒级 `timeout`、`loadbalance` 和 `hosts` |

modelBackends 说明

| 参数名称 | 参数类型 | 必选 | 描述 |
| -------- | -------- | ---- | ---- |
| name | string | 是 | 模型服务名称，必须对应 `kind=ai` 的 Backend |
| config | object | 是 | 模型服务在当前环境的配置 |

modelBackends.config 说明

| 参数名称 | 参数类型 | 必选 | 描述 |
| -------- | -------- | ---- | ---- |
| timeout | integer | 否 | 超时时间，单位毫秒，默认 `30000` |
| instances | array | 是 | 模型实例列表；第一期必须且只能配置 1 个实例 |

instances 说明

| 参数名称 | 参数类型 | 必选 | 描述 |
| -------- | -------- | ---- | ---- |
| name | string | 是 | 实例名称 |
| provider | string | 是 | `openai`、`deepseek` 或 `openai-compatible` |
| weight | integer | 是 | 第一期固定为 `1` |
| auth.header | object | 否 | 发往模型服务的认证 Header；凭证入库时加密 |
| options.model | string | 是 | 模型名称 |
| override.endpoint | string | 否 | 自定义模型服务地址 |


### 请求参数示例

```json
{
    "name": "prod",
    "description": "正式环境",
    "vars": {
        "foo": "bar"
    },
    "modelBackends": [
        {
            "name": "openai-primary",
            "config": {
                "timeout": 30000,
                "instances": [
                    {
                        "name": "primary",
                        "provider": "openai-compatible",
                        "weight": 1,
                        "auth": {
                            "header": {
                                "Authorization": "Bearer <token>"
                            }
                        },
                        "options": {
                            "model": "gpt-4o"
                        },
                        "override": {
                            "endpoint": "https://llm.example.com/v1/chat/completions"
                        }
                    }
                ]
            }
        }
    ]
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
        "modelBackends": [
            {
                "name": "openai-primary",
                "config": {
                    "instances": [
                        {
                            "name": "primary",
                            "provider": "openai",
                            "weight": 1,
                            "options": {"model": "gpt-4o"}
                        }
                    ]
                }
            }
        ]
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
