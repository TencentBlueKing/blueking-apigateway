debug: false

server:
  host: 127.0.0.1
  port: 8000

  readTimeout: 60
  writeTimeout: 60
  idleTimeout: 180

dashboard:
  # should configured same as the apisix:conf/config.yaml bk_gateway.instance.{id, secret}
  id: "faf44a48-59e9-f790-2412-e56c90551fb3"
  secret: "358627d8-d3e8-4522-8f16-b5530776bbb8"

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
  serviceName: "apigateway-core-api"
  instrument:
    ginAPI: true
    dbAPI: true
