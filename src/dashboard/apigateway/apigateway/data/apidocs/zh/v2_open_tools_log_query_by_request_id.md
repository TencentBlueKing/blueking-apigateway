### 描述

根据 request_id 查询访问日志。

### 输入参数

#### 请求参数

| 参数名称 | 参数类型 | 必选 | 描述 |
|----------|----------|------|------|
| request_id | string | 是 | 请求 ID，36 位 UUID |

### 响应示例

```json
{
  "data": [
    {
      "request_id": "61fee544-be60-4e06-85b5-23befebc2bd0",
      "timestamp": 1785998318,
      "stage": "prod",
      "resource_id": 13649,
      "resource_name": "ai_resource_mrsmshr2",
      "app_code": "bk_apigw_test",
      "client_ip": "10.0.6.23",
      "method": "POST",
      "http_host": "bkapi-dev.example.com",
      "http_path": "/api/aigateway-mrsmshr2/prod/ai-mrsmshr2/chat/completions",
      "params": "",
      "body": "{\"messages\": [{\"role\": \"user\", \"content\": \"Hello\"}]}",
      "backend_scheme": "http",
      "backend_method": "POST",
      "backend_host": "",
      "backend_path": "",
      "response_body": "",
      "status": 200,
      "request_duration": 11663,
      "backend_duration": 0,
      "llm_summary": {
        "request_model": "",
        "prompt_tokens": 107,
        "completion_tokens": 1718,
        "upstream_response_time": 11662,
        "model": "deepseek-v4-flash",
        "duration": 11662
      },
      "code_name": "",
      "error": "",
      "response_desc": "网关已请求后端接口，并将其响应原样返回。"
    }
  ]
}
```

### 响应参数说明

| 字段 | 类型 | 描述 |
|------|------|------|
| data | array | 访问日志列表 |

#### data

| 参数名称 | 参数类型 | 描述 |
|----------|----------|------|
| request_id | string | 请求 ID |
| timestamp | int | 请求时间戳 |
| stage | string | 环境名称 |
| resource_id | int | 资源 ID |
| resource_name | string | 资源名称 |
| app_code | string | 应用编码 |
| client_ip | string | 客户端 IP |
| method | string | 请求方法 |
| http_host | string | 请求域名 |
| http_path | string | 请求路径 |
| params | string | 请求参数 |
| body | string | 请求体 |
| backend_scheme | string | 后端请求协议 |
| backend_method | string | 后端请求方法 |
| backend_host | string | 后端请求域名 |
| backend_path | string | 后端请求路径 |
| response_body | string | 响应体 |
| status | int | 响应状态码 |
| request_duration | int | 请求耗时，单位毫秒 |
| backend_duration | int | 后端请求耗时，单位毫秒 |
| llm_summary | object/null | LLM 调用摘要，模型代理请求返回摘要，其他请求为 null |
| code_name | string | 状态码名称 |
| error | string | 错误信息 |
| response_desc | string | 响应说明 |
