debug: false

server:
  host: 127.0.0.1
  port: 8000

  readTimeout: 60
  writeTimeout: 60
  idleTimeout: 180

sentry:
  dsn: ""
  ## zapcore.Level
  reportLogLevel: 2


databases:
  - id: "apigateway"
    host: "127.0.0.1"
    port: 3306
    user: "root"
    password: "blueking"
    name: "bk_apigateway"
    maxOpenConns: 200
    maxIdleConns: 50
    connMaxLifetimeSecond: 600
    # TLS配置（可选）
    tls:
      enabled: false
      # CA证书文件路径
      certCaFile: ""
      # 客户端证书文件路径
      certFile: ""
      # 客户端私钥文件路径
      certKeyFile: ""
      # 是否跳过主机名验证（仅用于测试，生产环境请设置为false）
      insecureSkipVerify: false

logger:
  default:
    level: debug
    writer: os
    buffered: false
    settings: {name: stdout}
  api:
    level: info
    writer: file
    buffered: true
    settings: {name: core_api.log, size: 100, backups: 10, age: 7, path: ./}
  audit:
    level: info
    writer: file
    buffered: true
    settings: {name: core_api.log, size: 100, backups: 10, age: 7, path: ./}



## config for metric/prometheus
metric:
  ## Metric name prefix, should be aligned with the dashboard's PROMETHEUS_METRIC_NAME_PREFIX.
  ## The PROMETHEUS_METRIC_NAME_PREFIX environment variable takes priority when set.
  namePrefix: "bk_apigateway_"

## config for mcp server
mcpServer:
  interval: 60
  ## The BK_API_URL_TMPL environment variable takes priority when set.
  bkApiUrlTmpl: ""
  # messageUrlFormat / messageApplicationUrlFormat：蓝鲸网关资源路径模板；第一个 % 之前的段用于推导 SSE 对外前缀（网关剥前缀时与官方 SDK 的 endpoint 一致）
  # messageUrlFormat: "/api/bk-apigateway/prod/api/v2/mcp-servers/%s/sse/message"
  # messageApplicationUrlFormat: "/api/bk-apigateway/prod/api/v2/mcp-servers/%s/application/sse/message"
  # Maximum concurrent goroutines for prefetching server configs (default: 20)
  maxConcurrentPrefetch: 20
  # Shared HTTP transport config for upstream tool calls
  transport:
    # Skip TLS certificate verification (only for internal networks; set false for public networks)
    insecureSkipVerify: true
    maxIdleConns: 200
    maxIdleConnsPerHost: 20
    idleConnTimeoutSecond: 90
  # Log truncation limits (string length, not bytes)
  logTruncate:
    # Audit log body size limit for tool call requests and body params
    auditLogMaxBodySize: 4096
    # Audit log response size limit for tool call responses
    auditLogMaxResponseSize: 4096
    # Audit log response size limit for failed tool call responses (keeps more diagnostic info)
    auditLogMaxErrorResponseSize: 16384
    # MCP API log request params size limit
    apiLogRequestSize: 2048
    # MCP API log response size limit (normal responses)
    apiLogResponseSize: 1024
    # MCP API log response size limit (error responses, keeps more diagnostic info)
    apiLogErrorResponseSize: 4096

## config for trace
tracing:
  enable: true
  endpoint: "127.0.0.1:4318"
  ## report type: grpc/http
  type: "http"
  ## support: "always_on"/"always_off"/"trace_id_ratio"/"parentbased_always_on",if not config,default: "trace_id_ratio"
  sampler: "trace_id_ratio"
  samplerRatio: 0.001
  token: "blueking"
  serviceName: "apigateway-mcp-proxy"
  instrument:
    ginAPI: true
    dbAPI: true
    mcpAPI: true

## config for bk ai dev trace (independent from tracing)
bkAIDevTrace:
  enable: false  # 环境变量 BKAI_DEV_TRACE_ENABLE 优先，设置后将覆盖此配置值
  endpoint: ""  # 例如: "127.0.0.1:4318"；环境变量 BKAI_DEV_TRACE_ENDPOINT 优先
  serviceName: "apigateway-mcp-proxy"  # 环境变量 BKAI_DEV_TRACE_SERVICE_NAME 优先
  token: ""  # 环境变量 BKAI_DEV_TRACE_TOKEN 优先

## config for pprof
pprof:
  username: ""  # 环境变量 PPROF_USERNAME 优先；为空时禁用 pprof
  password: ""  # 环境变量 PPROF_PASSWORD 优先；为空时禁用 pprof
