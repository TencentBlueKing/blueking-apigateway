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
    timeout: 2
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
  database:
    level: info
    writer: os
    buffered: false
    settings: {name: stdout}



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

## config for pprof
pprof:
  username: "bk-apigateway"  # 可通过环境变量 PPROF_USERNAME 覆盖
  password: "xxxxx"  # 可通过环境变量 PPROF_PASSWORD 覆盖，生产环境请使用强密码

## config for mcp server
mcpServer:
  # Maximum concurrent goroutines for prefetching server configs (default: 20)
  maxConcurrentPrefetch: 20
  # Shared HTTP transport config for upstream tool calls
  transport:
    # Skip TLS certificate verification (only for internal networks; set false for public networks)
    insecureSkipVerify: true
    maxIdleConns: 200
    maxIdleConnsPerHost: 20
    idleConnTimeoutSecond: 90
  # Log truncation limits (bytes)
  logTruncate:
    # Audit log body size limit for tool call requests and body params
    maxBodySize: 4096
    # Audit log response size limit for tool call responses
    maxResponseSize: 4096
    # MCP API log request params size limit
    apiLogRequestSize: 2048
    # MCP API log response size limit (normal responses)
    apiLogResponseSize: 1024
    # MCP API log response size limit (error responses, keeps more diagnostic info)
    apiLogErrorResponseSize: 4096