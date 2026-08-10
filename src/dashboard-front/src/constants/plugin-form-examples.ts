// 插件表单填写示例
export const PLUGIN_FORM_EXAMPLE_CN: { [pluginCode: string]: string } = {
  // proxy-cache
  'proxy-cache': `作用：可缓存 GET 请求的响应数据 300 秒

cache_method: ["GET"]
cache_ttl: 300`,
  // bk-user-restriction
  'bk-user-restriction': `作用：仅允许用户 admin 请求当前接口

类型：白名单
白名单： ["admin"]
message: "The bk-user is not allowed"`,
  // bk-request-body-limit
  'bk-request-body-limit': `作用：限制请求体大小为 100 B

max_body_size: 100`,
  // bk-access-token-source
  'bk-access-token-source': `作用：来源为 bearer 时，从请求 header 中获取 Authorization，来源为 api_key 时，从请求 header 中获取 X-API-KEY

source: bearer`,
  // ai-proxy
  'ai-proxy': `作用：配置 API 密钥、模型和其他参数，将用户提示代理到 OpenAI

provider: "openai"
auth: {"header": {"Authorization": "Bearer key"}}
options: {"model": "gpt-4"}`,
  // ai-rate-limiting
  'ai-rate-limiting': `作用：配置每秒限制20个请求，超出限制则返回 503 状态码和错误响应。

limit: 20
time_window: 1
show_limit_quota_header: true
limit_strategy: total_tokens
rejected_code: 503
rejected_msg: "test..."`,
  // redirect
  'redirect': `重定向 URI: /test/default.html,
HTTP 响应码: 301`,
  // bk-mock
  'bk-mock': `作用：返回 json response，状态码为 200，并且携带响应头 foo:bar

响应状态码：200
响应体：{"hello": "world"}
响应头：
      Content-Type: application/json
      foo: bar`,
  // response-rewrite
  'response-rewrite': `"status_code": 200,
"body": {"code":"ok","message":"new json body"},
"headers": {
  "add": ["X-Server-balancer-addr: test"],
  "set": {"X-Server-id": 3},
  "remove": ["X-TO-BE-REMOVED"]
},
"vars": [[["arg_name", "==", "jack"], ["arg_age", "==", 18]]]`,
  // fault-injection
  'fault-injection': `作用：当请求参数 name 等于 jack，并且 age 等于 18 的时候，则返回 400 拒绝状态码和响应内容

"abort": {
    "http_status": 400,
    "body": "not valid request params",
    "vars": [[["arg_name", "==", "jack"], ["arg_age", "==", 18]]]
}`,
  // request-validation
  'request-validation': `作用：当请求体中没有包含 boolean_payload 时，则返回 400 拒绝状态码和拒绝信息

"body_schema": {
  "type": "object",
  "required": ["bool_payload"],
  "properties": {
    "bool_payload": {
      "type": "boolean"
    }
  }
}
"header_schema": {}
"rejected_code": 400
"rejected_msg": "not valid request body"`,
  // api-breaker
  'api-breaker': `作用：当后端服务返回状态码 500 或 503，并达到 3 次，则触发熔断，返回响应体 hello world，状态码为 502，并且携带响应头 foo:bar。
第一次触发不健康状态时，熔断 2 秒。超过熔断时间后，将重新开始转发请求到上游服务，如果继续返回 500 状态码，当计数再次达到 3 次时，熔断 4 秒。依次类推（2，4，8，16，……），直到达到预设的最大熔断时间 300 秒。
当上游服务处于不健康状态时，如果后端服务返回状态码 200，并达到 2 次时，则认为上游服务恢复至健康状态。

break_response_code：502
break_response_body：helloworld
break_response_headers： [ { "key": "foo", "value": "bar" } ]
max_breaker_sec：300
unhealthy： { "http_statuses": [ 500, 503 ], "failures": 3 }
healthy： { "http_statuses": [ 200 ], "successes": 2 }`,
  // bk-cors
  'bk-cors': `作用：允许 https://a.example.com:8081, https://b.example.com:8081 这两个站点发起跨域请求

allow_origins:
allow_origins_by_regex: ^https://.*\\.example\\.com:8081$
allow_methods: GET,POST,PUT,PATCH,HEAD,DELETE,OPTIONS
allow_headers: **
expose_headers:
max_age: 86400
allow_credential: false`,
  // bk-ip-restriction
  'bk-ip-restriction': `作用：仅允许 IP 192.168.1.1 和 192.168.1.2 请求当前接口

类型：白名单
白名单：
      # comment
       192.168.1.1
       192.168.1.2`,
  // bk-header-rewrite
  'bk-header-rewrite': `作用：设置 header \`X-Api-Version: 1\`，并且删除 header \`X-test\`

设置：X-Api-Version: 1
删除：X-test`,
  // bk-rate-limit
  'bk-rate-limit': `作用：默认每个应用 100 次/秒，应用 demo 200 次/秒

默认频率限制：

次数：100
时间范围：秒

特殊应用频率限制：
次数：200
时间范围：秒

蓝鲸应用 ID: demo`,
  // bk-traffic-label
  'bk-traffic-label': `# 一个match条件
     "bk-traffic-label": {
       "rules": [
         {
           "match": [
             ["uri", "==", "/headers"]
           ],
           "actions": [
             {
               "set_headers": {
                 "X-Server-Id": 100
               }
             }
           ]
         }
       ]
     }

# 一个match多个条件，有逻辑关系
     "bk-traffic-label": {
       "rules": [
         {
           "match": [
             "OR",
             ["arg_version", "==", "v1"],
             ["arg_env", "==", "dev"]
           ],
           "actions": [
             {
               "set_headers": {
                 "X-Server-Id": 100
               }
             }
           ]
         }
       ]
     }

# 一个match多个action，有权重的
# ❶ 30% of the requests should have the \`X-Server-Id: 100\` request header.
# ❷ 20% of the requests should have the \`X-API-Version: v2\` request header.
# ❸ 50% of the requests should not have any action performed on them.
     "bk-traffic-label": {
       "rules": [
         {
           "match": [
             ["uri", "==", "/headers"]
           ],
           "actions": [
             {
               "set_headers": {
                 "X-Server-Id": 100
               },
               "weight": 3
             },
             {
               "set_headers": {
                 "X-API-Version": "v2"
               },
               "weight": 2
             },
             {
               "weight": 5
             }
           ]
         }
       ]
     }

# 多个match   => 顺序执行
     "bk-traffic-label": {
       "rules": [
         {
           "match": [
             ["arg_version", "==", "v1"]
           ],
           "actions": [
             {
               "set_headers": {
                 "X-Server-Id": 100
               }
             }
           ]
         },
         {
           "match": [
             ["arg_version", "==", "v2"]
           ],
           "actions": [
             {
               "set_headers": {
                 "X-Server-Id": 200
               }
             }
           ]
         }
       ]
     }`,
  // uri-blocker
  'uri-blocker': `作用：当请求 URI 命中拦截规则时，直接返回 403，常用于阻断管理后台路径、内部路径或可疑扫描请求

拦截规则：
^/admin(?:/.*)?$
^/internal(?:/.*)?$
.*\\.php(?:\\?.*)?$
忽略大小写：true
拒绝状态码：403
拒绝消息：URI is blocked`,
  'bk-status-rewrite': '',
  'bk-legacy-invalid-params': '',
  'bk-username-required': '',
  'bk-oauth2-verify': '',
  'bk-oauth2-protected-resource': '',
  'bk-oauth2-audience-validate': '',
  // bk-query-string-rewrite
  'bk-query-string-rewrite': `示例：

Add version=v2
Set bk_app_code=demo
Remove debug


假设原始请求为：GET /users?name=tom&debug=true&bk_app_code=test

插件处理后，请求将变为：GET /users?name=tom&version=v2&bk_app_code=demo`,
};

