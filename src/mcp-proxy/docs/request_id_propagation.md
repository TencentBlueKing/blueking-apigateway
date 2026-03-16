# Request ID 传递关系说明

## 全链路请求流

```
User -> bk-apigateway -> mcp-proxy -> biz-gateway -> biz-backend
```

## 两个 Request ID 的区别

### X-Request-Id（全链路 ID）

- **语义**: 全链路唯一标识，从第一个网关开始生成，贯穿所有服务
- **传递方式**: 经过每一层网关/服务时原样透传，不会被重置
- **用途**: 用于跨服务关联日志和追踪，是排查全链路问题的核心标识

### X-Bkapi-Request-ID（分段 ID）

- **语义**: 每段网关独立生成的请求 ID
- **传递方式**: 每经过一个 bk-apigateway 实例，该网关会生成新的 `X-Bkapi-Request-ID`
- **用途**: 用于定位某一段网关自身的日志

## mcp-proxy 中的处理

### 入站提取

RequestID 中间件从入站请求中提取两个 ID：

| Header | Context Key | 日志字段 |
|---|---|---|
| `X-Request-Id` | `constant.XRequestID` | `x_request_id` |
| `X-Bkapi-Request-ID` | `util.RequestIDKey` | `request_id` |

### 出站传递

当 mcp-proxy 调用下游 biz-gateway 时：

| Header | 传递行为 |
|---|---|
| `X-Request-Id` | 透传入站值（保持全链路一致） |
| `X-Bkapi-Request-ID` | 透传入站值（供下游网关日志参考，下游网关会生成自己的新段 ID） |

### 传递示例

```
bk-apigateway
├── 生成 X-Request-Id: abc-123（全链路 ID）
├── 生成 X-Bkapi-Request-ID: seg-001（本段 ID）
└── 发送到 mcp-proxy

mcp-proxy
├── 提取 x_request_id=abc-123, request_id=seg-001
├── 日志中输出两个 ID
└── 调用下游时透传 X-Request-Id: abc-123

biz-gateway
├── 收到 X-Request-Id: abc-123（继续透传）
├── 生成新的 X-Bkapi-Request-ID: seg-002（本段 ID）
└── 发送到 biz-backend

biz-backend
├── 收到 X-Request-Id: abc-123
└── 收到 X-Bkapi-Request-ID: seg-002
```

## 日志排查指引

- **跨服务追踪**: 使用 `x_request_id` 在所有服务日志中搜索同一个全链路 ID
- **定位 mcp-proxy 段**: 使用 `request_id`（即 `X-Bkapi-Request-ID`）在 mcp-proxy 日志中过滤
- **定位下游段**: 在下游 biz-gateway 日志中使用其生成的 `X-Bkapi-Request-ID`
