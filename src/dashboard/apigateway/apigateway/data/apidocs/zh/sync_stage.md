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
| proxy_http  | object   | 否   | 代理配置，具体内容参考下面描述；与 `ai_backends` 至少提供一种 |
| ai_backends | array[object] | 否 | 模型服务配置列表，仅 AI 网关支持                  |

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

ai_backends 说明

| 参数名称 | 参数类型 | 必选 | 描述 |
| -------- | -------- | ---- | ---- |
| name | string | 是 | 模型服务名称 |
| config | object | 是 | 模型服务在当前环境的配置 |

ai_backends.config 说明

| 参数名称 | 参数类型 | 必选 | 描述 |
| -------- | -------- | ---- | ---- |
| timeout | integer | 否 | 超时时间，单位秒，默认 `300`，范围 `1..300` |
| instances | array[object] | 是 | 至少一个主实例，最多一个备用实例 |
| balancer | object | 否 | 多实例公共负载均衡配置，algorithm 为 roundrobin（默认）或 chash |
| fallback_strategy | array[string] | 否 | 多实例默认启用 http_429、http_5xx；仅主池可传空数组关闭重试 |

instances 说明

| 参数名称 | 参数类型 | 必选 | 描述 |
| -------- | -------- | ---- | ---- |
| name | string | 是 | 非空、配置内唯一且稳定的实例名 |
| provider | string | 是 | `openai`、`deepseek` 或 `openai-compatible` |
| priority | integer | 否 | `10` 为主实例（默认），`0` 为备用实例；至少一主、最多一备 |
| weight | integer | 否 | 多实例固定为 `1`，可省略；旧单实例兼容默认 `0` |
| auth.header | object | 否 | 认证 Header 映射，可包含多个 Header |
| options | object | 否 | 模型参数；`model` 可选，其他 JSON 字段完整保存 |
| override.endpoint | string | 否 | `openai-compatible` 必填的 Chat Completions 地址 |
| model_endpoint | string | 否 | 自定义 Models API；连接测试使用，不发布到 APISIX |


多实例调度规则：

- 所有实例共用外层 timeout（秒），它不是整个重试链的总期限。
- chash 固定按调用应用编码分配：hash_on 为 `vars_combinations`，key 为 `$bk_app_code`。两项可省略，由后端填入；不支持其他哈希变量。roundrobin 不接受哈希参数。
- `fallback_strategy` 仅支持 `http_429`、`http_5xx`；重复项会去重。429 指模型上游限流；5xx 也包括映射后的连接失败和超时。400/401/403 不触发重试。
- 主池候选耗尽后进入备用实例；有备用实例时至少开启一项重试条件。
- 更新时完整替换所提交配置的 instances 数组；从数组移除即删除该实例，不新增独立实例接口。
- 单实例省略调度配置；显式空策略会移除。其他调度配置在单实例下会被拒绝。
- 认证值按字面值处理，不使用 Web 的掩码回填逻辑；配置继续整体加密保存。

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

AI 网关模型服务示例：

```json
{
    "name": "prod",
    "description": "正式环境",
    "ai_backends": [
        {
            "name": "openai-primary",
            "config": {
                "timeout": 300,
                "instances": [
                    {
                        "name": "primary",
                        "provider": "openai",
                        "auth": {
                            "header": {
                                "Authorization": "Bearer <token>"
                            }
                        }
                    }
                ]
            }
        },
        {
            "name": "custom-models",
            "config": {
                "instances": [
                    {
                        "name": "primary",
                        "provider": "openai-compatible",
                        "auth": {
                            "header": {
                                "X-Api-Key": "<token>",
                                "X-Tenant": "tenant-a"
                            }
                        },
                        "override": {
                            "endpoint": "https://llm.example.com/v1/chat/completions"
                        },
                        "model_endpoint": "https://llm.example.com/v1/models"
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