export const PLUGIN_FORM_EXAMPLE_EN: { [pluginCode: string]: string } = {
  // proxy-cache
  'proxy-cache': `Purpose: The response data of GET request can be cached for 300 seconds.

cache_method: ["GET"]
cache_ttl: 300`,
  // bk-user-restriction
  'bk-user-restriction': `Purpose: Only User admin are allowed to request the current interface

Type: whitelist
whitelist: ["admin"]
message: "The bk-user is not allowed"`,
  // bk-request-body-limit
  'bk-request-body-limit': `Purpose: Limit the request body size to 100 B.

max_body_size: 100`,
  // bk-access-token-source
  'bk-access-token-source': `Purpose: When the source is bearer, get Authorization from the request header; When the source is api_key, get X-API-KEY from the request header.

source: bearer`,
  // ai-proxy
  'ai-proxy': `Purpose：Configure API keys, models and other parameters, and proxy user prompts to OpenAI.

provider: "openai"
auth: {"header": {"Authorization": "Bearer key"}}
options: {"model": "gpt-4"}`,
  // ai-rate-limiting
  'ai-rate-limiting': `Purpose：Configure a limit of 20 requests per second. If the limit is exceeded, a 503 status code and an error response will be returned.

limit: 20
time_window: 1
show_limit_quota_header: true
limit_strategy: total_tokens
rejected_code: 503
rejected_msg: "test..."`,
  // redirect
  'redirect': `uri: /test/default.html,
ret_code: 301`,
  // bk-mock
  'bk-mock': `Purpose: Return json response with status code 200 and response header foo:bar
Response status code: 200
Response body: {"hello": "world"}
Response header:
      Content-Type: application/json
      foo: bar`,
  // response-rewrite
  'response-rewrite': `"status_code": 200,
"body": {"code":"ok","message":"new json body"},
"headers": {
  "add": ["X-Server-balancer-addr: test"],
  "set": {"X-Server-id": 3},
  "remove": ["X-TO-BE-REMOVED"]
},
"vars": [[["arg_name", "==", "jack"], ["arg_age", "==", 18]]]`,
  // fault-injection
  'fault-injection': `Purpose: When the request parameter name is equal to jack and age is 18, return 400 reject status code and response body

"abort": {
    "http_status": 400,
    "body": "not valid request params",
    "vars": [[["arg_name", "==", "jack"], ["arg_age", "==", 18]]]
}`,
  // request-validation
  'request-validation': `Purpose: When the boolean_payload argument is not filled, 400 reject status code and reject information are returned

"body_schema": {
  "type": "object",
  "required": ["bool_payload"],
  "properties": {
    "bool_payload": {
      "type": "boolean"
    }
  }
}
"header_schema": {}
"rejected_code": 400
"rejected_msg": "not valid request body"`,
  // api-breaker
  'api-breaker': `Purpose: When the backend service returns a status code of 500 or 503 and this happens 3 times, a circuit breaker is triggered. It will return a response body with "hello world", a status code of 502, and a response header of foo:bar.
The first time the unhealthy state is triggered, the circuit breaker lasts for 2 seconds. After the circuit breaker time elapses, requests will be forwarded to the upstream service again. If it continues to return a status code of 502 and the count reaches 3 times again, the circuit breaker time is extended to 4 seconds. This pattern continues (2, 4, 8, 16, …) until the preset maximum circuit breaker time of 300 seconds is reached.
When the upstream service is in an unhealthy state, if a forwarded request returns a status code of 200 and this happens 2 times, the upstream service is considered to have recovered to a healthy state.

break_response_code: 502
break_response_body: helloworld
break_response_headers: [ { "key": "foo", "value": "bar" } ]
max_breaker_sec: 300
unhealthy: { "http_statuses": [ 500, 503 ], "failures": 3 }
healthy: { "http_statuses": [ 200 ], "successes": 2 }`,
  // bk-cors
  'bk-cors': `Purpose: allows https://a.example.com:8081, https://b.example.com:8081 this two site launch cross-domain request

allow_origins:
allow_origins_by_regex: ^https://.*\\.example\\.com:8081$
allow_methods: GET,POST,PUT,PATCH,HEAD,DELETE,OPTIONS
allow_headers: **
expose_headers:
max_age: 86400
allow_credential: false`,
  // bk-ip-restriction
  'bk-ip-restriction': `Purpose: Only IP 192.168.1.1 and 192.168.1.2 are allowed to request the current interface

Type: whitelist
Whitelist:
       # comment
       192.168.1.1
       192.168.1.2`,
  // bk-header-rewrite
  'bk-header-rewrite': `Purpose: Set header 'X-Api-Version: 1' and delete header 'X-test'

Settings: X-Api-Version: 1
Delete: X-test`,
  // bk-rate-limit
  'bk-rate-limit': `Purpose: By default, each application is performed 100 times/second, and demo is performed 200 times/second

Default frequency limit:
Times: 100
Time range: seconds

Special application frequency limit:
Times: 200
Time range: seconds

Blueking application ID: demo`,
  // bk-traffic-label
  'bk-traffic-label': `# single match
     "bk-traffic-label": {
       "rules": [
         {
           "match": [
             ["uri", "==", "/headers"]
           ],
           "actions": [
             {
               "set_headers": {
                 "X-Server-Id": 100
               }
             }
           ]
         }
       ]
     }

# single match with multiple conditions
     "bk-traffic-label": {
       "rules": [
         {
           "match": [
             "OR",
             ["arg_version", "==", "v1"],
             ["arg_env", "==", "dev"]
           ],
           "actions": [
             {
               "set_headers": {
                 "X-Server-Id": 100
               }
             }
           ]
         }
       ]
     }

# one match multiple actions with weight
# ❶ 30% of the requests should have the \`X-Server-Id: 100\` request header.
# ❷ 20% of the requests should have the \`X-API-Version: v2\` request header.
# ❸ 50% of the requests should not have any action performed on them.
     "bk-traffic-label": {
       "rules": [
         {
           "match": [
             ["uri", "==", "/headers"]
           ],
           "actions": [
             {
               "set_headers": {
                 "X-Server-Id": 100
               },
               "weight": 3
             },
             {
               "set_headers": {
                 "X-API-Version": "v2"
               },
               "weight": 2
             },
             {
               "weight": 5
             }
           ]
         }
       ]
     }

# multiple match  => execute in order
     "bk-traffic-label": {
       "rules": [
         {
           "match": [
             ["arg_version", "==", "v1"]
           ],
           "actions": [
             {
               "set_headers": {
                 "X-Server-Id": 100
               }
             }
           ]
         },
         {
           "match": [
             ["arg_version", "==", "v2"]
           ],
           "actions": [
             {
               "set_headers": {
                 "X-Server-Id": 200
               }
             }
           ]
         }
       ]
     }`,
  // uri-blocker
  'uri-blocker': `Purpose: When request URI matches block rule, return status code 403. Commonly used on admin/internal path and suspicious requests blocking.

block_rules:
^/admin(?:/.*)?$
^/internal(?:/.*)?$
.*\\.php(?:\\?.*)?$
case_insensitive: true
rejected_code: 403
rejected_msg: URI is blocked`,
  'bk-status-rewrite': '',
  'bk-legacy-invalid-params': '',
  'bk-username-required': '',
  'bk-oauth2-verify': '',
  'bk-oauth2-protected-resource': '',
  'bk-oauth2-audience-validate': '',
  // bk-query-string-rewrite
  'bk-query-string-rewrite': `Example:

Add version=v2
Set bk_app_code=demo
Remove debug

Suppose the original request is: GET /users?name=tom&debug=true&bk_app_code=test

After the plugin is applied, the request becomes: GET /users?name=tom&version=v2&bk_app_code=demo`,
};
