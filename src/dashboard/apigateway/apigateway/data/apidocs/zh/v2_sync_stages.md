### 描述

同步网关环境，如果环境不存在，创建环境，如果已存在，则更新。

AI 网关可同时配置 `backends` 和 `modelBackends`，形成“环境 × 服务”的配置矩阵。创建环境时两者至少提供一项；更新时未传的列表保持不变，显式空列表不合法。`modelBackends` 仅允许 AI 网关使用。


### 输入参数

#### 路径参数

| 参数名称   | 参数类型 | 必选 | 描述   |
|--------| -------- | ---- | ------ |
| gateway_name | string   | 是   | 网关名 |

#### 请求参数

| 参数名称         | 参数类型       | 必选 | 描述                                                                 |
| ---------------- | -------------- | ---- | -------------------------------------------------------------------- |
| `name`           | string         | 是   | 环境名称（例如 `"stag"`）                                            |
| `description`    | string         | 否   | 中文描述（例如 `"预发布环境"`）                                      |
| `description_en`| string         | 否   | 英文描述（例如 `"Staging Env"`）                                     |
| `vars`           | object         | 否   | 环境变量（键值对均为字符串类型，示例：`{ "api_sub_path": "/test" }`）|
| `backends`       | array[object]  | 否   | 普通后端服务配置列表，参考下方 **backends 参数说明**                 |
| `modelBackends`  | array[object]  | 否   | 模型服务配置列表，仅 AI 网关支持                                    |
| `plugin_configs` | array[object]  | 否   | 插件配置列表，参考下方 **plugin_configs 参数说明**                   |


backends 参数说明
每个后端服务配置对象包含：

| 参数名称  | 参数类型       | 必选 | 描述                                       |
| --------- | -------------- | ---- | ------------------------------------------ |
| `name`    | string         | 是   | 后端服务名称（例如 `"default"`）           |
| `config`  | object         | 是   | 后端配置，参考下方 **config 参数说明**     |


config 参数说明（属于 backends）

| 参数名称        | 参数类型       | 必选 | 描述                                                                 |
| --------------- | -------------- | ---- | -------------------------------------------------------------------- |
| `timeout`       | integer        | 是   | 超时时间（单位：秒，例如 `60`）                                      |
| `loadbalance`   | string         | 是   | 负载均衡类型，可选值：`roundrobin`                                   |
| `hosts`         | array[object]  | 是   | 后端服务地址列表，参考下方 **hosts 参数说明**                        |

hosts 参数说明（属于 config）

| 参数名称  | 参数类型  | 必选 | 描述                                                               |
| --------- | --------- | ---- | ------------------------------------------------------------------ |
| `host`    | string    | 是   |以 http:// 或 https:// 开头的合法域名、service 地址或 ip:port |
| `weight`  | integer   | 否   | 权重，取值范围 `1 ~ 100`（未提供时默认均衡分配）                   |

modelBackends 参数说明

| 参数名称 | 参数类型 | 必选 | 描述 |
| -------- | -------- | ---- | ---- |
| `name` | string | 是 | 模型服务名称，必须对应 `kind=ai` 的 Backend |
| `config` | object | 是 | 模型服务在当前环境的配置 |

modelBackends.config 参数说明

| 参数名称 | 参数类型 | 必选 | 描述 |
| -------- | -------- | ---- | ---- |
| `timeout` | integer | 否 | 超时时间，单位毫秒，默认 `30000` |
| `instances` | array[object] | 是 | 模型实例列表；第一期必须且只能配置 1 个实例 |

instances 参数说明

| 参数名称 | 参数类型 | 必选 | 描述 |
| -------- | -------- | ---- | ---- |
| `name` | string | 是 | 实例名称 |
| `provider` | string | 是 | `openai`、`deepseek` 或 `openai-compatible` |
| `weight` | integer | 是 | 第一期固定为 `1` |
| `auth.header` | object | 否 | 发往模型服务的认证 Header；凭证入库时加密 |
| `options.model` | string | 是 | 模型名称 |
| `override.endpoint` | string | 否 | 自定义模型服务地址 |

plugin_configs 参数说明
每个插件配置对象包含：

| 参数名称  | 参数类型  | 必选 | 描述                                                                 |
| --------- | --------- | ---- | -------------------------------------------------------------------- |
| `type`    | string    | 是   | 插件类型（例如 `"bk-rate-limit"`）                                   |
| `yaml`    | string    | 是   | YAML 格式的插件配置（需转义换行符，示例见下方代码块）                |


### 请求参数示例

```json
{
  "name": "demo",
  "description": "预发布环境",
  "description_en": "Staging Env",
  "vars": {
    "api_sub_path": "/test"
  },
  "backends": [
    {
      "name": "default",
      "config": {
        "timeout": 60,
        "loadbalance": "roundrobin",
        "hosts": [
          {
            "host": "http://xxx.com"
          }
        ]
      }
    }
  ],
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
  ],
  "plugin_configs": [
    {
      "type": "bk-rate-limit",
      "yaml": "rates:\n  __default:\n  - period: 60\n    tokens: 1000\n  demo3:\n  - period: 3600\n    tokens: 1000"
    }
  ]
}
```



### 响应示例

```json
{
    "data": {
        "id": 1,
        "name": "demo"
    }
}
```


#### 响应参数说明


| 字段    | 类型   | 描述                               |
| ------- | ------ | ---------------------------------- |
| data    | object | 结果数据，详细信息请见下面说明     |

data

| 参数名称 | 参数类型 | 描述     |
| -------- | -------- | -------- |
| id       | integer  | 环境ID   |
| name     | string   | 环境名称 |
