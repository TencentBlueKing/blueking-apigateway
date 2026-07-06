### 描述

应用维度调用流水日志列表（开发者视角）

### 输入参数

#### 路径参数

| 参数名称 | 参数类型 | 必选 | 描述 |
|---|---|---|---|
| app_code | string | 是 | 应用编码，必须与当前请求应用一致 |

#### 请求参数

| 参数名称 | 参数类型 | 必选 | 描述 |
|---|---|---|---|
| gateway_name | string | 否 | 网关名称（精确匹配） |
| resource_name | string | 否 | 资源名称（精确匹配） |
| request_id | string | 否 | 请求 ID |
| status | int | 否 | 响应状态码（100-599） |
| time_start | int | 是 | 开始时间（Unix 时间戳，秒），不能早于当前时间前 180 天 |
| time_end | int | 是 | 结束时间（Unix 时间戳，秒），必须大于 time_start 且小于当前时间 |
| offset | int | 否 | 偏移量，默认 0 |
| limit | int | 否 | 限制条数，默认 10，最大 100 |

### 响应示例

```json
{
  "data": {
    "count": 1,
    "has_next": false,
    "has_previous": false,
    "results": [
      {
        "request_id": "f1a0f0f4aef149d88b36e5",
        "timestamp": 1751366500,
        "gateway_name": "bk-user-api",
        "stage": "prod",
        "resource_id": 12,
        "resource_name": "list_users",
        "method": "GET",
        "http_host": "bk-user-api.example.com",
        "http_path": "/prod/users",
        "status": 200,
        "request_duration": 32,
        "code_name": "",
        "error": "",
        "response_desc": "OK"
      }
    ]
  }
}
```

### 响应参数说明

| 字段 | 类型 | 描述 |
|---|---|---|
| data | object | 结果数据，包含 count、has_next、has_previous 与 results |

#### data.results

| 参数名称 | 参数类型 | 描述 |
|---|---|---|
| request_id | string | 请求 ID |
| timestamp | int | 请求时间戳 |
| gateway_name | string | 网关名称 |
| stage | string | 环境名称 |
| resource_id | int | 资源 ID |
| resource_name | string | 资源名称 |
| method | string | 请求方法 |
| http_host | string | 请求域名 |
| http_path | string | 请求路径 |
| status | int | 响应状态码 |
| request_duration | int | 请求耗时 |
| code_name | string | 状态码名称 |
| error | string | 错误信息 |
| response_desc | string | 响应说明 |
